"""
GerLauNR10 - Estilos e tema visual
Paleta: Azul marinho profissional + âmbar elétrico
"""

# Paleta de cores
COLORS = {
    "primary": "#1a1a1a",
    "primary_dark": "#111111",
    "primary_light": "#e8820c",
    "accent": "#e8820c",
    "accent_dark": "#c56a00",
    "sidebar_bg": "#1a1a1a",
    "sidebar_hover": "#2a2a2a",
    "sidebar_active": "#3a1a00",
    "sidebar_active_border": "#e8820c",
    "content_bg": "#f0f4f8",
    "card_bg": "#ffffff",
    "border": "#d0d7de",
    "border_light": "#e8edf2",
    "text_primary": "#1a2332",
    "text_secondary": "#586069",
    "text_muted": "#8a9bb0",
    "text_white": "#ffffff",
    "success": "#1a7f37",
    "success_bg": "#dcfce7",
    "warning": "#9a6700",
    "warning_bg": "#fef3c7",
    "danger": "#b91c1c",
    "danger_bg": "#fee2e2",
    "input_bg": "#ffffff",
    "input_border": "#c8d0d8",
    "input_focus": "#e8820c",
    "table_header": "#1a1a1a",
    "table_alt": "#f8fafc",
    "table_hover": "#ebf0f7",
}


def nivel_cor(nivel: float) -> str:
    """Retorna cor baseada no nível de aderência."""
    if nivel >= 0.85:
        return COLORS["success"]
    elif nivel >= 0.60:
        return COLORS["warning"]
    else:
        return COLORS["danger"]


def nivel_label(nivel: float) -> str:
    if nivel >= 0.85:
        return "BOM"
    elif nivel >= 0.60:
        return "REGULAR"
    else:
        return "CRÍTICO"


APP_STYLESHEET = """
/* ===== GLOBAL ===== */
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #1a2332;
    background-color: #f0f4f8;
}

QMainWindow {
    background-color: #1a1a1a;
}

/* ===== SIDEBAR ===== */
#sidebar {
    background-color: #1a1a1a;
    border-right: 1px solid #2a2a2a;
    min-width: 220px;
    max-width: 220px;
}

#sidebar_logo {
    background-color: #111111;
    padding: 0px;
    border-bottom: 2px solid #e8820c;
}

#app_title {
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 0.5px;
}

#app_subtitle {
    color: #888888;
    font-size: 10px;
    letter-spacing: 0.5px;
}

/* ===== NAV BUTTONS ===== */
QPushButton#nav_btn {
    background-color: transparent;
    color: #aaaaaa;
    border: none;
    border-left: 3px solid transparent;
    text-align: left;
    padding: 12px 16px 12px 16px;
    font-size: 13px;
    border-radius: 0px;
}

QPushButton#nav_btn:hover {
    background-color: #2a2a2a;
    color: #ffffff;
    border-left: 3px solid #e8820c;
}

QPushButton#nav_btn[active="true"] {
    background-color: #2a2a2a;
    color: #ffffff;
    border-left: 3px solid #e8820c;
    font-weight: bold;
}

/* ===== CONTENT AREA ===== */
#content_stack {
    background-color: #f0f4f8;
}

/* ===== CARDS ===== */
QFrame#card {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
}

QFrame#card_header {
    background-color: #1a1a1a;
    border-radius: 8px 8px 0 0;
    padding: 10px 16px;
    color: #ffffff;
}

/* ===== LABELS ===== */
QLabel#page_title {
    font-size: 20px;
    font-weight: bold;
    color: #1a1a1a;
}

QLabel#section_title {
    font-size: 14px;
    font-weight: bold;
    color: #1a1a1a;
    border-bottom: 2px solid #e8820c;
    padding-bottom: 4px;
}

QLabel#card_title {
    font-size: 13px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#field_label {
    font-size: 12px;
    color: #586069;
    font-weight: 500;
}

QLabel#nivel_badge {
    border-radius: 4px;
    padding: 2px 8px;
    font-weight: bold;
    font-size: 11px;
}

/* ===== INPUTS ===== */
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #c8d0d8;
    border-radius: 5px;
    padding: 6px 10px;
    color: #1a2332;
    selection-background-color: #e8820c;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 2px solid #e8820c;
    outline: none;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #586069;
    width: 0;
    height: 0;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #c8d0d8;
    selection-background-color: #e8820c;
    selection-color: #ffffff;
}

/* ===== BUTTONS ===== */
QPushButton {
    background-color: #1a1a1a;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
    min-height: 32px;
}

QPushButton:hover {
    background-color: #e8820c;
}

QPushButton:pressed {
    background-color: #111111;
}

QPushButton:disabled {
    background-color: #c8d0d8;
    color: #8a9bb0;
}

QPushButton#btn_primary {
    background-color: #1a1a1a;
    color: white;
}

QPushButton#btn_accent {
    background-color: #e8820c;
    color: white;
}

QPushButton#btn_accent:hover {
    background-color: #c56a00;
}

QPushButton#btn_success {
    background-color: #1a7f37;
    color: white;
}

QPushButton#btn_success:hover {
    background-color: #145c28;
}

QPushButton#btn_danger {
    background-color: #b91c1c;
    color: white;
}

QPushButton#btn_danger:hover {
    background-color: #991b1b;
}

QPushButton#btn_secondary {
    background-color: #f0f4f8;
    color: #1a2332;
    border: 1px solid #c8d0d8;
}

QPushButton#btn_secondary:hover {
    background-color: #e2e8f0;
}

QPushButton#btn_small {
    padding: 4px 12px;
    font-size: 11px;
    min-height: 24px;
    border-radius: 4px;
}

QPushButton#btn_icon {
    background-color: transparent;
    border: 1px solid #c8d0d8;
    color: #586069;
    padding: 4px 8px;
    border-radius: 4px;
    min-width: 28px;
    min-height: 28px;
}

QPushButton#btn_icon:hover {
    background-color: #e2e8f0;
    color: #1a2332;
}

/* ===== TABLES ===== */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    gridline-color: #e8edf2;
    selection-background-color: #ebf0f7;
    selection-color: #1a2332;
    alternate-background-color: #f8fafc;
}

QTableWidget::item {
    padding: 6px 10px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #dbeafe;
    color: #1a2332;
}

QHeaderView::section {
    background-color: #1a1a1a;
    color: #ffffff;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #e8820c;
    font-weight: bold;
    font-size: 12px;
}

QHeaderView::section:last {
    border-right: none;
}

/* ===== TABS ===== */
QTabWidget::pane {
    border: 1px solid #d0d7de;
    border-radius: 0 6px 6px 6px;
    background: #ffffff;
}

QTabBar::tab {
    background: #e2e8f0;
    border: 1px solid #d0d7de;
    border-bottom: none;
    padding: 8px 20px;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    color: #586069;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #1a1a1a;
    font-weight: bold;
    border-top: 3px solid #e8820c;
}

QTabBar::tab:hover {
    background: #f0f4f8;
    color: #1a2332;
}

/* ===== SCROLLBAR ===== */
QScrollBar:vertical {
    background: #f0f4f8;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #c8d0d8;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #8a9bb0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #f0f4f8;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background: #c8d0d8;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ===== GROUPBOX ===== */
QGroupBox {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    margin-top: 16px;
    padding-top: 8px;
    font-weight: bold;
    color: #1a1a1a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #1a1a1a;
    background-color: #f0f4f8;
}

/* ===== CHECKBOX ===== */
QCheckBox {
    spacing: 8px;
    color: #1a2332;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #c8d0d8;
    border-radius: 3px;
    background: white;
}

QCheckBox::indicator:checked {
    background-color: #1a1a1a;
    border-color: #1a1a1a;
}

QCheckBox::indicator:hover {
    border-color: #e8820c;
}

/* ===== RADIO BUTTONS ===== */
QRadioButton {
    spacing: 8px;
    color: #1a2332;
    padding: 4px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #c8d0d8;
    border-radius: 9px;
    background: white;
}

QRadioButton::indicator:checked {
    background-color: #1a1a1a;
    border-color: #1a1a1a;
}

QRadioButton::indicator:hover {
    border-color: #e8820c;
}

/* ===== PROGRESSBAR ===== */
QProgressBar {
    border: 1px solid #d0d7de;
    border-radius: 4px;
    background: #e2e8f0;
    height: 16px;
    text-align: center;
    color: #1a2332;
    font-size: 11px;
    font-weight: bold;
}

QProgressBar::chunk {
    border-radius: 3px;
    background-color: #e8820c;
}

/* ===== SPLITTER ===== */
QSplitter::handle {
    background: #d0d7de;
}

QSplitter::handle:horizontal {
    width: 3px;
}

/* ===== STATUSBAR ===== */
QStatusBar {
    background-color: #1a1a1a;
    color: #b0c0d4;
    font-size: 11px;
    padding: 2px 8px;
}

/* ===== MESSAGES ===== */
QMessageBox {
    background-color: #ffffff;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* ===== DIALOG ===== */
QDialog {
    background-color: #f0f4f8;
}

/* ===== TOOLBOX ===== */
QToolTip {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #e8820c;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}

/* ===== SPIN BOX ===== */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #c8d0d8;
    border-radius: 5px;
    padding: 5px 8px;
    color: #1a2332;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #e8820c;
}
"""
