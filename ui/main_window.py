"""
GerLauNR10 - Janela principal com sidebar de navegação
"""
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QStatusBar, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont

from ui.clientes_widget import ClientesWidget
from ui.laudos_widget import LaudosWidget
from ui.painel_widget import PainelWidget
from ui.pdf_widget import PDFWidget
from ui.configuracoes_widget import ConfiguracoesWidget
from ui.devtools_widget import DevToolsWidget
from styles import COLORS


# ---------------------------------------------------------------------------
# Botão de navegação
# ---------------------------------------------------------------------------
class NavButton(QPushButton):
    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("nav_btn")
        self.setText(f"  {icon_text}  {label}")
        self.setCheckable(False)
        self.setMinimumHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ---------------------------------------------------------------------------
# Janela Principal
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GerLauNR10 – Gerador de Laudos NR-10  |  Engelogic")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 820)

        self._current_index = 0
        self._nav_buttons = []

        self._build_ui()
        self._connect_signals()
        self._navigate(0)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Sidebar ----
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo / título
        import os
        logo_frame = QFrame()
        logo_frame.setObjectName("sidebar_logo")
        logo_frame.setFixedHeight(80)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 8, 0, 8)
        logo_layout.setSpacing(2)

        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "logo_engelogic.png")
        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_img.setStyleSheet("background: transparent; border: none;")
        lbl_img.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            pix = pix.scaled(180, 52, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_img.setPixmap(pix)
        else:
            lbl_img.setText("ENGELOGIC")
            lbl_img.setObjectName("app_title")
        logo_layout.addWidget(lbl_img)

        sub_lbl = QLabel("NR-10  •  Laudos Elétricos")
        sub_lbl.setObjectName("app_subtitle")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(sub_lbl)
        sb_layout.addWidget(logo_frame)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #243b55; max-height: 1px;")
        sb_layout.addWidget(sep)

        # Itens de navegação
        nav_items = [
            ("🏢", "Clientes"),
            ("📋", "Laudos"),
            ("✅", "Avaliação de Painel"),
            ("📄", "Gerar Relatório PDF"),
            ("⚙️", "Configurações"),
            ("🔧", "Dev Tools"),
        ]
        for i, (icon, label) in enumerate(nav_items):
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda checked, idx=i: self._navigate(idx))
            self._nav_buttons.append(btn)
            sb_layout.addWidget(btn)

        sb_layout.addStretch()

        # Versão
        ver_lbl = QLabel("  v1.0.0  |  © Engelogic")
        ver_lbl.setStyleSheet("color: #4a6580; font-size: 10px; padding: 8px 16px;")
        sb_layout.addWidget(ver_lbl)

        root.addWidget(sidebar)

        # ---- Área de conteúdo ----
        self.stack = QStackedWidget()
        self.stack.setObjectName("content_stack")

        self.w_clientes = ClientesWidget()
        self.w_laudos = LaudosWidget()
        self.w_painel = PainelWidget()
        self.w_pdf = PDFWidget()
        self.w_config = ConfiguracoesWidget()
        self.w_devtools = DevToolsWidget()

        self.stack.addWidget(self.w_clientes)   # 0
        self.stack.addWidget(self.w_laudos)     # 1
        self.stack.addWidget(self.w_painel)     # 2
        self.stack.addWidget(self.w_pdf)        # 3
        self.stack.addWidget(self.w_config)     # 4
        self.stack.addWidget(self.w_devtools)   # 5

        root.addWidget(self.stack)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto  |  GerLauNR10 – Engelogic Automação e Controle Industrial")

    def _connect_signals(self):
        # Navegação cross-widget
        self.w_clientes.open_laudos.connect(self._on_open_laudos)
        self.w_laudos.open_painel.connect(self._on_open_painel)
        self.w_laudos.open_pdf.connect(self._on_open_pdf)
        self.w_laudos.go_clientes.connect(lambda: self._navigate(0))

    def _navigate(self, index: int):
        self._current_index = index
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == index)

    def _on_open_laudos(self, cliente_id: int, cliente_nome: str):
        self.w_laudos.set_cliente(cliente_id, cliente_nome)
        self._navigate(1)
        self.status_bar.showMessage(f"Cliente: {cliente_nome}")

    def _on_open_painel(self, laudo_id: int, painel_id: int):
        self.w_painel.set_laudo_painel(laudo_id, painel_id)
        self._navigate(2)

    def _on_open_pdf(self, laudo_id: int):
        self.w_pdf.set_laudo(laudo_id)
        self._navigate(3)
