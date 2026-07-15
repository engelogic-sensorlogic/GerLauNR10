"""
GerLauNR10 - Widget de configurações e editor de checklist
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QMessageBox,
    QFrame, QTabWidget, QListWidget, QListWidgetItem,
    QSpinBox, QDoubleSpinBox, QAbstractItemView, QGroupBox,
    QScrollArea
)
from PyQt6.QtCore import Qt

import database as db
from styles import COLORS


# ---------------------------------------------------------------------------
# Diálogo de profissional
# ---------------------------------------------------------------------------
class ProfissionalDialog(QDialog):
    def __init__(self, dados: dict = None, parent=None):
        super().__init__(parent)
        self.dados = dados or {}
        self.setWindowTitle("Profissional Responsável")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Dados do Profissional Habilitado")
        title.setObjectName("section_title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.e_nome = QLineEdit(); self.e_nome.setPlaceholderText("Nome completo *")
        self.e_empresa = QLineEdit(); self.e_empresa.setPlaceholderText("Empresa / Prestador")
        self.e_hab = QLineEdit(); self.e_hab.setPlaceholderText("Ex: Engenheiro Eletricista")
        self.e_crea = QLineEdit(); self.e_crea.setPlaceholderText("Ex: CREA-PR 83611/D")
        self.e_email = QLineEdit(); self.e_email.setPlaceholderText("email@empresa.com.br")
        self.e_tel = QLineEdit(); self.e_tel.setPlaceholderText("(00) 0000-0000")

        form.addRow("Nome *:", self.e_nome)
        form.addRow("Empresa:", self.e_empresa)
        form.addRow("Habilitação:", self.e_hab)
        form.addRow("CREA:", self.e_crea)
        form.addRow("E-mail:", self.e_email)
        form.addRow("Telefone:", self.e_tel)
        layout.addLayout(form)

        d = self.dados
        self.e_nome.setText(d.get("nome", "") or "")
        self.e_empresa.setText(d.get("empresa", "") or "")
        self.e_hab.setText(d.get("habilitacao", "") or "")
        self.e_crea.setText(d.get("crea", "") or "")
        self.e_email.setText(d.get("email", "") or "")
        self.e_tel.setText(d.get("telefone", "") or "")

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Salvar")
        btn_save.setObjectName("btn_accent")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _save(self):
        nome = self.e_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o Nome.")
            return
        self.result_data = {
            "id": self.dados.get("id"),
            "nome": nome,
            "empresa": self.e_empresa.text().strip(),
            "habilitacao": self.e_hab.text().strip(),
            "crea": self.e_crea.text().strip(),
            "email": self.e_email.text().strip(),
            "telefone": self.e_tel.text().strip(),
        }
        self.accept()


# ---------------------------------------------------------------------------
# Diálogo editor de item do checklist
# ---------------------------------------------------------------------------
class ChecklistItemDialog(QDialog):
    def __init__(self, dados: dict = None, parent=None):
        super().__init__(parent)
        self.dados = dados or {}
        self.setWindowTitle("Item do Checklist")
        self.setMinimumWidth(620)
        self.setMinimumHeight(500)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Editar / Criar Item do Checklist")
        title.setObjectName("section_title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.e_numero = QSpinBox()
        self.e_numero.setRange(1, 999)
        self.e_numero.setValue(self.dados.get("numero", 1))

        self.e_questao = QTextEdit()
        self.e_questao.setPlaceholderText("Texto da questão de avaliação...")
        self.e_questao.setMaximumHeight(80)
        self.e_questao.setPlainText(self.dados.get("questao", ""))

        self.e_just = QTextEdit()
        self.e_just.setPlaceholderText("Referência normativa NR-10 correspondente...")
        self.e_just.setMaximumHeight(100)
        self.e_just.setPlainText(self.dados.get("justificativa", ""))

        form.addRow("Número:", self.e_numero)
        form.addRow("Questão *:", self.e_questao)
        form.addRow("Justificativa NR-10:", self.e_just)
        layout.addLayout(form)

        # Opções de resposta
        grp = QGroupBox("Opções de Resposta (e seus pesos)")
        grp_layout = QVBoxLayout(grp)

        info = QLabel("Peso: 1.0 = Conforme | 0.5 = Parcial | 0.0 = Não conforme | (vazio) = Não avaliado (excluído do cálculo)")
        info.setStyleSheet("color: #586069; font-size: 10px;")
        info.setWordWrap(True)
        grp_layout.addWidget(info)

        self.opcoes_table = QTableWidget(0, 2)
        self.opcoes_table.setHorizontalHeaderLabels(["Descrição da Resposta", "Peso (0.0 a 1.0)"])
        self.opcoes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.opcoes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.opcoes_table.setColumnWidth(1, 130)
        grp_layout.addWidget(self.opcoes_table)

        # Preenche opções existentes
        for opc in self.dados.get("opcoes", []):
            self._add_opcao_row(opc.get("descricao", ""), opc.get("peso"))

        opc_btns = QHBoxLayout()
        btn_add_opc = QPushButton("+ Adicionar Opção")
        btn_add_opc.setObjectName("btn_secondary")
        btn_add_opc.clicked.connect(lambda: self._add_opcao_row())
        btn_del_opc = QPushButton("Remover Opção")
        btn_del_opc.setObjectName("btn_danger")
        btn_del_opc.clicked.connect(self._del_opcao_row)
        opc_btns.addWidget(btn_add_opc)
        opc_btns.addWidget(btn_del_opc)
        opc_btns.addStretch()
        grp_layout.addLayout(opc_btns)
        layout.addWidget(grp)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Salvar Item")
        btn_save.setObjectName("btn_accent")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _add_opcao_row(self, descricao: str = "", peso=None):
        row = self.opcoes_table.rowCount()
        self.opcoes_table.insertRow(row)
        self.opcoes_table.setItem(row, 0, QTableWidgetItem(descricao))
        peso_item = QTableWidgetItem("" if peso is None else str(peso))
        self.opcoes_table.setItem(row, 1, peso_item)

    def _del_opcao_row(self):
        row = self.opcoes_table.currentRow()
        if row >= 0:
            self.opcoes_table.removeRow(row)

    def _save(self):
        questao = self.e_questao.toPlainText().strip()
        if not questao:
            QMessageBox.warning(self, "Campo obrigatório", "Informe a Questão.")
            return
        opcoes = []
        for r in range(self.opcoes_table.rowCount()):
            desc = (self.opcoes_table.item(r, 0) or QTableWidgetItem()).text().strip()
            peso_txt = (self.opcoes_table.item(r, 1) or QTableWidgetItem()).text().strip()
            if desc:
                try:
                    peso = float(peso_txt) if peso_txt else None
                except ValueError:
                    peso = None
                opcoes.append({"descricao": desc, "peso": peso})
        self.result_data = {
            "id": self.dados.get("id"),
            "numero": self.e_numero.value(),
            "questao": questao,
            "justificativa": self.e_just.toPlainText().strip(),
            "opcoes": opcoes,
        }
        self.accept()


# ---------------------------------------------------------------------------
# Widget de Configurações
# ---------------------------------------------------------------------------
class ConfiguracoesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)

        header = QLabel(" Configurações")
        header.setObjectName("page_title")
        layout.addWidget(header)

        tabs = QTabWidget()

        # ---- Tab: Profissionais ----
        prof_tab = QWidget()
        prof_layout = QVBoxLayout(prof_tab)
        prof_layout.setContentsMargins(16, 16, 16, 16)

        ph = QHBoxLayout()
        ph.addWidget(QLabel("Profissionais Responsáveis Cadastrados"))
        ph.addStretch()
        btn_new_p = QPushButton("+ Novo Profissional")
        btn_new_p.setObjectName("btn_accent")
        btn_new_p.clicked.connect(self._new_profissional)
        ph.addWidget(btn_new_p)
        prof_layout.addLayout(ph)

        self.table_prof = QTableWidget(0, 6)
        self.table_prof.setHorizontalHeaderLabels(["Nome", "Empresa", "Habilitação", "CREA", "E-mail", "Ações"])
        self.table_prof.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_prof.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_prof.setAlternatingRowColors(True)
        self.table_prof.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        prof_layout.addWidget(self.table_prof)
        tabs.addTab(prof_tab, "👤  Profissionais")

        # ---- Tab: Checklist ----
        check_tab = QWidget()
        check_layout = QVBoxLayout(check_tab)
        check_layout.setContentsMargins(16, 16, 16, 16)

        ch = QHBoxLayout()
        lbl_c = QLabel("Itens do Checklist NR-10")
        lbl_c.setStyleSheet("font-size: 13px; font-weight: bold;")
        ch.addWidget(lbl_c)
        ch.addStretch()
        btn_new_c = QPushButton("+ Novo Item")
        btn_new_c.setObjectName("btn_accent")
        btn_new_c.clicked.connect(self._new_item)
        ch.addWidget(btn_new_c)
        check_layout.addLayout(ch)

        info = QLabel("Edite as questões, opções de resposta e seus respectivos pesos para o cálculo do Nível de Aderência.")
        info.setStyleSheet("color: #586069; font-size: 11px;")
        info.setWordWrap(True)
        check_layout.addWidget(info)

        self.table_items = QTableWidget(0, 4)
        self.table_items.setHorizontalHeaderLabels(["Nº", "Questão", "Opções", "Ações"])
        self.table_items.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_items.setAlternatingRowColors(True)
        self.table_items.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_items.verticalHeader().setDefaultSectionSize(44)
        check_layout.addWidget(self.table_items)
        tabs.addTab(check_tab, "✅  Checklist")

        layout.addWidget(tabs)

        self._load_profissionais()
        self._load_items()

    def _load_profissionais(self):
        self.table_prof.setRowCount(0)
        self._profs = db.listar_profissionais()
        for p in self._profs:
            row = self.table_prof.rowCount()
            self.table_prof.insertRow(row)
            for col, key in enumerate(["nome", "empresa", "habilitacao", "crea", "email"]):
                self.table_prof.setItem(row, col, QTableWidgetItem(p.get(key, "") or ""))

            cell = QWidget()
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(4, 2, 4, 2)
            btn_e = QPushButton("Editar")
            btn_e.setObjectName("btn_icon")
            btn_e.clicked.connect(lambda _, pd=p: self._edit_profissional(pd))
            btn_d = QPushButton("Excluir")
            btn_d.setObjectName("btn_icon")
            btn_d.clicked.connect(lambda _, pid=p["id"]: self._del_profissional(pid))
            cl.addWidget(btn_e)
            cl.addWidget(btn_d)
            self.table_prof.setCellWidget(row, 5, cell)

    def _load_items(self):
        self.table_items.setRowCount(0)
        self._items = db.listar_checklist_items()
        for item in self._items:
            row = self.table_items.rowCount()
            self.table_items.insertRow(row)
            self.table_items.setItem(row, 0, QTableWidgetItem(str(item["numero"])))
            q = item["questao"]
            self.table_items.setItem(row, 1, QTableWidgetItem(q[:70] + "..." if len(q) > 70 else q))
            opc_txt = ", ".join(o["descricao"] for o in item["opcoes"][:3])
            if len(item["opcoes"]) > 3:
                opc_txt += "..."
            self.table_items.setItem(row, 2, QTableWidgetItem(opc_txt))

            cell = QWidget()
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(4, 2, 4, 2)
            btn_e = QPushButton("Editar")
            btn_e.setObjectName("btn_secondary")
            btn_e.clicked.connect(lambda _, d=item: self._edit_item(d))
            cl.addWidget(btn_e)
            cl.addStretch()
            self.table_items.setCellWidget(row, 3, cell)

    def _new_profissional(self):
        dlg = ProfissionalDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.salvar_profissional(dlg.result_data)
            self._load_profissionais()

    def _edit_profissional(self, dados: dict):
        dlg = ProfissionalDialog(dados=dados, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.salvar_profissional(dlg.result_data)
            self._load_profissionais()

    def _del_profissional(self, pid: int):
        resp = QMessageBox.question(self, "Excluir", "Excluir profissional?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            db.excluir_profissional(pid)
            self._load_profissionais()

    def _new_item(self):
        items = db.listar_checklist_items()
        next_num = max((i["numero"] for i in items), default=0) + 1
        dlg = ChecklistItemDialog(dados={"numero": next_num}, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.salvar_checklist_item(dlg.result_data)
            self._load_items()

    def _edit_item(self, dados: dict):
        dlg = ChecklistItemDialog(dados=dados, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.salvar_checklist_item(dlg.result_data)
            self._load_items()
