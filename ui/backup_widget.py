"""
GerLauNR10 - Aba de exportacao e importacao de dados (backup e transferencia)
"""
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox, QGroupBox,
    QTextEdit, QProgressBar, QFormLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

import database as db
import backup
from styles import COLORS


def _mb(n: int) -> str:
    return "%.1f MB" % (n / 1e6)


def _ajustar_botoes(caixa: QMessageBox):
    """Garante que o rotulo caiba dentro do botao.

    O QDialogButtonBox uniformiza a largura dos botoes pelo sizeHint deles, que
    nao leva em conta o "padding: 8px 18px" do stylesheet global. Com rotulos
    longos ("Substituir o existente") o texto acabava cortado nas duas pontas.
    Aqui a largura minima e calculada a partir do texto renderizado.
    """
    for botao in caixa.buttons():
        largura = botao.fontMetrics().horizontalAdvance(botao.text())
        # 18px de padding em cada lado, mais folga para variacoes de fonte e
        # de escalonamento de tela (125%/150%), onde a sobra some rapido.
        botao.setMinimumWidth(largura + 56)


class _Tarefa(QThread):
    """Roda exportacao/importacao fora da thread da interface.

    Pacotes com fotos chegam facilmente a dezenas de MB; feito na thread da
    interface, a janela congelaria durante a operacao.
    """
    concluido = pyqtSignal(object)
    falhou = pyqtSignal(str)

    def __init__(self, funcao, *args):
        super().__init__()
        self._funcao, self._args = funcao, args

    def run(self):
        try:
            self.concluido.emit(self._funcao(*self._args))
        except Exception as e:            # noqa: BLE001 - reportado na interface
            self.falhou.emit(str(e))


class BackupWidget(QWidget):
    """Exporta e importa pacotes .gnr10 (cliente completo ou painel avulso)."""

    dados_alterados = pyqtSignal()   # avisa a janela para recarregar as telas

    def __init__(self, parent=None):
        super().__init__(parent)
        self._arquivo_import = None
        self._manifest = None
        self._tarefa = None
        self._build_ui()
        self.recarregar()

    # ── Construcao ────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        topo = QHBoxLayout()
        topo.addWidget(self._grupo_exportar(), 1)
        topo.addWidget(self._grupo_importar(), 1)
        layout.addLayout(topo, 3)

        self.progresso = QProgressBar()
        self.progresso.setRange(0, 0)          # indeterminado
        self.progresso.setVisible(False)
        self.progresso.setFixedHeight(6)
        self.progresso.setTextVisible(False)
        layout.addWidget(self.progresso)

        layout.addWidget(QLabel("Registro de operações:"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet(
            "background: #1a2332; color: #d0d7de; font-family: Consolas, monospace;"
            "font-size: 11px; border-radius: 6px;"
        )
        layout.addWidget(self.log, 2)

    def _grupo_exportar(self) -> QGroupBox:
        cx = QGroupBox("Exportar")
        v = QVBoxLayout(cx)
        v.setSpacing(8)

        ajuda = QLabel(
            "Gera um arquivo .gnr10 com os dados e as fotos. Pode ser gravado "
            "em qualquer pasta do computador ou da rede."
        )
        ajuda.setWordWrap(True)
        ajuda.setStyleSheet("color: #586069; font-size: 11px;")
        v.addWidget(ajuda)

        self.rb_cliente = QRadioButton("Cliente completo (laudos, painéis, avaliações e fotos)")
        self.rb_painel = QRadioButton("Painel individual")
        self.rb_cliente.setChecked(True)
        self._grupo_escopo = QButtonGroup(self)
        self._grupo_escopo.addButton(self.rb_cliente, 0)
        self._grupo_escopo.addButton(self.rb_painel, 1)
        self._grupo_escopo.idToggled.connect(lambda _i, _c: self._atualizar_escopo())
        v.addWidget(self.rb_cliente)
        v.addWidget(self.rb_painel)

        form = QFormLayout()
        form.setSpacing(6)
        self.cb_cliente = QComboBox()
        self.cb_cliente.currentIndexChanged.connect(self._carregar_laudos)
        self.cb_laudo = QComboBox()
        self.cb_laudo.currentIndexChanged.connect(self._carregar_paineis)
        self.cb_painel = QComboBox()
        form.addRow("Cliente:", self.cb_cliente)
        self.lbl_laudo = QLabel("Laudo:")
        self.lbl_painel = QLabel("Painel:")
        form.addRow(self.lbl_laudo, self.cb_laudo)
        form.addRow(self.lbl_painel, self.cb_painel)
        v.addLayout(form)

        v.addStretch()
        self.btn_exportar = QPushButton("Escolher destino e exportar...")
        self.btn_exportar.setObjectName("btn_accent")
        self.btn_exportar.clicked.connect(self._exportar)
        v.addWidget(self.btn_exportar)
        return cx

    def _grupo_importar(self) -> QGroupBox:
        cx = QGroupBox("Importar")
        v = QVBoxLayout(cx)
        v.setSpacing(8)

        ajuda = QLabel(
            "Lê um arquivo .gnr10. A importação apenas acrescenta dados — "
            "nada existente é apagado ou sobrescrito."
        )
        ajuda.setWordWrap(True)
        ajuda.setStyleSheet("color: #586069; font-size: 11px;")
        v.addWidget(ajuda)

        self.btn_escolher = QPushButton("Selecionar arquivo...")
        self.btn_escolher.setObjectName("btn_secondary")
        self.btn_escolher.clicked.connect(self._escolher_arquivo)
        v.addWidget(self.btn_escolher)

        self.lbl_pacote = QLabel("Nenhum arquivo selecionado.")
        self.lbl_pacote.setWordWrap(True)
        self.lbl_pacote.setStyleSheet(
            "color: #586069; font-size: 11px; border: 1px dashed #c8d0d8;"
            "border-radius: 4px; padding: 8px;"
        )
        v.addWidget(self.lbl_pacote)

        # Destino: so faz sentido depois de ler o manifest
        self.cx_destino = QGroupBox("Destino")
        dv = QVBoxLayout(self.cx_destino)
        dv.setSpacing(6)
        self.rb_novo = QRadioButton("Criar um novo cliente")
        self.rb_existente = QRadioButton("Acrescentar a um cliente já cadastrado")
        self.rb_novo.setChecked(True)
        self.rb_novo.toggled.connect(self._atualizar_destino)
        dv.addWidget(self.rb_novo)
        dv.addWidget(self.rb_existente)

        dform = QFormLayout()
        dform.setSpacing(6)
        self.cb_cliente_dest = QComboBox()
        self.cb_cliente_dest.currentIndexChanged.connect(self._carregar_laudos_destino)
        self.cb_laudo_dest = QComboBox()
        dform.addRow("Cliente:", self.cb_cliente_dest)
        self.lbl_laudo_dest = QLabel("Laudo:")
        dform.addRow(self.lbl_laudo_dest, self.cb_laudo_dest)
        dv.addLayout(dform)
        self.cx_destino.setVisible(False)
        v.addWidget(self.cx_destino)

        v.addStretch()
        self.btn_importar = QPushButton("Importar")
        self.btn_importar.setObjectName("btn_success")
        self.btn_importar.setEnabled(False)
        self.btn_importar.clicked.connect(self._importar)
        v.addWidget(self.btn_importar)
        return cx

    # ── Carga dos combos ──────────────────────────────────────────────────
    def recarregar(self):
        """Recarrega as listas de clientes. Chamado ao abrir a aba."""
        for combo in (self.cb_cliente, self.cb_cliente_dest):
            atual = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for c in db.listar_clientes():
                combo.addItem(c["razao_social"], c["id"])
            indice = combo.findData(atual)
            if indice >= 0:
                combo.setCurrentIndex(indice)
            combo.blockSignals(False)
        self._carregar_laudos()
        self._carregar_laudos_destino()
        self._atualizar_escopo()

    def _carregar_laudos(self):
        self.cb_laudo.blockSignals(True)
        self.cb_laudo.clear()
        cid = self.cb_cliente.currentData()
        if cid:
            for l in db.listar_laudos(cid):
                self.cb_laudo.addItem(l.get("numero") or l.get("titulo") or "Laudo", l["id"])
        self.cb_laudo.blockSignals(False)
        self._carregar_paineis()

    def _carregar_paineis(self):
        self.cb_painel.clear()
        lid = self.cb_laudo.currentData()
        if lid:
            for p in db.listar_paineis(lid):
                rotulo = "%s  (%s)" % (p.get("tag") or "sem TAG", p.get("setor") or "—")
                self.cb_painel.addItem(rotulo, p["id"])

    def _carregar_laudos_destino(self):
        self.cb_laudo_dest.clear()
        cid = self.cb_cliente_dest.currentData()
        if cid:
            for l in db.listar_laudos(cid):
                self.cb_laudo_dest.addItem(l.get("numero") or l.get("titulo") or "Laudo", l["id"])

    def _atualizar_escopo(self):
        por_painel = self.rb_painel.isChecked()
        for w in (self.lbl_laudo, self.cb_laudo, self.lbl_painel, self.cb_painel):
            w.setVisible(por_painel)

    def _atualizar_destino(self):
        if not self._manifest:
            return
        tipo = self._manifest.get("tipo")
        if tipo == "painel":
            # Um painel precisa obrigatoriamente de um laudo existente
            self.cb_cliente_dest.setVisible(True)
            self.lbl_laudo_dest.setVisible(True)
            self.cb_laudo_dest.setVisible(True)
        else:
            usa_existente = self.rb_existente.isChecked()
            self.cb_cliente_dest.setVisible(usa_existente)
            self.lbl_laudo_dest.setVisible(False)
            self.cb_laudo_dest.setVisible(False)

    # ── Log e estado ──────────────────────────────────────────────────────
    def _log(self, texto: str):
        self.log.append("[%s]  %s" % (datetime.now().strftime("%H:%M:%S"), texto))

    def _ocupado(self, ocupado: bool):
        self.progresso.setVisible(ocupado)
        self.btn_exportar.setEnabled(not ocupado)
        self.btn_escolher.setEnabled(not ocupado)
        self.btn_importar.setEnabled(not ocupado and self._arquivo_import is not None)

    # ── Exportacao ────────────────────────────────────────────────────────
    def _exportar(self):
        por_painel = self.rb_painel.isChecked()
        carimbo = datetime.now().strftime("%Y-%m-%d")

        if por_painel:
            painel_id = self.cb_painel.currentData()
            if not painel_id:
                QMessageBox.warning(self, "Exportar", "Selecione um painel.")
                return
            tag = self.cb_painel.currentText().split("  (")[0]
            sugerido = "Painel_%s_%s%s" % (tag, carimbo, backup.EXTENSAO)
        else:
            cliente_id = self.cb_cliente.currentData()
            if not cliente_id:
                QMessageBox.warning(self, "Exportar", "Selecione um cliente.")
                return
            sugerido = "Cliente_%s_%s%s" % (self.cb_cliente.currentText()[:40], carimbo,
                                            backup.EXTENSAO)

        sugerido = "".join(ch if ch.isalnum() or ch in " _-." else "_" for ch in sugerido)
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar pacote de dados", sugerido,
            "Pacote GerLauNR10 (*%s)" % backup.EXTENSAO)
        if not caminho:
            return
        if not caminho.lower().endswith(backup.EXTENSAO):
            caminho += backup.EXTENSAO

        self._ocupado(True)
        if por_painel:
            self._log("Exportando painel para %s ..." % caminho)
            self._tarefa = _Tarefa(backup.exportar_painel, self.cb_painel.currentData(), caminho)
        else:
            self._log("Exportando cliente para %s ..." % caminho)
            self._tarefa = _Tarefa(backup.exportar_cliente, self.cb_cliente.currentData(), caminho)
        self._tarefa.concluido.connect(self._exportacao_ok)
        self._tarefa.falhou.connect(self._operacao_falhou)
        self._tarefa.start()

    def _exportacao_ok(self, r: dict):
        self._ocupado(False)
        if "painel" in r:
            self._log("Painel '%s' exportado. %s avaliações, %s foto(s), %s."
                      % (r["painel"], r["avaliacoes"], r["fotos"], _mb(r["tamanho"])))
        else:
            self._log("Cliente '%s' exportado. %s laudo(s), %s painel(is), %s foto(s), %s."
                      % (r["cliente"], r["laudos"], r["paineis"], r["fotos"], _mb(r["tamanho"])))
        ausentes = r.get("fotos_ausentes") or []
        if ausentes:
            self._log("AVISO: %d foto(s) do banco não foram encontradas no disco e ficaram "
                      "de fora do pacote." % len(ausentes))
            for caminho in ausentes[:5]:
                self._log("   ausente: %s" % caminho)
            if len(ausentes) > 5:
                self._log("   ... e mais %d." % (len(ausentes) - 5))
        QMessageBox.information(self, "Exportação concluída",
                                "Pacote gravado em:\n%s\n\nTamanho: %s"
                                % (r["arquivo"], _mb(r["tamanho"])))

    # ── Importacao ────────────────────────────────────────────────────────
    def _escolher_arquivo(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar pacote de dados", "",
            "Pacote GerLauNR10 (*%s);;Todos os arquivos (*)" % backup.EXTENSAO)
        if not caminho:
            return
        try:
            manifest = backup.ler_manifest(caminho)
        except backup.BackupErro as e:
            self._arquivo_import = self._manifest = None
            self.cx_destino.setVisible(False)
            self.btn_importar.setEnabled(False)
            self.lbl_pacote.setText("Arquivo inválido.")
            QMessageBox.critical(self, "Arquivo inválido", str(e))
            return

        self._arquivo_import, self._manifest = caminho, manifest
        resumo = manifest.get("resumo", {})
        tipo = manifest.get("tipo")
        if tipo == "cliente":
            descricao = ("Cliente: <b>%s</b><br>%s laudo(s), %s painel(is)"
                         % (resumo.get("cliente", "—"), resumo.get("laudos", 0),
                            resumo.get("paineis", 0)))
            self.rb_novo.setVisible(True)
            self.rb_existente.setVisible(True)
        else:
            descricao = ("Painel: <b>%s</b><br>Origem: %s<br>%s avaliações"
                         % (resumo.get("painel", "—"), resumo.get("cliente", "—"),
                            resumo.get("avaliacoes", 0)))
            self.rb_novo.setVisible(False)
            self.rb_existente.setVisible(False)

        self.lbl_pacote.setText(
            "%s<br><span style='color:#8a9bb0'>%s &nbsp;|&nbsp; gerado em %s</span>"
            % (descricao, os.path.basename(caminho), manifest.get("gerado_em", "—")))
        self.cx_destino.setVisible(True)
        self._atualizar_destino()
        self.btn_importar.setEnabled(True)
        self._log("Pacote selecionado: %s (tipo: %s)" % (os.path.basename(caminho), tipo))

    def _perguntar(self, titulo: str, texto: str, rotulo_novo: str,
                   rotulo_substituir: str):
        """Caixa com tres saidas. Devolve 'novo', 'substituir' ou None."""
        cx = QMessageBox(self)
        cx.setWindowTitle(titulo)
        cx.setIcon(QMessageBox.Icon.Question)
        cx.setText(texto)
        bt_novo = cx.addButton(rotulo_novo, QMessageBox.ButtonRole.AcceptRole)
        bt_sub = cx.addButton(rotulo_substituir, QMessageBox.ButtonRole.DestructiveRole)
        cx.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        cx.setDefaultButton(bt_novo)
        _ajustar_botoes(cx)
        cx.exec()
        if cx.clickedButton() is bt_novo:
            return "novo"
        if cx.clickedButton() is bt_sub:
            return "substituir"
        return None

    def _resolver_conflito_painel(self, laudo_id: int, alvo: str):
        """Decide o modo de importacao de um painel. None = cancelar."""
        try:
            conf = backup.conflito_painel(self._arquivo_import, laudo_id)
        except backup.BackupErro as e:
            QMessageBox.critical(self, "Falha ao ler o pacote", str(e))
            return None

        tag = self._manifest.get("resumo", {}).get("painel", "—")
        if not conf:
            if QMessageBox.question(
                    self, "Confirmar importação",
                    "Importar o painel '%s' para:\n\n%s" % (tag, alvo)
            ) != QMessageBox.StandardButton.Yes:
                return None
            return "novo"

        partes = []
        if conf.get("tag_existente"):
            partes.append("Já existe um painel com a TAG '%s' neste laudo (Nº Form %s)."
                          % (conf.get("tag"), conf.get("formulario_existente")))
        else:
            partes.append("O Nº Form %s do pacote já está ocupado neste laudo."
                          % conf.get("formulario_origem"))
        partes.append("")
        partes.append("Destino: %s" % alvo)
        return self._perguntar(
            "Painel já existente", "\n".join(partes),
            "Criar novo (Nº Form %s)" % conf.get("formulario_sugerido"),
            "Substituir o existente")

    def _resolver_conflito_cliente(self, destino_id, alvo: str):
        """Decide o modo de importacao de um cliente. None = cancelar."""
        cliente = self._manifest.get("resumo", {}).get("cliente", "—")
        repetidos = []
        if destino_id:
            try:
                repetidos = backup.conflito_cliente(self._arquivo_import, destino_id)
            except backup.BackupErro as e:
                QMessageBox.critical(self, "Falha ao ler o pacote", str(e))
                return None

        if not repetidos:
            if QMessageBox.question(
                    self, "Confirmar importação",
                    "Importar os dados de '%s' para %s?" % (cliente, alvo)
            ) != QMessageBox.StandardButton.Yes:
                return None
            return "novo"

        lista = "\n".join("  • %s" % n for n in repetidos[:6])
        if len(repetidos) > 6:
            lista += "\n  ... e mais %d." % (len(repetidos) - 6)
        return self._perguntar(
            "Laudos já existentes",
            "Este cliente já tem laudo(s) com o mesmo número:\n\n%s\n\n"
            "Substituir apaga o laudo existente com todos os seus painéis "
            "e avaliações." % lista,
            "Criar novos (renumerando)", "Substituir os existentes")

    def _importar(self):
        if not self._arquivo_import or not self._manifest:
            return
        tipo = self._manifest.get("tipo")

        if tipo == "painel":
            laudo_id = self.cb_laudo_dest.currentData()
            if not laudo_id:
                QMessageBox.warning(
                    self, "Importar",
                    "Escolha o cliente e o laudo que vão receber este painel.\n\n"
                    "Se o cliente ainda não tem laudo, crie um na tela de Laudos.")
                return
            alvo = "%s / %s" % (self.cb_cliente_dest.currentText(),
                                self.cb_laudo_dest.currentText())

            modo = self._resolver_conflito_painel(laudo_id, alvo)
            if modo is None:
                return
            self._ocupado(True)
            self._log("Importando painel para %s (modo: %s) ..."
                      % (alvo, "substituir" if modo == "substituir" else "criar novo"))
            self._tarefa = _Tarefa(backup.importar_painel, self._arquivo_import,
                                   laudo_id, modo)
        else:
            destino_id = None
            if self.rb_existente.isChecked():
                destino_id = self.cb_cliente_dest.currentData()
                if not destino_id:
                    QMessageBox.warning(self, "Importar", "Selecione o cliente de destino.")
                    return
                alvo = "cliente já cadastrado: %s" % self.cb_cliente_dest.currentText()
            else:
                alvo = "um novo cliente"

            modo = self._resolver_conflito_cliente(destino_id, alvo)
            if modo is None:
                return
            self._ocupado(True)
            self._log("Importando cliente para %s (modo: %s) ..."
                      % (alvo, "substituir" if modo == "substituir" else "criar novo"))
            self._tarefa = _Tarefa(backup.importar_cliente, self._arquivo_import,
                                   destino_id, modo)

        self._tarefa.concluido.connect(self._importacao_ok)
        self._tarefa.falhou.connect(self._operacao_falhou)
        self._tarefa.start()

    def _importacao_ok(self, r: dict):
        self._ocupado(False)
        self._log("Importação concluída: %d cliente(s), %d laudo(s), %d painel(is)."
                  % (r["clientes"], r["laudos"], r["paineis"]))

        for tag, de, para in r.get("renumerados") or []:
            self._log("   painel '%s': Nº Form %s já ocupado, gravado como %s."
                      % (tag, de, para))
        for tag in r.get("substituidos") or []:
            self._log("   painel '%s' substituiu o existente de mesma TAG." % tag)
        for antigo, novo in r.get("laudos_renomeados") or []:
            self._log("   laudo '%s' já existia; gravado como '%s'." % (antigo, novo))
        for numero in r.get("laudos_substituidos") or []:
            self._log("   laudo '%s' foi substituído (o anterior foi removido)." % numero)

        faltantes = r.get("opcoes_nao_encontradas") or []
        if faltantes:
            self._log("AVISO: %d resposta(s) do checklist não existem no checklist local. "
                      "O peso e os textos foram preservados, mas a opção ficou sem vínculo:"
                      % len(faltantes))
            for f in faltantes[:5]:
                self._log("   %s" % f)
            if len(faltantes) > 5:
                self._log("   ... e mais %d." % (len(faltantes) - 5))
        self.recarregar()
        self.dados_alterados.emit()
        QMessageBox.information(
            self, "Importação concluída",
            "%d cliente(s), %d laudo(s) e %d painel(is) importados."
            % (r["clientes"], r["laudos"], r["paineis"]))

    def _operacao_falhou(self, erro: str):
        self._ocupado(False)
        self._log("ERRO: %s" % erro)
        QMessageBox.critical(self, "Falha na operação", erro)
