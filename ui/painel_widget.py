"""
GerLauNR10 - Widget de avaliação de painel (checklist NR-10)
Otimizado para uso em tablet e desktop
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTextEdit, QButtonGroup, QRadioButton,
    QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap

import database as db
from styles import COLORS, nivel_cor, nivel_label

# Paleta preto+laranja para o dashboard
C_BLACK  = "#1a1a1a"
C_ORANGE = "#e8820c"
C_DARK   = "#2a2a2a"
C_LIGHT  = "#f5f5f5"


# ---------------------------------------------------------------------------
# Miniatura de foto com botão remover
# ---------------------------------------------------------------------------
class FotoSlot(QFrame):
    """Slot individual: vazio → '+' clicável; preenchido → thumbnail clicável (substitui) + botão ✕."""
    clicked = pyqtSignal()   # clique no slot (add ou replace)
    removed = pyqtSignal()   # clique no ✕

    def __init__(self, foto: dict = None, parent=None):
        super().__init__(parent)
        self.foto = foto
        self.setFixedSize(96, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()

    def set_foto(self, foto: dict):
        """Atualiza o slot com nova foto (ou None) sem recriar o widget."""
        self.foto = foto
        self._build()

    def _build(self):
        # Remove widgets filhos antigos
        old = self.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
        for w in old:
            w.hide()
            w.deleteLater()
        if self.layout():
            QWidget().setLayout(self.layout())   # desvincula o layout antigo

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)

        has_foto = bool(self.foto and os.path.exists(self.foto.get("caminho", "")))

        if has_foto:
            self.setStyleSheet(
                "FotoSlot { border: 2px solid #e8820c; border-radius: 6px; background: #fff; }"
                "FotoSlot:hover { border-color: #c06000; }"
            )
            pix_lbl = QLabel()
            pix_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix_lbl.setFixedHeight(72)
            pix = QPixmap(self.foto["caminho"]).scaled(
                86, 68, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            pix_lbl.setPixmap(pix)
            pix_lbl.setStyleSheet("background: transparent; border: none;")

            btn_del = QPushButton("✕ Remover")
            btn_del.setFixedHeight(20)
            btn_del.setStyleSheet(
                "background: #b91c1c; color: #fff; border: none; border-radius: 3px;"
                "font-size: 9px; font-weight: bold;"
            )
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(self.removed.emit)

            layout.addWidget(pix_lbl)
            layout.addWidget(btn_del)
        else:
            self.setStyleSheet(
                "FotoSlot { border: 2px dashed #cccccc; border-radius: 6px; background: #fafafa; }"
                "FotoSlot:hover { border-color: #e8820c; background: #fff8f0; }"
            )
            icon_lbl = QLabel("📷")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet("font-size: 22px; background: transparent; border: none;")
            plus_lbl = QLabel("+ foto")
            plus_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            plus_lbl.setStyleSheet(
                f"color: {C_ORANGE}; font-size: 10px; font-weight: bold;"
                "background: transparent; border: none;"
            )
            layout.addWidget(icon_lbl)
            layout.addWidget(plus_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# Card de avaliação de um item (com fotos integradas)
# ---------------------------------------------------------------------------
class ItemCard(QFrame):
    changed = pyqtSignal()

    def __init__(self, item: dict, avaliacao: dict = None, painel_id: int = None, parent=None):
        super().__init__(parent)
        self.item = item
        self.item_num = item["numero"]
        self.painel_id = painel_id
        self._fotos = []
        self.setObjectName("card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._build_ui(avaliacao or {})
        if painel_id:
            self._load_fotos()

    def _build_ui(self, aval: dict):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Cabeçalho do item ──────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            f"background: {C_BLACK}; border-radius: 8px 8px 0 0;"
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 8, 14, 8)

        num_lbl = QLabel(f"  Item {self.item_num:02d}")
        num_lbl.setStyleSheet(
            f"color: {C_ORANGE}; font-weight: bold; font-size: 14px;"
            "background: transparent; padding: 2px 6px;"
        )
        h_layout.addWidget(num_lbl)

        self.score_lbl = QLabel("—")
        self.score_lbl.setStyleSheet(
            "color: #ffffff; font-size: 12px; font-weight: bold; background: transparent;"
        )
        h_layout.addStretch()
        h_layout.addWidget(self.score_lbl)
        layout.addWidget(header)

        # ── Corpo ──────────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: #ffffff; border-radius: 0 0 8px 8px;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 10, 14, 12)
        body_layout.setSpacing(8)

        # Questão
        questao_lbl = QLabel(self.item["questao"])
        questao_lbl.setWordWrap(True)
        questao_lbl.setStyleSheet(
            f"font-size: 13px; color: {COLORS['text_primary']}; font-weight: 500;"
        )
        body_layout.addWidget(questao_lbl)

        # Justificativa (tooltip)
        just = self.item.get("justificativa", "")
        if just:
            just_preview = just.split("\n")[0][:110]
            nr_lbl = QLabel(f"📖  {just_preview}{'...' if len(just) > 110 else ''}")
            nr_lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 10px; font-style: italic;"
            )
            nr_lbl.setWordWrap(True)
            nr_lbl.setToolTip(just)
            body_layout.addWidget(nr_lbl)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {COLORS['border_light']}; max-height: 1px;")
        body_layout.addWidget(sep)

        # ── Opções de resposta ─────────────────────────────────────────────
        self.btn_group = QButtonGroup(self)
        self._opcao_ids  = {}
        self._opcao_pesos = {}

        opcoes_layout = QGridLayout()
        opcoes_layout.setSpacing(5)
        cols = 2
        for i, opc in enumerate(self.item["opcoes"]):
            rb = QRadioButton(opc["descricao"])
            rb.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 12px; padding: 6px 10px;
                    border: 1px solid {COLORS['border']};
                    border-radius: 5px; background: {COLORS['content_bg']};
                }}
                QRadioButton:hover {{
                    background: {COLORS['table_hover']};
                    border-color: {C_ORANGE};
                }}
                QRadioButton:checked {{
                    background: #fff3e0; border-color: {C_ORANGE};
                    color: #7a3500; font-weight: bold;
                }}
            """)
            rb.toggled.connect(self._on_option_changed)
            self.btn_group.addButton(rb, i)
            self._opcao_ids[i]   = opc["id"]
            self._opcao_pesos[i] = opc.get("peso")
            opcoes_layout.addWidget(rb, i // cols, i % cols)

        body_layout.addLayout(opcoes_layout)

        # Pré-seleciona resposta existente
        if aval.get("opcao_id"):
            for i, opc in enumerate(self.item["opcoes"]):
                if opc["id"] == aval["opcao_id"]:
                    btn = self.btn_group.button(i)
                    if btn:
                        btn.setChecked(True)
                    break

        # ── Observações + Ação Corretiva ───────────────────────────────────
        obs_row = QHBoxLayout()
        obs_row.setSpacing(10)

        obs_col = QVBoxLayout()
        obs_lbl = QLabel("Observações:")
        obs_lbl.setStyleSheet(
            f"font-size: 11px; color: {COLORS['text_secondary']}; font-weight: 500;"
        )
        self.obs_edit = QTextEdit()
        self.obs_edit.setPlaceholderText("Estado observado no painel...")
        self.obs_edit.setMaximumHeight(62)
        self.obs_edit.setPlainText(aval.get("observacoes", "") or "")
        obs_col.addWidget(obs_lbl)
        obs_col.addWidget(self.obs_edit)

        ac_col = QVBoxLayout()
        ac_lbl = QLabel("Ação Corretiva:")
        ac_lbl.setStyleSheet(
            f"font-size: 11px; color: {COLORS['text_secondary']}; font-weight: 500;"
        )
        self.ac_edit = QTextEdit()
        self.ac_edit.setPlaceholderText("Ação corretiva recomendada...")
        self.ac_edit.setMaximumHeight(62)
        self.ac_edit.setPlainText(aval.get("acao_corretiva", "") or "")
        ac_col.addWidget(ac_lbl)
        ac_col.addWidget(self.ac_edit)

        obs_row.addLayout(obs_col)
        obs_row.addLayout(ac_col)
        body_layout.addLayout(obs_row)

        # ── Evidências fotográficas integradas (até 4 fotos) ───────────────
        foto_sep = QFrame()
        foto_sep.setFrameShape(QFrame.Shape.HLine)
        foto_sep.setStyleSheet(f"background: {COLORS['border_light']}; max-height: 1px;")
        body_layout.addWidget(foto_sep)

        foto_header = QHBoxLayout()
        foto_lbl = QLabel("📷  Evidências fotográficas (até 4 imagens):")
        foto_lbl.setStyleSheet(
            f"font-size: 11px; color: {COLORS['text_secondary']}; font-weight: 500;"
        )
        foto_header.addWidget(foto_lbl)
        foto_header.addStretch()
        body_layout.addLayout(foto_header)

        # Row de 4 slots
        self._slots_layout = QHBoxLayout()
        self._slots_layout.setSpacing(8)
        self._slots_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._foto_slots = []
        for idx in range(4):
            slot = FotoSlot(parent=self)
            slot.clicked.connect(lambda i=idx: self._on_slot_clicked(i))
            slot.removed.connect(lambda i=idx: self._remove_foto_slot(i))
            self._foto_slots.append(slot)
            self._slots_layout.addWidget(slot)
        self._slots_layout.addStretch()
        body_layout.addLayout(self._slots_layout)

        layout.addWidget(body)

    # ── Gestão de fotos ────────────────────────────────────────────────────
    def _load_fotos(self):
        """Carrega fotos deste item do banco e atualiza os slots."""
        todas = db.listar_fotos(self.painel_id)
        self._fotos = [f for f in todas if f.get("item_numero") == self.item_num]
        for i, slot in enumerate(self._foto_slots):
            slot.set_foto(self._fotos[i] if i < len(self._fotos) else None)

    def _on_slot_clicked(self, idx: int):
        """Clique num slot: abre diálogo de arquivo para adicionar ou substituir."""
        if not self.painel_id:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, f"Selecionar Foto – Item {self.item_num:02d}", "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not path:
            return
        # Se o slot já tinha foto, remove a antiga antes de adicionar
        if idx < len(self._fotos):
            db.excluir_foto(self._fotos[idx]["id"])
        db.adicionar_foto(self.painel_id, self.item_num, path)
        self._load_fotos()

    def _remove_foto_slot(self, idx: int):
        """Remove a foto de um slot pelo índice."""
        if idx < len(self._fotos):
            db.excluir_foto(self._fotos[idx]["id"])
            self._load_fotos()

    # ── Resposta e pontuação ───────────────────────────────────────────────
    def _on_option_changed(self):
        btn = self.btn_group.checkedButton()
        if btn:
            idx = self.btn_group.id(btn)
            peso = self._opcao_pesos.get(idx)
            if peso is None:
                self.score_lbl.setText("Não avaliado")
                self.score_lbl.setStyleSheet(
                    "color: #8a9bb0; font-size: 12px; background: transparent;"
                )
            else:
                pct = int(peso * 100)
                if peso >= 0.75:
                    cor = "#1a7f37"
                elif peso > 0:
                    cor = C_ORANGE
                else:
                    cor = "#b91c1c"
                self.score_lbl.setText(f"Pontuação: {pct}%")
                self.score_lbl.setStyleSheet(
                    f"color: {cor}; font-size: 12px; font-weight: bold; background: transparent;"
                )
        self.changed.emit()

    def get_data(self) -> dict:
        btn = self.btn_group.checkedButton()
        if btn is None:
            return None
        idx = self.btn_group.id(btn)
        return {
            "item_numero":   self.item_num,
            "opcao_id":      self._opcao_ids.get(idx),
            "peso":          self._opcao_pesos.get(idx),
            "observacoes":   self.obs_edit.toPlainText().strip(),
            "acao_corretiva": self.ac_edit.toPlainText().strip(),
        }


# ---------------------------------------------------------------------------
# Widget principal de avaliação
# ---------------------------------------------------------------------------
class PainelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._laudo_id  = None
        self._painel_id = None
        self._item_cards = []
        self._build_ui()

    def set_laudo_painel(self, laudo_id: int, painel_id: int):
        self._laudo_id  = laudo_id
        self._painel_id = painel_id
        self._load_painel()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        placeholder = QLabel("Selecione um painel na tela de Laudos para iniciar a avaliação.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 14px; padding: 60px;"
        )
        self.main_layout.addWidget(placeholder)

    def _load_painel(self):
        # Limpa layout
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._item_cards = []

        painel = db.buscar_painel(self._painel_id)
        if not painel:
            return

        # ── HEADER: preto + laranja ────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setStyleSheet(
            f"background: {C_BLACK}; border-bottom: 3px solid {C_ORANGE};"
        )
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 14, 24, 14)
        header_layout.setSpacing(16)

        # Título e info
        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        title = QLabel(f"Avaliação do Painel:  {painel.get('tag', '—')}")
        title.setStyleSheet(
            "color: #ffffff; font-size: 17px; font-weight: bold; background: transparent;"
        )
        info = QLabel(
            f"Setor: {painel.get('setor','—')}  |  "
            f"Tipo: {painel.get('tipo_painel','—')}  |  "
            f"Laudo ID: {self._laudo_id}"
        )
        info.setStyleSheet("color: #aaaaaa; font-size: 11px; background: transparent;")
        title_col.addWidget(title)
        title_col.addWidget(info)
        header_layout.addLayout(title_col)
        header_layout.addStretch()

        # Nível de aderência – widget preto/laranja limpo
        nivel_frame = QFrame()
        nivel_frame.setStyleSheet(
            f"background: {C_DARK}; border: 2px solid {C_ORANGE};"
            "border-radius: 8px;"
        )
        nivel_frame.setFixedWidth(220)
        nivel_layout = QVBoxLayout(nivel_frame)
        nivel_layout.setContentsMargins(16, 10, 16, 10)
        nivel_layout.setSpacing(4)

        self.nivel_lbl = QLabel("0.0%")
        self.nivel_lbl.setStyleSheet(
            f"color: {C_ORANGE}; font-size: 26px; font-weight: bold; background: transparent;"
        )
        self.nivel_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nivel_cat_lbl = QLabel("Nível de Aderência")
        self.nivel_cat_lbl.setStyleSheet(
            "color: #888888; font-size: 10px; background: transparent;"
        )
        self.nivel_cat_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background: #444; border-radius: 4px; border: none; }}"
            f"QProgressBar::chunk {{ background: {C_ORANGE}; border-radius: 4px; }}"
        )

        nivel_layout.addWidget(self.nivel_lbl)
        nivel_layout.addWidget(self.nivel_cat_lbl)
        nivel_layout.addWidget(self.progress_bar)
        header_layout.addWidget(nivel_frame)

        # Botão salvar
        btn_save = QPushButton("Salvar Avaliação")
        btn_save.setObjectName("btn_accent")
        btn_save.setFixedHeight(44)
        btn_save.clicked.connect(self._save)
        header_layout.addWidget(btn_save)

        self.main_layout.addWidget(header_frame)

        # ── CHECKLIST (sem aba de fotos separada) ─────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['content_bg']};")
        cl_layout = QVBoxLayout(container)
        cl_layout.setContentsMargins(20, 20, 20, 20)
        cl_layout.setSpacing(14)

        items     = db.listar_checklist_items()
        avaliacoes = db.listar_avaliacoes(self._painel_id)

        for item in items:
            aval = avaliacoes.get(item["numero"], {})
            card = ItemCard(item, aval, painel_id=self._painel_id, parent=container)
            card.changed.connect(self._update_nivel)
            self._item_cards.append(card)
            cl_layout.addWidget(card)

        cl_layout.addStretch()
        scroll.setWidget(container)
        self.main_layout.addWidget(scroll)

        self._update_nivel()

    def _update_nivel(self):
        scores = [
            d["peso"] for card in self._item_cards
            if (d := card.get_data()) and d.get("peso") is not None
        ]
        nivel = sum(scores) / len(scores) if scores else 0.0
        pct = nivel * 100

        self.nivel_lbl.setText(f"{pct:.1f}%")
        cat = nivel_label(nivel)
        self.nivel_cat_lbl.setText(f"Nível: {cat}")
        self.progress_bar.setValue(int(pct))

        if nivel >= 0.85:
            chunk_color = "#1a7f37"
        elif nivel >= 0.60:
            chunk_color = C_ORANGE
        else:
            chunk_color = "#b91c1c"

        self.nivel_lbl.setStyleSheet(
            f"color: {chunk_color}; font-size: 26px; font-weight: bold; background: transparent;"
        )
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background: #444; border-radius: 4px; border: none; }}"
            f"QProgressBar::chunk {{ background: {chunk_color}; border-radius: 4px; }}"
        )

    def _save(self):
        if not self._painel_id:
            return
        saved = 0
        for card in self._item_cards:
            data = card.get_data()
            if data:
                db.salvar_avaliacao(
                    self._painel_id,
                    data["item_numero"],
                    data["opcao_id"],
                    data["peso"],
                    data["observacoes"],
                    data["acao_corretiva"],
                )
                saved += 1

        nivel = db.atualizar_nivel_aderencia(self._painel_id)
        self.nivel_lbl.setText(f"{nivel*100:.1f}%")
        QMessageBox.information(
            self, "Avaliação Salva",
            f"{saved} itens salvos com sucesso!\n\n"
            f"Nível de Aderência: {nivel*100:.1f}%  ({nivel_label(nivel)})"
        )
