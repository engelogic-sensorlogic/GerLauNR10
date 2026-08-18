"""
GerLauNR10 - Aba com as instrucoes de instalacao do aplicativo de campo
"""
import io
import webbrowser

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QLineEdit, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

URL_APP = "https://engelogic-sensorlogic.github.io/GerLauNR10/"


def _qrcode_pixmap(texto: str, lado: int = 240) -> QPixmap:
    """Gera o QR Code como QPixmap. Devolve um pixmap nulo se a biblioteca
    qrcode nao estiver instalada -- a aba continua util so com o link."""
    try:
        import qrcode
    except ImportError:
        return QPixmap()
    try:
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(texto)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue(), "PNG")
        return pix.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
    except Exception:
        return QPixmap()


class CelularWidget(QWidget):
    """Instrucoes para instalar o aplicativo de coleta em campo nos aparelhos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        topo = QHBoxLayout()
        topo.addWidget(self._grupo_instalacao(), 1)
        topo.addWidget(self._grupo_passos(), 1)
        layout.addLayout(topo)
        layout.addStretch()

    def _grupo_instalacao(self) -> QGroupBox:
        cx = QGroupBox("Instalar no celular ou tablet")
        v = QVBoxLayout(cx)
        v.setSpacing(10)

        ajuda = QLabel(
            "Aponte a câmera do aparelho para o código abaixo, ou digite o "
            "endereço no navegador."
        )
        ajuda.setWordWrap(True)
        ajuda.setStyleSheet("color: #586069; font-size: 11px;")
        v.addWidget(ajuda)

        qr = QLabel()
        qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = _qrcode_pixmap(URL_APP)
        if pix.isNull():
            qr.setText("Instale a biblioteca qrcode para exibir o código:\n"
                       "pip install qrcode")
            qr.setStyleSheet("color: #b91c1c; font-size: 11px; padding: 20px;"
                             "border: 1px dashed #e8b4b4; border-radius: 6px;")
        else:
            qr.setPixmap(pix)
            qr.setStyleSheet("background: #ffffff; border: 1px solid #d0d7de;"
                             "border-radius: 6px; padding: 10px;")
        v.addWidget(qr)

        v.addWidget(QLabel("Endereço do aplicativo:"))
        linha = QHBoxLayout()
        self.e_url = QLineEdit(URL_APP)
        self.e_url.setReadOnly(True)
        self.e_url.setCursorPosition(0)
        linha.addWidget(self.e_url)
        btn_copiar = QPushButton("Copiar")
        btn_copiar.setObjectName("btn_secondary")
        btn_copiar.setFixedWidth(90)
        btn_copiar.clicked.connect(self._copiar)
        linha.addWidget(btn_copiar)
        v.addLayout(linha)

        btn_abrir = QPushButton("Abrir no navegador do computador")
        btn_abrir.setObjectName("btn_secondary")
        btn_abrir.clicked.connect(lambda: webbrowser.open(URL_APP))
        v.addWidget(btn_abrir)
        return cx

    def _grupo_passos(self) -> QGroupBox:
        cx = QGroupBox("Como usar")
        v = QVBoxLayout(cx)
        v.setSpacing(8)

        passos = QLabel(
            "<b>1. Instalar no aparelho</b><br>"
            "Abra o endereço no <b>Chrome</b> do Android e toque em "
            "<b>Instalar na tela inicial</b> (ou menu ⋮ › Instalar aplicativo). "
            "O ícone <b>NR10</b> vai para a tela inicial.<br><br>"

            "<b>2. Carregar o checklist</b><br>"
            "Na aba <i>Backup</i>, use <b>Exportar checklist para o aplicativo "
            "de campo</b> e leve o arquivo <b>.json</b> para o aparelho. No "
            "aplicativo, toque em <b>Carregar checklist do PC</b>. Repita sempre "
            "que editar o checklist.<br><br>"

            "<b>3. Coletar em campo</b><br>"
            "Preencha os dados do painel, responda as 10 perguntas e tire as "
            "fotos. Funciona sem internet.<br><br>"

            "<b>4. Trazer para o computador</b><br>"
            "Toque em <b>Gerar pacote do painel</b> e <b>Salvar arquivo</b>. "
            "Envie o <b>.zip</b> por WhatsApp, e-mail, Drive ou cabo USB e "
            "importe aqui em <i>Backup › Importar</i>.<br><br>"

            "<b>Atualizações</b><br>"
            "Quando houver uma versão nova, use <b>Atualizar aplicativo</b> "
            "dentro do próprio aplicativo — não é preciso desinstalar."
        )
        passos.setWordWrap(True)
        passos.setTextFormat(Qt.TextFormat.RichText)
        passos.setStyleSheet("font-size: 12px; line-height: 140%;")
        passos.setAlignment(Qt.AlignmentFlag.AlignTop)
        v.addWidget(passos)
        v.addStretch()
        return cx

    def _copiar(self):
        QApplication.clipboard().setText(URL_APP)
        QMessageBox.information(self, "Endereço copiado",
                                "O endereço foi copiado:\n\n%s" % URL_APP)
