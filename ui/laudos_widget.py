"""
GerLauNR10 - Widget de gerenciamento de laudos e painéis
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QDateEdit, QFileDialog,
    QMessageBox, QFrame, QComboBox, QListWidget, QListWidgetItem,
    QSplitter, QAbstractItemView, QCheckBox, QScrollArea,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont, QPixmap

import database as db
from styles import COLORS, nivel_cor, nivel_label


# ---------------------------------------------------------------------------
# Diálogo novo/editar laudo
# ---------------------------------------------------------------------------
class LaudoDialog(QDialog):
    def __init__(self, cliente_id: int, dados: dict = None, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.dados = dados or {}
        self.setWindowTitle("Novo Laudo" if not dados else "Editar Laudo")
        self.setMinimumWidth(680)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Informações do Laudo")
        title.setObjectName("section_title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.e_numero = QLineEdit(); self.e_numero.setPlaceholderText("Ex: 2024-001")
        self.e_titulo = QLineEdit(); self.e_titulo.setPlaceholderText("Inspeção de Painéis Elétricos – NR-10")
        self.e_cidade = QLineEdit(); self.e_cidade.setPlaceholderText("Londrina – PR")

        self.e_inicio = QDateEdit()
        self.e_inicio.setCalendarPopup(True)
        self.e_inicio.setDate(QDate.currentDate())
        self.e_inicio.setDisplayFormat("dd/MM/yyyy")

        self.e_fim = QDateEdit()
        self.e_fim.setCalendarPopup(True)
        self.e_fim.setDate(QDate.currentDate())
        self.e_fim.setDisplayFormat("dd/MM/yyyy")

        self.e_status = QComboBox()
        self.e_status.addItems(["Em andamento", "Concluído", "Revisão"])

        form.addRow("Número do Laudo:", self.e_numero)
        form.addRow("Título:", self.e_titulo)
        form.addRow("Cidade:", self.e_cidade)
        form.addRow("Período Início:", self.e_inicio)
        form.addRow("Período Fim:", self.e_fim)
        form.addRow("Status:", self.e_status)
        layout.addLayout(form)

        # Profissionais responsáveis
        grp_prof = QGroupBox("Profissionais Responsáveis (Engenheiros Habilitados)")
        grp_layout = QVBoxLayout(grp_prof)

        prof_header = QHBoxLayout()
        prof_lbl = QLabel("Selecione os profissionais vinculados a este laudo:")
        prof_lbl.setStyleSheet("font-size: 11px; color: #586069;")
        btn_novo_prof = QPushButton("+ Cadastrar Novo")
        btn_novo_prof.setObjectName("btn_secondary")
        btn_novo_prof.setFixedWidth(140)
        btn_novo_prof.clicked.connect(self._new_profissional)
        prof_header.addWidget(prof_lbl)
        prof_header.addStretch()
        prof_header.addWidget(btn_novo_prof)
        grp_layout.addLayout(prof_header)

        self.list_prof = QListWidget()
        self.list_prof.setFixedHeight(120)
        grp_layout.addWidget(self.list_prof)
        layout.addWidget(grp_prof)

        # ART
        art_row = QHBoxLayout()
        self.lbl_art = QLabel("Nenhum arquivo ART selecionado")
        self.lbl_art.setStyleSheet("color: #8a9bb0; font-size: 11px;")
        btn_art = QPushButton("📎 Selecionar ART (PDF)")
        btn_art.setObjectName("btn_secondary")
        btn_art.clicked.connect(self._select_art)
        art_row.addWidget(self.lbl_art)
        art_row.addWidget(btn_art)
        layout.addLayout(art_row)

        # Preenchimento
        self._fill_fields()
        self._load_profissionais()

        # Botões
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Salvar Laudo")
        btn_save.setObjectName("btn_accent")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _fill_fields(self):
        d = self.dados
        self.e_numero.setText(d.get("numero", "") or "")
        self.e_titulo.setText(d.get("titulo", "") or "")
        self.e_cidade.setText(d.get("cidade_laudo", "") or "")
        if d.get("periodo_inicio"):
            try:
                parts = d["periodo_inicio"].split("-")
                self.e_inicio.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            except Exception:
                pass
        if d.get("periodo_fim"):
            try:
                parts = d["periodo_fim"].split("-")
                self.e_fim.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            except Exception:
                pass
        idx = self.e_status.findText(d.get("status", "Em andamento"))
        if idx >= 0:
            self.e_status.setCurrentIndex(idx)
        self._art_path = d.get("art_pdf_path", "") or ""
        if self._art_path:
            self.lbl_art.setText(self._art_path.split("/")[-1].split("\\")[-1])

    def _load_profissionais(self):
        self.list_prof.clear()
        todos = db.listar_profissionais()
        vinculados_ids = {p["id"] for p in db.profissionais_do_laudo(self.dados.get("id", -1))}
        for p in todos:
            item = QListWidgetItem(f"{p['nome']}  —  {p.get('crea', '')}  |  {p.get('empresa', '')}")
            item.setData(Qt.ItemDataRole.UserRole, p["id"])
            item.setCheckState(
                Qt.CheckState.Checked if p["id"] in vinculados_ids else Qt.CheckState.Unchecked
            )
            self.list_prof.addItem(item)

    def _new_profissional(self):
        from ui.configuracoes_widget import ProfissionalDialog
        dlg = ProfissionalDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.salvar_profissional(dlg.result_data)
            self._load_profissionais()

    def _select_art(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar ART", "", "PDF (*.pdf)"
        )
        if path:
            self._art_path = path
            self.lbl_art.setText(path.split("/")[-1].split("\\")[-1])

    def _save(self):
        titulo = self.e_titulo.text().strip()
        if not titulo:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o Título do Laudo.")
            return
        self.result_data = {
            "id": self.dados.get("id"),
            "cliente_id": self.cliente_id,
            "numero": self.e_numero.text().strip(),
            "titulo": titulo,
            "cidade_laudo": self.e_cidade.text().strip(),
            "periodo_inicio": self.e_inicio.date().toString("yyyy-MM-dd"),
            "periodo_fim": self.e_fim.date().toString("yyyy-MM-dd"),
            "status": self.e_status.currentText(),
            "art_pdf_path": getattr(self, "_art_path", ""),
        }
        # Profissionais selecionados
        self.prof_ids_selecionados = []
        for i in range(self.list_prof.count()):
            item = self.list_prof.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.prof_ids_selecionados.append(item.data(Qt.ItemDataRole.UserRole))
        self.accept()


# ---------------------------------------------------------------------------
# Diálogo de painel (identificação)
# ---------------------------------------------------------------------------
class PainelDialog(QDialog):
    def __init__(self, laudo_id: int, dados: dict = None, parent=None):
        super().__init__(parent)
        self.laudo_id = laudo_id
        self.dados = dados or {}
        self.setWindowTitle("Identificação do Painel")
        self.setMinimumWidth(620)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # ── Área rolável ──────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(12)
        scroll.setWidget(inner)
        root.addWidget(scroll)

        title = QLabel("Dados de Identificação do Painel")
        title.setObjectName("section_title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.e_form_num = QLineEdit(); self.e_form_num.setPlaceholderText("Ex: 01")
        self.e_tag = QLineEdit(); self.e_tag.setPlaceholderText("Ex: QDG-01")
        self.e_setor = QLineEdit(); self.e_setor.setPlaceholderText("Ex: Produção")

        self.e_tipo = QComboBox()
        self.e_tipo.addItems([
            "QDG - Quadro Geral",
            "QDS - Quadro de Distribuição",
            "CCM - Centro de Controle de Motores",
            "QF - Quadro de Força",
            "QC - Quadro de Comando",
            "QGBT - Quadro Geral Baixa Tensão",
            "PP - Painel de Processo",
            "Outro",
        ])
        self.e_tipo.setEditable(True)

        self.e_tensao_forca = QLineEdit(); self.e_tensao_forca.setPlaceholderText("Ex: 380V")
        self.e_tensao_cmd = QLineEdit(); self.e_tensao_cmd.setPlaceholderText("Ex: 24Vcc")
        self.e_fases = QComboBox()
        self.e_fases.addItems(["3 Fases", "1 Fase", "2 Fases", "1 Fase + N"])

        self.e_data = QDateEdit()
        self.e_data.setCalendarPopup(True)
        self.e_data.setDate(QDate.currentDate())
        self.e_data.setDisplayFormat("dd/MM/yyyy")

        self.e_descricao = QTextEdit()
        self.e_descricao.setPlaceholderText("Descrição geral do painel e equipamentos...")
        self.e_descricao.setMaximumHeight(80)

        form.addRow("Nº Formulário:", self.e_form_num)
        form.addRow("TAG do Painel *:", self.e_tag)
        form.addRow("Setor:", self.e_setor)
        form.addRow("Tipo de Painel:", self.e_tipo)
        form.addRow("Tensão de Força:", self.e_tensao_forca)
        form.addRow("Tensão de Comando:", self.e_tensao_cmd)
        form.addRow("Número de Fases:", self.e_fases)
        form.addRow("Data da Avaliação:", self.e_data)
        form.addRow("Descrição:", self.e_descricao)
        layout.addLayout(form)

        # ── Fotos de identificação visual ─────────────────────────────────────
        foto_title = QLabel("Fotos de Identificação Visual")
        foto_title.setObjectName("section_title")
        layout.addWidget(foto_title)

        foto_info = QLabel(
            "Adicione até 4 fotos do painel para o relatório (Identificação Visual)."
        )
        foto_info.setStyleSheet("color: #586069; font-size: 11px;")
        foto_info.setWordWrap(True)
        layout.addWidget(foto_info)

        self._foto_paths = {
            "frontal": "",
            "lateral_dir": "",
            "lateral_esq": "",
            "traseira": "",
        }
        self._foto_labels = {}

        foto_grid = QGridLayout()
        foto_grid.setSpacing(8)
        configs = [
            ("frontal",     "📷 Frontal",          0, 0),
            ("lateral_dir", "📷 Lateral Direita",   0, 1),
            ("lateral_esq", "📷 Lateral Esquerda",  1, 0),
            ("traseira",    "📷 Traseira",           1, 1),
        ]
        for key, label_txt, row, col in configs:
            grp = QGroupBox(label_txt)
            grp_lay = QVBoxLayout(grp)
            grp_lay.setSpacing(4)

            lbl = QLabel("Nenhuma foto selecionada")
            lbl.setStyleSheet(
                "color: #8a9bb0; font-size: 10px; border: 1px dashed #c8d0d8;"
                "border-radius: 4px; padding: 6px;"
            )
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedHeight(100)
            self._foto_labels[key] = lbl
            grp_lay.addWidget(lbl)

            btn_row2 = QHBoxLayout()
            btn_sel = QPushButton("Selecionar")
            btn_sel.setObjectName("btn_secondary")
            btn_sel.setFixedHeight(28)
            btn_sel.clicked.connect(lambda checked, k=key: self._pick_foto(k))
            btn_clr = QPushButton("✕")
            btn_clr.setObjectName("btn_danger")
            btn_clr.setFixedSize(28, 28)
            btn_clr.clicked.connect(lambda checked, k=key: self._clear_foto(k))
            btn_row2.addWidget(btn_sel)
            btn_row2.addWidget(btn_clr)
            grp_lay.addLayout(btn_row2)

            foto_grid.addWidget(grp, row, col)

        layout.addLayout(foto_grid)
        self._fill_fields()

        # ── Botões ────────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Salvar Painel")
        btn_save.setObjectName("btn_accent")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _pick_foto(self, key: str):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto",
            filter="Imagens (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self._foto_paths[key] = path
            self._set_foto_preview(key, path)

    def _set_foto_preview(self, key: str, path: str):
        lbl = self._foto_labels[key]
        pix = QPixmap(path)
        if pix.isNull():
            self._clear_foto(key)
            return
        scaled = pix.scaled(
            160, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        lbl.setPixmap(scaled)
        lbl.setText("")
        lbl.setToolTip(path)
        lbl.setStyleSheet(
            "border: 1px solid #1a7f37; border-radius: 4px; padding: 4px;"
        )

    def _clear_foto(self, key: str):
        self._foto_paths[key] = ""
        lbl = self._foto_labels[key]
        lbl.setPixmap(QPixmap())
        lbl.setText("Nenhuma foto selecionada")
        lbl.setToolTip("")
        lbl.setStyleSheet(
            "color: #8a9bb0; font-size: 10px; border: 1px dashed #c8d0d8;"
            "border-radius: 4px; padding: 6px;"
        )

    def _fill_fields(self):
        d = self.dados
        self.e_form_num.setText(str(d.get("formulario_num", "")) or "")
        self.e_tag.setText(d.get("tag", "") or "")
        self.e_setor.setText(d.get("setor", "") or "")
        idx = self.e_tipo.findText(d.get("tipo_painel", ""), Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.e_tipo.setCurrentIndex(idx)
        elif d.get("tipo_painel"):
            self.e_tipo.setCurrentText(d["tipo_painel"])
        self.e_tensao_forca.setText(d.get("tensao_forca", "") or "")
        self.e_tensao_cmd.setText(d.get("tensao_comando", "") or "")
        self.e_descricao.setPlainText(d.get("descricao", "") or "")
        if d.get("data_avaliacao"):
            try:
                parts = d["data_avaliacao"].split("-")
                self.e_data.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            except Exception:
                pass
        # Carrega fotos existentes (edição)
        if d.get("id"):
            fotos = db.buscar_fotos_identificacao(d["id"])
            for key in self._foto_paths:
                p = fotos.get(key, "")
                if p:
                    self._foto_paths[key] = p
                    self._set_foto_preview(key, p)

    def _save(self):
        tag = self.e_tag.text().strip()
        if not tag:
            QMessageBox.warning(self, "Campo obrigatório", "Informe a TAG do Painel.")
            return
        try:
            form_num = int(self.e_form_num.text().strip()) if self.e_form_num.text().strip() else None
        except ValueError:
            form_num = None
        self.result_data = {
            "id": self.dados.get("id"),
            "laudo_id": self.laudo_id,
            "formulario_num": form_num,
            "tag": tag,
            "setor": self.e_setor.text().strip(),
            "tipo_painel": self.e_tipo.currentText(),
            "tensao_forca": self.e_tensao_forca.text().strip(),
            "tensao_comando": self.e_tensao_cmd.text().strip(),
            "num_fases": self.e_fases.currentText(),
            "data_avaliacao": self.e_data.date().toString("yyyy-MM-dd"),
            "descricao": self.e_descricao.toPlainText().strip(),
            "_fotos_id": self._foto_paths.copy(),
        }
        self.accept()


# ---------------------------------------------------------------------------
# Widget principal de laudos
# ---------------------------------------------------------------------------
class LaudosWidget(QWidget):
    open_painel = pyqtSignal(int, int)   # laudo_id, painel_id
    open_pdf = pyqtSignal(int)           # laudo_id
    go_clientes = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cliente_id = None
        self._cliente_nome = ""
        self._laudo_id = None
        self._build_ui()

    def set_cliente(self, cliente_id: int, nome: str):
        self._cliente_id = cliente_id
        self._cliente_nome = nome
        self.lbl_cliente.setText(f"Cliente:  {nome}")
        self._load_laudos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        self.lbl_title = QLabel(" Laudos")
        self.lbl_title.setObjectName("page_title")
        btn_back = QPushButton("◀ Clientes")
        btn_back.setObjectName("btn_secondary")
        btn_back.clicked.connect(self.go_clientes)
        header.addWidget(self.lbl_title)
        header.addStretch()
        header.addWidget(btn_back)
        layout.addLayout(header)

        self.lbl_cliente = QLabel()
        self.lbl_cliente.setStyleSheet(f"color: {COLORS['primary_light']}; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.lbl_cliente)

        # Splitter vertical: laudos acima | painéis abaixo
        splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Painel superior: laudos ---
        left = QFrame()
        left.setObjectName("card")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        lh = QHBoxLayout()
        lh.setContentsMargins(12, 10, 12, 8)
        lbl_l = QLabel("Laudos")
        lbl_l.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {COLORS['primary']};")
        btn_new_laudo = QPushButton("+ Novo Laudo")
        btn_new_laudo.setObjectName("btn_accent")
        btn_new_laudo.clicked.connect(self._new_laudo)
        lh.addWidget(lbl_l)
        lh.addStretch()
        lh.addWidget(btn_new_laudo)
        left_layout.addLayout(lh)

        self.table_laudos = QTableWidget(0, 4)
        self.table_laudos.setHorizontalHeaderLabels(["Número", "Título", "Período", "Status"])
        self.table_laudos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_laudos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_laudos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_laudos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_laudos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_laudos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_laudos.setAlternatingRowColors(True)
        self.table_laudos.verticalHeader().setDefaultSectionSize(32)
        self.table_laudos.setMinimumHeight(140)
        self.table_laudos.currentItemChanged.connect(self._on_laudo_selected)
        left_layout.addWidget(self.table_laudos)

        # Botões do laudo
        laudo_btns = QHBoxLayout()
        laudo_btns.setContentsMargins(8, 6, 8, 8)
        self.btn_edit_laudo = QPushButton("Editar")
        self.btn_edit_laudo.setObjectName("btn_secondary")
        self.btn_edit_laudo.setEnabled(False)
        self.btn_edit_laudo.clicked.connect(self._edit_laudo)
        self.btn_del_laudo = QPushButton("Excluir")
        self.btn_del_laudo.setObjectName("btn_danger")
        self.btn_del_laudo.setEnabled(False)
        self.btn_del_laudo.clicked.connect(self._delete_laudo)
        self.btn_pdf = QPushButton("📄 Gerar PDF")
        self.btn_pdf.setObjectName("btn_success")
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self._open_pdf)
        laudo_btns.addWidget(self.btn_edit_laudo)
        laudo_btns.addWidget(self.btn_del_laudo)
        laudo_btns.addStretch()
        laudo_btns.addWidget(self.btn_pdf)
        left_layout.addLayout(laudo_btns)

        splitter.addWidget(left)

        # --- Painel inferior: painéis do laudo ---
        right = QFrame()
        right.setObjectName("card")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        rh = QHBoxLayout()
        rh.setContentsMargins(12, 10, 12, 8)
        lbl_r = QLabel("Painéis do Laudo")
        lbl_r.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {COLORS['primary']};")
        self.btn_new_painel = QPushButton("+ Adicionar Painel")
        self.btn_new_painel.setObjectName("btn_accent")
        self.btn_new_painel.setEnabled(False)
        self.btn_new_painel.clicked.connect(self._new_painel)
        rh.addWidget(lbl_r)
        rh.addStretch()
        rh.addWidget(self.btn_new_painel)
        right_layout.addLayout(rh)

        self.table_paineis = QTableWidget(0, 5)
        self.table_paineis.setHorizontalHeaderLabels(["Nº Form", "TAG", "Setor", "Tipo", "Nível"])
        self.table_paineis.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_paineis.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_paineis.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_paineis.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_paineis.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_paineis.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_paineis.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_paineis.setAlternatingRowColors(True)
        self.table_paineis.verticalHeader().setDefaultSectionSize(32)
        self.table_paineis.setMinimumHeight(140)
        right_layout.addWidget(self.table_paineis)

        painel_btns = QHBoxLayout()
        painel_btns.setContentsMargins(8, 6, 8, 8)
        self.btn_eval = QPushButton("✅ Preencher Avaliação")
        self.btn_eval.setObjectName("btn_primary")
        self.btn_eval.setEnabled(False)
        self.btn_eval.clicked.connect(self._open_avaliacao)
        self.btn_edit_painel = QPushButton("Editar")
        self.btn_edit_painel.setObjectName("btn_secondary")
        self.btn_edit_painel.setEnabled(False)
        self.btn_edit_painel.clicked.connect(self._edit_painel)
        self.btn_del_painel = QPushButton("Excluir")
        self.btn_del_painel.setObjectName("btn_danger")
        self.btn_del_painel.setEnabled(False)
        self.btn_del_painel.clicked.connect(self._delete_painel)
        painel_btns.addWidget(self.btn_eval)
        painel_btns.addWidget(self.btn_edit_painel)
        painel_btns.addWidget(self.btn_del_painel)
        painel_btns.addStretch()
        right_layout.addLayout(painel_btns)

        self.table_paineis.currentItemChanged.connect(self._on_painel_selected)
        splitter.addWidget(right)
        splitter.setSizes([300, 320])

        layout.addWidget(splitter)

    def _load_laudos(self):
        self.table_laudos.setRowCount(0)
        if not self._cliente_id:
            return
        self._laudos = db.listar_laudos(self._cliente_id)
        for l in self._laudos:
            row = self.table_laudos.rowCount()
            self.table_laudos.insertRow(row)
            self.table_laudos.setItem(row, 0, QTableWidgetItem(l.get("numero", "") or "—"))
            self.table_laudos.setItem(row, 1, QTableWidgetItem(l.get("titulo", "") or "—"))
            periodo = f"{l.get('periodo_inicio', '') or ''} a {l.get('periodo_fim', '') or ''}"
            self.table_laudos.setItem(row, 2, QTableWidgetItem(periodo.strip(" a ")))
            status_item = QTableWidgetItem(l.get("status", "—"))
            cor = {"Concluído": "#1a7f37", "Em andamento": "#9a6700", "Revisão": "#b91c1c"}.get(
                l.get("status", ""), "#586069"
            )
            status_item.setForeground(QColor(cor))
            self.table_laudos.setItem(row, 3, status_item)

    def _load_paineis(self):
        self.table_paineis.setRowCount(0)
        if not self._laudo_id:
            return
        self._paineis = db.listar_paineis(self._laudo_id)
        for p in self._paineis:
            row = self.table_paineis.rowCount()
            self.table_paineis.insertRow(row)
            self.table_paineis.setItem(row, 0, QTableWidgetItem(str(p.get("formulario_num", "") or "")))
            self.table_paineis.setItem(row, 1, QTableWidgetItem(p.get("tag", "") or "—"))
            self.table_paineis.setItem(row, 2, QTableWidgetItem(p.get("setor", "") or "—"))
            self.table_paineis.setItem(row, 3, QTableWidgetItem(p.get("tipo_painel", "") or "—"))
            nivel = p.get("nivel_aderencia", 0.0) or 0.0
            nivel_item = QTableWidgetItem(f"{nivel*100:.1f}%  {nivel_label(nivel)}")
            nivel_item.setForeground(QColor(nivel_cor(nivel)))
            nivel_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self.table_paineis.setItem(row, 4, nivel_item)

    def _on_laudo_selected(self, current, _):
        if current is None:
            self._laudo_id = None
            self.btn_edit_laudo.setEnabled(False)
            self.btn_del_laudo.setEnabled(False)
            self.btn_pdf.setEnabled(False)
            self.btn_new_painel.setEnabled(False)
            return
        row = current.row()
        if row < len(self._laudos):
            self._laudo_id = self._laudos[row]["id"]
            self.btn_edit_laudo.setEnabled(True)
            self.btn_del_laudo.setEnabled(True)
            self.btn_pdf.setEnabled(True)
            self.btn_new_painel.setEnabled(True)
            self._load_paineis()

    def _on_painel_selected(self, current, _):
        has = current is not None
        self.btn_eval.setEnabled(has)
        self.btn_edit_painel.setEnabled(has)
        self.btn_del_painel.setEnabled(has)

    def _new_laudo(self):
        if not self._cliente_id:
            return
        dlg = LaudoDialog(self._cliente_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            lid = db.salvar_laudo(dlg.result_data)
            for pid in dlg.prof_ids_selecionados:
                db.vincular_profissional_laudo(lid, pid)
            for part in db.listar_participantes(self._cliente_id):
                db.vincular_participante_laudo(lid, part["id"])
            self._load_laudos()

    def _edit_laudo(self):
        row = self.table_laudos.currentRow()
        if row < 0 or row >= len(self._laudos):
            return
        dados = self._laudos[row]
        dlg = LaudoDialog(self._cliente_id, dados=dados, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.salvar_laudo(dlg.result_data)
            for p in db.profissionais_do_laudo(dados["id"]):
                db.desvincular_profissional_laudo(dados["id"], p["id"])
            for pid in dlg.prof_ids_selecionados:
                db.vincular_profissional_laudo(dados["id"], pid)
            self._load_laudos()

    def _delete_laudo(self):
        row = self.table_laudos.currentRow()
        if row < 0 or row >= len(self._laudos):
            return
        laudo = self._laudos[row]
        resp = QMessageBox.question(
            self, "Confirmar excl\u00fasao",
            f"Excluir laudo \"{laudo.get('titulo', '')}\"?\nTodos os pain\u00e9is e avalia\u00e7\u00f5es ser\u00e3o removidos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            db.excluir_laudo(laudo["id"])
            self._laudo_id = None
            self._load_laudos()
            self.table_paineis.setRowCount(0)

    def _new_painel(self):
        if not self._laudo_id:
            return
        paineis = db.listar_paineis(self._laudo_id)
        proximo = len(paineis) + 1
        dlg = PainelDialog(self._laudo_id, dados={"formulario_num": proximo}, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fotos_id = dlg.result_data.pop("_fotos_id", {})
            pid = db.salvar_painel(dlg.result_data)
            db.salvar_fotos_identificacao(
                pid,
                frontal=fotos_id.get("frontal", ""),
                lateral_dir=fotos_id.get("lateral_dir", ""),
                lateral_esq=fotos_id.get("lateral_esq", ""),
                traseira=fotos_id.get("traseira", ""),
            )
            self._load_paineis()

    def _edit_painel(self):
        row = self.table_paineis.currentRow()
        if row < 0 or row >= len(self._paineis):
            return
        dados = self._paineis[row]
        dlg = PainelDialog(self._laudo_id, dados=dados, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fotos_id = dlg.result_data.pop("_fotos_id", {})
            pid = db.salvar_painel(dlg.result_data)
            db.salvar_fotos_identificacao(
                pid,
                frontal=fotos_id.get("frontal", ""),
                lateral_dir=fotos_id.get("lateral_dir", ""),
                lateral_esq=fotos_id.get("lateral_esq", ""),
                traseira=fotos_id.get("traseira", ""),
            )
            self._load_paineis()

    def _delete_painel(self):
        row = self.table_paineis.currentRow()
        if row < 0 or row >= len(self._paineis):
            return
        painel = self._paineis[row]
        resp = QMessageBox.question(
            self, "Confirmar excl\u00fasao",
            f"Excluir painel \"{painel.get('tag', '')}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            db.excluir_painel(painel["id"])
            self._load_paineis()

    def _open_avaliacao(self):
        row = self.table_paineis.currentRow()
        if row < 0 or row >= len(self._paineis):
            return
        painel = self._paineis[row]
        self.open_painel.emit(self._laudo_id, painel["id"])

    def _open_pdf(self):
        if self._laudo_id:
            self.open_pdf.emit(self._laudo_id)
