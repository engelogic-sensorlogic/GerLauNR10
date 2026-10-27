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
from styles import (
    COLORS, ACAO_BTN, ACAO_ICON, ACAO_SPACING, ACAO_LINHA, largura_coluna_acoes
)


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
    """Cadastro dos colaboradores do cliente que fornecem informacoes para os
    laudos (item 1.3 do PDF). Quais deles entram em cada laudo e escolhido no
    cadastro do laudo."""

    _CAMPOS = ["nome", "cargo", "setor", "telefone", "email", "empresa"]

    def __init__(self, cliente_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fornecedores de Informações")
        self.setMinimumSize(760, 500)
        self.setModal(True)
        self.cliente_id = cliente_id
        cliente = db.buscar_cliente(cliente_id) or {}
        self._empresa_padrao = cliente.get("razao_social", "") or ""
        self._editando_id = None
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Fornecedores de Informações")
        title.setObjectName("section_title")
        layout.addWidget(title)

        info = QLabel("Colaboradores do cliente que passam as informações necessárias para o "
                      "laudo. Dê dois cliques em uma linha para editar.")
        info.setStyleSheet("color: #586069; font-size: 11px;")
        layout.addWidget(info)

        # Tabela
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Nome", "Cargo", "Setor", "Telefone", "E-mail", "Empresa"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(lambda row, _c: self._editar(row))
        layout.addWidget(self.table)

        # Formulário para adicionar
        form_frame = QFrame()
        form_frame.setObjectName("card")
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QVBoxLayout(form_frame)

        self.form_lbl = form_lbl = QLabel("Adicionar Fornecedor de Informações")
        form_lbl.setObjectName("card_title")
        form_lbl.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold;")
        form_layout.addWidget(form_lbl)

        grid = QHBoxLayout()
        self.e_nome = QLineEdit(); self.e_nome.setPlaceholderText("Nome do colaborador *")
        self.e_cargo = QLineEdit(); self.e_cargo.setPlaceholderText("Cargo")
        self.e_setor = QLineEdit(); self.e_setor.setPlaceholderText("Setor")
        self.e_telefone = QLineEdit(); self.e_telefone.setPlaceholderText("Telefone")
        self.e_email = QLineEdit(); self.e_email.setPlaceholderText("E-mail")
        self.e_empresa = QLineEdit(); self.e_empresa.setPlaceholderText("Empresa")
        self.e_empresa.setText(self._empresa_padrao)
        for w in self._campos():
            grid.addWidget(w)
        form_layout.addLayout(grid)

        btn_row = QHBoxLayout()
        self.btn_add = btn_add = QPushButton("+ Adicionar")
        btn_add.setObjectName("btn_success")
        btn_add.clicked.connect(self._add)
        btn_edit = QPushButton("Editar Selecionado")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.clicked.connect(lambda: self._editar(self.table.currentRow()))
        self.btn_cancel_edit = QPushButton("Cancelar edição")
        self.btn_cancel_edit.setObjectName("btn_secondary")
        self.btn_cancel_edit.clicked.connect(self._limpar_form)
        self.btn_cancel_edit.setVisible(False)
        btn_del = QPushButton("Remover Selecionado")
        btn_del.setObjectName("btn_danger")
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(self.btn_cancel_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        form_layout.addLayout(btn_row)
        layout.addWidget(form_frame)

        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btn_primary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def _campos(self):
        return [self.e_nome, self.e_cargo, self.e_setor, self.e_telefone,
                self.e_email, self.e_empresa]

    def _refresh(self):
        self.table.setRowCount(0)
        self._parts = db.listar_participantes(self.cliente_id)
        for p in self._parts:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, key in enumerate(self._CAMPOS):
                self.table.setItem(row, col, QTableWidgetItem(p.get(key, "") or ""))

    def _limpar_form(self):
        for w in self._campos():
            w.clear()
        self.e_empresa.setText(self._empresa_padrao)
        self._editando_id = None
        self.form_lbl.setText("Adicionar Fornecedor de Informações")
        self.btn_add.setText("+ Adicionar")
        self.btn_cancel_edit.setVisible(False)

    def _editar(self, row: int):
        if row < 0 or row >= len(self._parts):
            return
        p = self._parts[row]
        for w, key in zip(self._campos(), self._CAMPOS):
            w.setText(p.get(key, "") or "")
        self._editando_id = p["id"]
        self.form_lbl.setText("Editando: %s" % (p.get("nome") or ""))
        self.btn_add.setText("Salvar alterações")
        self.btn_cancel_edit.setVisible(True)
        self.e_nome.setFocus()

    def _add(self):
        nome = self.e_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o Nome do colaborador.")
            return
        dados = {key: w.text().strip() for w, key in zip(self._campos(), self._CAMPOS)}
        dados["cliente_id"] = self.cliente_id
        if self._editando_id:
            dados["id"] = self._editando_id
        db.salvar_participante(dados)
        self._limpar_form()
        self._refresh()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._parts):
            return
        p = self._parts[row]
        if QMessageBox.question(
                self, "Remover fornecedor",
                "Remover '%s' do cadastro?\n\nEle sai também de todos os laudos em "
                "que estiver indicado." % (p.get("nome") or "")
        ) != QMessageBox.StandardButton.Yes:
            return
        db.excluir_participante(p["id"])
        if self._editando_id == p["id"]:
            self._limpar_form()
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
        self.table.setColumnWidth(5, largura_coluna_acoes(4))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(ACAO_LINHA)
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
            cell_layout.setContentsMargins(6, 0, 6, 0)
            cell_layout.setSpacing(ACAO_SPACING)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            sty = self.style()

            def _icon_btn(pixmap, tooltip, slot):
                b = QPushButton(sty.standardIcon(pixmap), "")
                b.setObjectName("btn_table_icon")
                b.setFixedSize(ACAO_BTN, ACAO_BTN)
                b.setIconSize(QSize(ACAO_ICON, ACAO_ICON))
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setToolTip(tooltip)
                b.clicked.connect(slot)
                cell_layout.addWidget(b)

            cid, cnome = c["id"], c["razao_social"]
            _icon_btn(QStyle.StandardPixmap.SP_FileDialogDetailedView,
                      "Abrir Laudos deste Cliente",
                      lambda _, i=cid, n=cnome: self.open_laudos.emit(i, n))
            _icon_btn(QStyle.StandardPixmap.SP_MessageBoxInformation,
                      "Fornecedores de Informações (colaboradores do cliente)",
                      lambda _, i=cid: self._manage_participantes(i))
            _icon_btn(QStyle.StandardPixmap.SP_FileDialogNewFolder,
                      "Editar cliente",
                      lambda _, cd=c: self._edit_cliente(cd))
            _icon_btn(QStyle.StandardPixmap.SP_TrashIcon,
                      "Excluir cliente",
                      lambda _, i=cid, n=cnome: self._delete_cliente(i, n))

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
