"""
GerLauNR10 – Gerador de Laudos NR-10
Engelogic Automação e Controle Industrial
Ponto de entrada da aplicação
"""
import sys
import os
from pathlib import Path

# Garante que o diretório do script está no path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QIcon

import database as db
from styles import APP_STYLESHEET
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GerLauNR10")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Engelogic")
    app.setOrganizationDomain("engelogic.com.br")

    # Aplica tema
    app.setStyleSheet(APP_STYLESHEET)

    # Fonte padrão
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Inicializa banco de dados
    db.init_db()

    # Splash screen simples
    splash_pix = QPixmap(480, 280)
    splash_pix.fill(Qt.GlobalColor.transparent)

    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.setStyleSheet("""
        QSplashScreen {
            background-color: #1e3a5f;
            border: 2px solid #e8820c;
            border-radius: 8px;
        }
    """)
    splash.showMessage(
        "  GerLauNR10  –  Engelogic\n  Carregando...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        Qt.GlobalColor.white
    )
    splash.show()
    app.processEvents()

    # Janela principal
    window = MainWindow()

    QTimer.singleShot(1200, lambda: (splash.finish(window), window.show()))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
