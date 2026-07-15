"""
GerLauNR10 - Widget de geração de relatório PDF
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFileDialog, QMessageBox,
    QFrame, QScrollArea, QGroupBox, QFormLayout, QLineEdit,
    QCheckBox, QSplitter, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap

import database as db
from styles import COLORS, nivel_cor, nivel_label


# ---------------------------------------------------------------------------
# Thread de geração de PDF
# ---------------------------------------------------------------------------
class PDFThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, laudo_id: int, output_path: str, opcoes: dict):
        super().__init__()
        self.laudo_id = laudo_id
        self.output_path = output_path
        self.opcoes = opcoes

    def run(self):
        try:
            from pdf_generator import gerar_laudo_pdf
            gerar_laudo_pdf(
                self.laudo_id,
                self.output_path,
                self.opcoes,
                progress_cb=lambda p, msg: self.progress.emit(p, msg)
            )
            self.finished.emit(self.output_path)
        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n\n{traceback.format_exc()}")


# ---------------------------------------------------------------------------
# Widget principal
# ---------------------------------------------------------------------------
class PDFWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._laudo_id = None
        self._output_path = ""
        self._todos_laudos = []   # cache de todos os laudos
        self._build_ui()

    def set_laudo(self, laudo_id: int):
        self._laudo_id = laudo_id
        self._refresh_selector()
        self._load_info()

    def showEvent(self, event):
        """Atualiza o seletor toda vez que a tela é exibida."""
        super().showEvent(event)
        self._refresh_selector()

    def _refresh_selector(self):
        """Recarrega o combo com todos os laudos de todos os clientes."""
        self.combo_laudo.blockSignals(True)
        self.combo_laudo.clear()
        self.combo_laudo.addItem("— Selecione um laudo —", None)
        self._todos_laudos = []
        clientes = db.listar_clientes()
        for c in clientes:
            laudos = db.listar_laudos(c["id"])
            for l in laudos:
                label = f"{c['razao_social']}  |  {l.get('numero','—')}  –  {l.get('titulo','—')}"
                self.combo_laudo.addItem(label, l["id"])
                self._todos_laudos.append(l["id"])
        # Seleciona o laudo atual se existir
        if self._laudo_id:
            for i in range(self.combo_laudo.count()):
                if self.combo_laudo.itemData(i) == self._laudo_id:
                    self.combo_laudo.setCurrentIndex(i)
                    break
        self.combo_laudo.blockSignals(False)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("📄  Gerar Relatório PDF – Laudo NR-10")
        header.setObjectName("page_title")
        layout.addWidget(header)

        # ── Seletor de laudo ──────────────────────────────────────────────────
        sel_frame = QFrame()
        sel_frame.setStyleSheet(
            "background:#ffffff; border:1px solid #e8820c;"
            "border-left:4px solid #e8820c; border-radius:6px;"
        )
        sel_layout = QHBoxLayout(sel_frame)
        sel_layout.setContentsMargins(12, 8, 12, 8)
        sel_layout.setSpacing(8)

        # Logo do cliente (atualizado quando laudo é selecionado)
        self.lbl_logo_cli = QLabel()
        self.lbl_logo_cli.setFixedSize(64, 40)
        self.lbl_logo_cli.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo_cli.setText("LOGO")
        self.lbl_logo_cli.setStyleSheet(
            "color:#586069; font-size:9px; font-weight:bold;"
            "border:1px dashed #c8d0d8; border-radius:4px; background:#f0f4f8;"
        )
        sel_layout.addWidget(self.lbl_logo_cli)

        sel_lbl = QLabel("Laudo:")
        sel_lbl.setStyleSheet("font-weight:bold; color:#1a1a1a; min-width:52px;")
        self.combo_laudo = QComboBox()
        self.combo_laudo.setMinimumHeight(34)
        self.combo_laudo.addItem("— Selecione um laudo —", None)
        self.combo_laudo.currentIndexChanged.connect(self._on_combo_changed)

        btn_refresh = QPushButton("⟳")
        btn_refresh.setObjectName("btn_secondary")
        btn_refresh.setFixedSize(34, 34)
        btn_refresh.setStyleSheet(
            "font-size:18px; font-weight:bold; padding:0; border-radius:4px;"
        )
        btn_refresh.setToolTip("Atualizar lista de laudos")
        btn_refresh.clicked.connect(self._refresh_selector)

        sel_layout.addWidget(sel_lbl)
        sel_layout.addWidget(self.combo_laudo, 1)
        sel_layout.addWidget(btn_refresh)
        layout.addWidget(sel_frame)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---- Esquerdo: info do laudo ----
        left = QScrollArea()
        left.setWidgetResizable(True)
        left.setMaximumWidth(420)
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(12)

        # Resumo do laudo
        self.grp_laudo = QGroupBox("Laudo Selecionado")
        grp_l = QVBoxLayout(self.grp_laudo)
        self.lbl_laudo_info = QLabel("Nenhum laudo selecionado")
        self.lbl_laudo_info.setWordWrap(True)
        self.lbl_laudo_info.setStyleSheet("font-size: 12px; color: #586069;")
        grp_l.addWidget(self.lbl_laudo_info)
        left_layout.addWidget(self.grp_laudo)

        # Resumo de painéis
        self.grp_paineis = QGroupBox("Painéis / Avaliações")
        grp_p = QVBoxLayout(self.grp_paineis)
        self.lbl_paineis_info = QLabel("—")
        self.lbl_paineis_info.setWordWrap(True)
        self.lbl_paineis_info.setStyleSheet("font-size: 12px;")
        grp_p.addWidget(self.lbl_paineis_info)
        left_layout.addWidget(self.grp_paineis)

        # Opções de geração
        grp_opt = QGroupBox("Seções do Relatório")
        opt_layout = QVBoxLayout(grp_opt)
        self.chk_capa = QCheckBox("Capa de apresentação")
        self.chk_identificacao = QCheckBox("Identificação (cliente + profissionais)")
        self.chk_art = QCheckBox("ART – Anotação de Responsabilidade Técnica")
        self.chk_nr10 = QCheckBox("Resumo Técnico da NR-10")
        self.chk_metodologia = QCheckBox("Metodologia de avaliação Engelogic")
        self.chk_avaliacoes = QCheckBox("Avaliações individuais dos painéis")
        self.chk_graficos = QCheckBox("Estratificação dos dados (gráficos)")
        self.chk_conclusoes = QCheckBox("Conclusões e Recomendações")
        self.chk_consideracoes = QCheckBox("Considerações Finais")
        self.chk_fotos = QCheckBox("Incluir evidências fotográficas")

        for chk in [self.chk_capa, self.chk_identificacao, self.chk_art, self.chk_nr10,
                    self.chk_metodologia, self.chk_avaliacoes, self.chk_graficos,
                    self.chk_conclusoes, self.chk_consideracoes, self.chk_fotos]:
            chk.setChecked(True)
            opt_layout.addWidget(chk)
        left_layout.addWidget(grp_opt)

        # Conclusões editáveis
        grp_conc = QGroupBox("Conclusões e Recomendações (editável)")
        conc_l = QVBoxLayout(grp_conc)
        self.conclusoes_edit = QTextEdit()
        self.conclusoes_edit.setPlaceholderText(
            "Descreva as conclusões e recomendações técnicas do laudo...\n\n"
            "Será inserido na seção de Conclusões do relatório PDF."
        )
        self.conclusoes_edit.setMinimumHeight(100)
        conc_l.addWidget(self.conclusoes_edit)
        left_layout.addWidget(grp_conc)

        left_layout.addStretch()
        left.setWidget(left_container)
        splitter.addWidget(left)

        # ---- Direito: log e controles ----
        right = QFrame()
        right.setObjectName("card")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        r_title = QLabel("Geração do Relatório")
        r_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['primary']};")
        right_layout.addWidget(r_title)

        # Destino
        dest_row = QHBoxLayout()
        self.lbl_dest = QLabel("Nenhum destino selecionado")
        self.lbl_dest.setStyleSheet("color: #8a9bb0; font-size: 11px;")
        btn_dest = QPushButton("📁 Escolher Destino")
        btn_dest.setObjectName("btn_secondary")
        btn_dest.clicked.connect(self._choose_dest)
        dest_row.addWidget(self.lbl_dest)
        dest_row.addWidget(btn_dest)
        right_layout.addLayout(dest_row)

        # Progress
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setValue(0)
        self.progress.setFormat("Aguardando...")
        right_layout.addWidget(self.progress)

        # Log
        log_lbl = QLabel("Log de geração:")
        log_lbl.setStyleSheet("color: #586069; font-size: 11px;")
        right_layout.addWidget(log_lbl)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFont(QFont("Courier New", 10))
        self.log_edit.setStyleSheet(
            "background: #1a2332; color: #a0c0e0; border-radius: 6px; padding: 8px;"
        )
        right_layout.addWidget(self.log_edit)

        # Botão gerar
        self.btn_gerar = QPushButton("🚀  Gerar Relatório PDF")
        self.btn_gerar.setObjectName("btn_accent")
        self.btn_gerar.setMinimumHeight(48)
        self.btn_gerar.setStyleSheet(
            f"font-size: 15px; font-weight: bold;"
        )
        self.btn_gerar.clicked.connect(self._generate)
        self.btn_gerar.setEnabled(False)
        right_layout.addWidget(self.btn_gerar)

        self.btn_open = QPushButton("📂  Abrir PDF Gerado")
        self.btn_open.setObjectName("btn_success")
        self.btn_open.clicked.connect(self._open_pdf)
        self.btn_open.setEnabled(False)
        right_layout.addWidget(self.btn_open)

        splitter.addWidget(right)
        splitter.setSizes([380, 600])
        layout.addWidget(splitter)

    def _on_combo_changed(self, index: int):
        laudo_id = self.combo_laudo.itemData(index)
        if laudo_id is not None:
            self._laudo_id = laudo_id
            self._load_info()
        else:
            self._laudo_id = None
            self.lbl_laudo_info.setText("Nenhum laudo selecionado")
            self.lbl_paineis_info.setText("—")
            self.btn_gerar.setEnabled(False)

    def _load_info(self):
        if not self._laudo_id:
            return
        laudo = db.buscar_laudo(self._laudo_id)
        if not laudo:
            return

        # Logo do cliente
        cliente = db.buscar_cliente(laudo["cliente_id"]) if laudo.get("cliente_id") else {}
        logo_path = cliente.get("logo_path", "") if cliente else ""
        if logo_path and os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(
                60, 36, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_logo_cli.setPixmap(pix)
            self.lbl_logo_cli.setStyleSheet(
                "border:1px solid #e8820c; border-radius:4px; background:#fff;"
            )
            self.lbl_logo_cli.setText("")
        else:
            self.lbl_logo_cli.setPixmap(QPixmap())
            razao = (cliente.get("razao_social") or "LOGO")[:8]
            self.lbl_logo_cli.setText(razao)
            self.lbl_logo_cli.setStyleSheet(
                "color:#888; font-size:8px; font-weight:bold;"
                "border:1px dashed #ccc; border-radius:4px; background:#f8f8f8;"
            )

        # Info do laudo
        self.lbl_laudo_info.setText(
            f"<b>{laudo.get('titulo', '—')}</b><br>"
            f"Nº: {laudo.get('numero', '—')}<br>"
            f"Período: {laudo.get('periodo_inicio', '—')} a {laudo.get('periodo_fim', '—')}<br>"
            f"Status: {laudo.get('status', '—')}"
        )

        # Painéis
        paineis = db.listar_paineis(self._laudo_id)
        if paineis:
            media = sum(p.get("nivel_aderencia", 0) for p in paineis) / len(paineis)
            info_txt = f"<b>{len(paineis)}</b> painel(is) avaliado(s)<br>"
            info_txt += f"Nível Médio de Aderência: <b>{media*100:.1f}%</b> ({nivel_label(media)})<br><br>"
            for p in paineis:
                n = p.get("nivel_aderencia", 0)
                info_txt += f"• {p.get('tag', '—')}  →  {n*100:.1f}%<br>"
            self.lbl_paineis_info.setText(info_txt)
        else:
            self.lbl_paineis_info.setText("Nenhum painel avaliado neste laudo.")

        # Conclusões
        conclusoes = laudo.get("conclusoes") or ""
        if not conclusoes:
            conclusoes = self._default_conclusoes()
        self.conclusoes_edit.setPlainText(conclusoes)

        self.btn_gerar.setEnabled(bool(paineis))
        self._log(" Laudo carregado. Selecione o destino e clique em 'Gerar'.")

    def _default_conclusoes(self) -> str:
        return (
            "Devido à grande quantidade de elementos avaliados durante a vistoria, torna-se inviável "
            "elencar todas as conclusões individualmente. Para maiores informações sobre a situação de "
            "cada um dos elementos avaliados, recomenda-se primeiramente uma análise cuidadosa dos "
            "formulários de avaliação gerados.\n\n"
            "Recomenda-se manutenção preventiva periódica, haja vista que as instalações elétricas "
            "estão expostas a severas condições de operação. Os resultados e conclusões apresentados "
            "neste relatório técnico representam as condições do estado atual dos diversos tipos de "
            "painéis elétricos avaliados.\n\n"
            "O prazo para execução das adequações deve ser definido de acordo com o plano de ação "
            "do cliente, priorizando os itens classificados como Não Conforme."
        )

    def _choose_dest(self):
        laudo = db.buscar_laudo(self._laudo_id) if self._laudo_id else {}
        default_name = f"Laudo_NR10_{laudo.get('numero', 'sem_numero')}.pdf".replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório PDF", default_name, "PDF (*.pdf)"
        )
        if path:
            self._output_path = path
            self.lbl_dest.setText(path)
            self.lbl_dest.setStyleSheet("color: #1a7f37; font-size: 11px;")

    def _generate(self):
        if not self._laudo_id:
            QMessageBox.warning(self, "Aviso", "Selecione um laudo.")
            return
        if not self._output_path:
            self._choose_dest()
            if not self._output_path:
                return

        # Salva conclusões no banco
        import database as db
        laudo = db.buscar_laudo(self._laudo_id)
        if laudo:
            laudo["conclusoes"] = self.conclusoes_edit.toPlainText()
            db.salvar_laudo(laudo)

        opcoes = {
            "capa":          self.chk_capa.isChecked(),
            "identificacao": self.chk_identificacao.isChecked(),
            "art":           self.chk_art.isChecked(),
            "nr10":          self.chk_nr10.isChecked(),
            "metodologia":   self.chk_metodologia.isChecked(),
            "avaliacoes":    self.chk_avaliacoes.isChecked(),
            "graficos":      self.chk_graficos.isChecked(),
            "conclusoes":    self.chk_conclusoes.isChecked(),
            "consideracoes": self.chk_consideracoes.isChecked(),
            "fotos":         self.chk_fotos.isChecked(),
        }

        self.btn_gerar.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setFormat("Iniciando...")
        self.log_edit.clear()
        self._log("Iniciando geração do PDF...")

        self._thread = PDFThread(self._laudo_id, self._output_path, opcoes)
        self._thread.progress.connect(self._on_progress)
        self._thread.finished.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_progress(self, value: int, msg: str):
        self.progress.setValue(value)
        self.progress.setFormat(f"{value}%")
        self._log(msg)

    def _on_finished(self, path: str):
        self.progress.setValue(100)
        self.progress.setFormat("Concluído!")
        self._log(f"PDF gerado com sucesso: {path}")
        self.btn_gerar.setEnabled(True)
        self.btn_open.setEnabled(True)
        QMessageBox.information(self, "Sucesso", f"Relatório PDF gerado com sucesso!\n\n{path}")

    def _on_error(self, err: str):
        self.progress.setFormat("Erro!")
        self._log(f"ERRO: {err}")
        self.btn_gerar.setEnabled(True)
        QMessageBox.critical(self, "Erro ao gerar PDF", err)

    def _log(self, msg: str):
        self.log_edit.append(f"  {msg}")
        sb = self.log_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _open_pdf(self):
        if self._output_path and os.path.exists(self._output_path):
            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(self._output_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", self._output_path])
            else:
                subprocess.run(["xdg-open", self._output_path])
