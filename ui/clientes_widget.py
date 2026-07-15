"""
GerLauNR10 - Widget de gerenciamento de clientes
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QFileDialog, QMessageBox,
    QFrame, QScrollArea, QSizePolicy, QAbstractItemView, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon

import database as db
from styles import COLORS


# ---------------------------------------------------------------------------
# Diálogo de edição de cliente
# ---------------------------------------------------------------------------
class ClienteDialog(QDialog):
    def __init__(self, dados: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dados do Cliente" if not dados else "Editar Cliente")
        self.setMinimumWidth(500)
        self.setModal(True)
        self.dados = dados or {}
        self._logo_path = self.dados.get("logo_path", "")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Cadastro de Cliente")
        title.setObjectName("section_title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def field(placeholder=""):
            le = QLineEdit()
            le.setPlaceholderText(placeholder)
            return le

        self.e_razao = field("Razão Social")
        self.e_cnpj = field("00.000.000/0000-00")
        self.e_filial = field("Ex: Matriz, Filial 1...")
        self.e_endereco = field("Rua, número, complemento")
        self.e_cep = field("00000-000")
        self.e_cidade = field("Cidade")
        self.e_estado = field("PR")
        self.e_telefone = field("(00) 0000-0000")

        form.addRow("Razão Social *:", self.e_razao)
        form.addRow("CNPJ:", self.e_cnpj)
        form.addRow("Filial:", self.e_filial)
        form.addRow("Endereço:", self.e_endereco)
        form.addRow("CEP:", self.e_cep)
        form.addRow("Cidade:", self.e_cidade)
        form.addRow("Estado:", self.e_estado)
        form.addRow("Telefone:", self.e_telefone)

        # Logo
        logo_row = QHBoxLayout()
        self.lbl_logo = QLabel("Nenhum logo selecionado")
        self.lbl_logo.setStyleSheet("color: #8a9bb0; font-size: 11px;")
        btn_logo = QPushButton("Selecionar Logo")
        btn_logo.setObjectName("btn_secondary")
        btn_logo.setFixedWidth(140)
        btn_logo.clicked.connect(self._select_logo)
        logo_row.addWidget(self.lbl_logo)
        logo_row.addWidget(btn_logo)

        self.logo_preview = QLabel()
        self.logo_preview.setFixedHeight(60)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet("border: 1px dashed #d0d7de; border-radius: 4px;")

        form.addRow("Logotipo:", logo_row)
        form.addRow("", self.logo_preview)
        layout.addLayout(form)

        # Preenche campos se edição
        self._fill_fields()

        # Botões
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Salvar Cliente")
        btn_save.setObjectName("btn_accent")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _fill_fields(self):
        d = self.dados
        self.e_razao.setText(d.get("razao_social", ""))
        self.e_cnpj.setText(d.get("cnpj", ""))
        self.e_filial.setText(d.get("filial", ""))
        self.e_endereco.setText(d.get("endereco", ""))
        self.e_cep.setText(d.get("cep", ""))
        self.e_cidade.setText(d.get("cidade", ""))
        self.e_estado.setText(d.get("estado", ""))
        self.e_telefone.setText(d.get("telefone", ""))
        if self._logo_path:
            self.lbl_logo.setText(self._logo_path.split("/")[-1].split("\\")[-1])
            self._show_logo_preview()

    def _select_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Logotipo", "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if path:
            self._logo_path = path
            self.lbl_logo.setText(path.split("/")[-1].split("\\")[-1])
            self._show_logo_preview()

    def _show_logo_preview(self):
        if self._logo_path:
            pix = QPixmap(self._logo_path)
            if not pix.isNull():
                pix = pix.scaledToHeight(56, Qt.TransformationMode.SmoothTransformation)
                self.logo_preview.setPixmap(pix)

    def _save(self):
        razao = self.e_razao.text().strip()
        if not razao:
            QMessageBox.warning(self, "Campo obrigatório", "Informe a Razão Social.")
            return
        self.result_data = {
            "id": self.dados.get("id"),
            "razao_social": razao,
            "cnpj": self.e_cnpj.text().strip(),
            "filial": self.e_filial.text().strip(),
            "endereco": self.e_endereco.text().strip(),
            "cep": self.e_cep.text().strip(),
            "cidade": self.e_cidade.text().strip(),
            "estado": self.e_estado.text().strip(),
            "telefone": self.e_telefone.text().strip(),
            "logo_path": self._logo_path,
        }
        self.accept()


# ---------------------------------------------------------------------------
# Diálogo de participantes
# ---------------------------------------------------------------------------
class ParticipantesDialog(QDialog):
    def __init__(self, cliente_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Participantes / Fornecedores de Informações")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self.cliente_id = cliente_id
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Participantes / Fornecedores de Informações")
        title.setObjectName("section_title")
        layout.addWidget(title)

        info = QLabel("Pessoas envolvidas no projeto que forneceram informações para o laudo.")
        info.setStyleSheet("color: #586069; font-size: 11px;")
        layout.addWidget(info)

        # Tabela
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Nome", "Empresa", "Cargo", "Setor", "E-mail", "Telefone"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Formulário para adicionar
        form_frame = QFrame()
        form_frame.setObjectName("card")
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QVBoxLayout(form_frame)

        form_lbl = QLabel("Adicionar Participante")
        form_lbl.setObjectName("card_title")
        form_lbl.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold;")
        form_layout.addWidget(form_lbl)

        grid = QHBoxLayout()
        self.e_nome = QLineEdit(); self.e_nome.setPlaceholderText("Nome *")
        self.e_empresa = QLineEdit(); self.e_empresa.setPlaceholderText("Empresa")
        self.e_cargo = QLineEdit(); self.e_cargo.setPlaceholderText("Cargo")
        self.e_setor = QLineEdit(); self.e_setor.setPlaceholderText("Setor")
        self.e_email = QLineEdit(); self.e_email.setPlaceholderText("E-mail")
        self.e_telefone = QLineEdit(); self.e_telefone.setPlaceholderText("Telefone")
        for w in [self.e_nome, self.e_empresa, self.e_cargo, self.e_setor, self.e_email, self.e_telefone]:
            grid.addWidget(w)
        form_layout.addLayout(grid)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ Adicionar")
        btn_add.setObjectName("btn_success")
        btn_add.clicked.connect(self._add)
        btn_del = QPushButton("Remover Selecionado")
        btn_del.setObjectName("btn_danger")
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        form_layout.addLayout(btn_row)
        layout.addWidget(form_frame)

        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btn_primary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def _refresh(self):
        self.table.setRowCount(0)
        self._parts = db.listar_participantes(self.cliente_id)
        for p in self._parts:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, key in enumerate(["nome", "empresa", "cargo", "setor", "email", "telefone"]):
                self.table.setItem(row, col, QTableWidgetItem(p.get(key, "") or ""))

    def _add(self):
        nome = self.e_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o Nome.")
            return
        db.salvar_participante({
            "cliente_id": self.cliente_id,
            "nome": nome,
            "empresa": self.e_empresa.text().strip(),
            "cargo": self.e_cargo.text().strip(),
            "setor": self.e_setor.text().strip(),
            "email": self.e_email.text().strip(),
            "telefone": self.e_telefone.text().strip(),
        })
        for w in [self.e_nome, self.e_empresa, self.e_cargo, self.e_setor, self.e_email, self.e_telefone]:
            w.clear()
        self._refresh()

    def _delete(self):
        rows = self.table.selectedItems()
        if not rows:
            return
        row = self.table.currentRow()
        if row < len(self._parts):
            pid = self._parts[row]["id"]
            db.excluir_participante(pid)
            self._refresh()


# ---------------------------------------------------------------------------
# Widget principal de clientes
# ---------------------------------------------------------------------------
class ClientesWidget(QWidget):
    open_laudos = pyqtSignal(int, str)   # cliente_id, nome

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)

        # Cabeçalho
        header = QHBoxLayout()
        title = QLabel("🏢  Clientes Cadastrados")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()
        btn_new = QPushButton("➕  Novo Cliente")
        btn_new.setObjectName("btn_accent")
        btn_new.clicked.connect(self._new_cliente)
        header.addWidget(btn_new)
        layout.addLayout(header)

        desc = QLabel("Gerencie os clientes. Cada cliente pode ter múltiplos laudos.")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(desc)

        # Tabela
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Razão Social", "Filial", "CNPJ", "Cidade / Estado", "Telefone", "Ações"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 160)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(self.table)

    def refresh(self):
        self.table.setRowCount(0)
        self._clientes = db.listar_clientes()
        for c in self._clientes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(c.get("razao_social", "")))
            self.table.setItem(row, 1, QTableWidgetItem(c.get("filial", "") or "—"))
            self.table.setItem(row, 2, QTableWidgetItem(c.get("cnpj", "") or "—"))
            cidade_estado = f"{c.get('cidade', '')} / {c.get('estado', '')}".strip(" /")
            self.table.setItem(row, 3, QTableWidgetItem(cidade_estado or "—"))
            self.table.setItem(row, 4, QTableWidgetItem(c.get("telefone", "") or "—"))

            # Coluna de ações
            cell = QWidget()
            cell_layout = QHBoxLayout(cell)
            cell_layout.setContentsMargins(4, 2, 4, 2)
            cell_layout.setSpacing(4)

            sty = self.style()
            icon_sz = QSize(16, 16)

            # Laudos – ícone de documento/lista
            btn_laudos = QPushButton(sty.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "")
            btn_laudos.setIconSize(icon_sz)
            btn_laudos.setObjectName("btn_icon")
            btn_laudos.setToolTip("Abrir Laudos deste Cliente")
            btn_laudos.clicked.connect(lambda _, cid=c["id"], cn=c["razao_social"]: self.open_laudos.emit(cid, cn))

            # Participantes – ícone de informação/pessoas
            btn_parts = QPushButton(sty.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation), "")
            btn_parts.setIconSize(icon_sz)
            btn_parts.setObjectName("btn_icon")
            btn_parts.setToolTip("Gerenciar Participantes / Fornecedores de Informação")
            btn_parts.clicked.connect(lambda _, cid=c["id"]: self._manage_participantes(cid))

            # Editar – ícone de lápis (FileDialogNewFolder aproximado)
            btn_edit = QPushButton(
                sty.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder), ""
            )
            btn_edit.setIconSize(icon_sz)
            btn_edit.setObjectName("btn_icon")
            btn_edit.setToolTip("Editar cliente")
            btn_edit.clicked.connect(lambda _, cd=c: self._edit_cliente(cd))

            # Excluir – ícone de lixeira
            btn_del = QPushButton(
                sty.standardIcon(QStyle.StandardPixmap.SP_TrashIcon), ""
            )
            btn_del.setIconSize(icon_sz)
            btn_del.setObjectName("btn_icon")
            btn_del.setToolTip("Excluir cliente")
            btn_del.clicked.connect(lambda _, cid=c["id"], cn=c["razao_social"]: self._delete_cliente(cid, cn))

            cell_layout.addWidget(btn_laudos)
            cell_layout.addWidget(btn_parts)
            cell_layout.addWidget(btn_edit)
            cell_layout.addWidget(btn_del)
            self.table.setCellWidget(row, 5, cell)

    def _new_cliente(self):
        dlg = ClienteDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.salvar_cliente(dlg.result_data)
            self.refresh()

    def _edit_cliente(self, dados: dict):
        dlg = ClienteDialog(dados=dados, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.salvar_cliente(dlg.result_data)
            self.refresh()

    def _delete_cliente(self, cliente_id: int, nome: str):
        resp = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Excluir o cliente '{nome}'?\nTodos os laudos relacionados também serão removidos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            db.excluir_cliente(cliente_id)
            self.refresh()

    def _manage_participantes(self, cliente_id: int):
        dlg = ParticipantesDialog(cliente_id, parent=self)
        dlg.exec()
