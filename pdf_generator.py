"""
GerLauNR10 - Gerador de Relatorio PDF (ReportLab)
Estrutura do laudo conforme metodologia Engelogic
"""
import os
import io
from pathlib import Path
from datetime import datetime
from typing import Callable

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, KeepTogether, HRFlowable, FrameBreak
)
from reportlab.platypus.flowables import Flowable
from reportlab import platypus
from reportlab.pdfgen import canvas

BASE_DIR = Path(__file__).parent

# ── Paleta ────────────────────────────────────────────────────────────────────
W, H     = A4
MARGIN_L = 1.5 * cm
MARGIN_R = 1.5 * cm
MARGIN_T = 2.0 * cm
MARGIN_B = 2.0 * cm

C_NAVY    = HexColor("#1a1a1a")
C_AMBER   = HexColor("#e8820c")
C_WHITE   = HexColor("#ffffff")
C_SUCCESS = HexColor("#1a7f37")
C_WARNING = HexColor("#9a6700")
C_DANGER  = HexColor("#b91c1c")
C_MUTED   = HexColor("#666666")
C_DARK    = HexColor("#2a2a2a")


def nivel_cor(nivel):
    """Retorna HexColor para o nivel de aderencia."""
    if nivel >= 0.85: return C_SUCCESS
    elif nivel >= 0.60: return C_WARNING
    return C_DANGER


def nivel_label(nivel) -> str:
    if nivel >= 0.85: return "BOM"
    elif nivel >= 0.60: return "REGULAR"
    return "CRITICO"


def _fmt_date(d):
    """Converte yyyy-mm-dd para dd/mm/yyyy. Retorna d inalterado se falhar."""
    if not d:
        return "—"
    s = str(d).strip()
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return s


def _build_styles():
    base = getSampleStyleSheet()
    s = {}
    # ── CAPA ──────────────────────────────────────────────────────────────────
    s["titulo_capa"] = ParagraphStyle("titulo_capa", parent=base["Normal"],
        fontSize=26, leading=32, textColor=C_NAVY, fontName="Helvetica-Bold",
        alignment=TA_CENTER)
    s["subtitulo_capa"] = ParagraphStyle("subtitulo_capa", parent=base["Normal"],
        fontSize=14, leading=18, textColor=HexColor("#2d3748"), fontName="Helvetica",
        alignment=TA_CENTER)
    s["cliente_capa"] = ParagraphStyle("cliente_capa", parent=base["Normal"],
        fontSize=16, leading=22, textColor=C_NAVY, fontName="Helvetica-Bold",
        alignment=TA_CENTER)
    # ── SECOES ────────────────────────────────────────────────────────────────
    s["secao"] = ParagraphStyle("secao", parent=base["Normal"],
        fontSize=13, leading=17, textColor=C_NAVY, fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=6, borderPad=4)
    s["subsecao"] = ParagraphStyle("subsecao", parent=base["Normal"],
        fontSize=11, leading=15, textColor=C_AMBER, fontName="Helvetica-Bold",
        spaceBefore=8, spaceAfter=4)
    # ── CORPO ────────────────────────────────────────────────────────────────
    s["body"] = ParagraphStyle("body", parent=base["Normal"],
        fontSize=10, leading=15, textColor=HexColor("#1a2332"),
        fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=6)
    s["body_bold"] = ParagraphStyle("body_bold", parent=base["Normal"],
        fontSize=10, leading=14, textColor=HexColor("#1a2332"), fontName="Helvetica-Bold")
    s["label"] = ParagraphStyle("label", parent=base["Normal"],
        fontSize=9, leading=12, textColor=C_MUTED, fontName="Helvetica-Bold")
    s["value"] = ParagraphStyle("value", parent=base["Normal"],
        fontSize=10, leading=14, textColor=HexColor("#1a2332"), fontName="Helvetica")
    s["center"] = ParagraphStyle("center", parent=base["Normal"],
        fontSize=10, leading=14, textColor=HexColor("#1a2332"), fontName="Helvetica",
        alignment=TA_CENTER)
    s["center_white"] = ParagraphStyle("center_white", parent=base["Normal"],
        fontSize=10, leading=14, textColor=C_WHITE, fontName="Helvetica",
        alignment=TA_CENTER)
    s["white_bold"] = ParagraphStyle("white_bold", parent=base["Normal"],
        fontSize=11, leading=14, textColor=C_WHITE, fontName="Helvetica-Bold",
        alignment=TA_CENTER)
    # ── QUESTOES ─────────────────────────────────────────────────────────────
    s["questao"] = ParagraphStyle("questao", parent=base["Normal"],
        fontSize=10, leading=14, textColor=HexColor("#1a2332"),
        fontName="Helvetica-Bold", spaceAfter=4)
    s["resposta_sim"] = ParagraphStyle("resposta_sim", parent=base["Normal"],
        fontSize=10, leading=13, textColor=C_SUCCESS, fontName="Helvetica-Bold")
    s["resposta_parcial"] = ParagraphStyle("resposta_parcial", parent=base["Normal"],
        fontSize=10, leading=13, textColor=C_WARNING, fontName="Helvetica-Bold")
    s["resposta_nao"] = ParagraphStyle("resposta_nao", parent=base["Normal"],
        fontSize=10, leading=13, textColor=C_DANGER, fontName="Helvetica-Bold")
    s["obs"] = ParagraphStyle("obs", parent=base["Normal"],
        fontSize=9, leading=13, textColor=C_MUTED, fontName="Helvetica-Oblique")
    # ── TABELAS ──────────────────────────────────────────────────────────────
    s["cell"] = ParagraphStyle("cell", parent=base["Normal"],
        fontSize=9, leading=12, textColor=HexColor("#1a2332"), fontName="Helvetica",
        spaceBefore=0, spaceAfter=0)
    s["cell_center"] = ParagraphStyle("cell_center", parent=base["Normal"],
        fontSize=9, leading=12, textColor=HexColor("#1a2332"), fontName="Helvetica",
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=0)
    s["cell_bold"] = ParagraphStyle("cell_bold", parent=base["Normal"],
        fontSize=9, leading=12, textColor=HexColor("#1a2332"), fontName="Helvetica-Bold",
        spaceBefore=0, spaceAfter=0)
    s["cell_bold_white"] = ParagraphStyle("cell_bold_white", parent=base["Normal"],
        fontSize=9, leading=12, textColor=C_WHITE, fontName="Helvetica-Bold",
        spaceBefore=0, spaceAfter=0)
    s["cell_success"] = ParagraphStyle("cell_success", parent=base["Normal"],
        fontSize=9, leading=12, textColor=C_SUCCESS, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=0)
    s["cell_warning"] = ParagraphStyle("cell_warning", parent=base["Normal"],
        fontSize=9, leading=12, textColor=C_WARNING, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=0)
    s["cell_danger"] = ParagraphStyle("cell_danger", parent=base["Normal"],
        fontSize=9, leading=12, textColor=C_DANGER, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=0)
    return s


# ── Cabecalho/rodape das paginas ──────────────────────────────────────────────
class LaudoCanvas(canvas.Canvas):
    def __init__(self, *args, laudo_info=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._laudo_info = laudo_info or {}

    def showPage(self):
        self._draw_header_footer()
        super().showPage()

    def _draw_header_footer(self):
        self.saveState()
        # Header
        self.setFillColor(C_NAVY)
        self.rect(0, H - 1.2 * cm, W, 1.2 * cm, stroke=0, fill=1)
        self.setFillColor(C_AMBER)
        self.rect(0, H - 1.3 * cm, W, 0.1 * cm, stroke=0, fill=1)
        self.setFillColor(C_WHITE)
        self.setFont("Helvetica-Bold", 9)
        titulo = self._laudo_info.get("titulo", "Laudo NR-10")[:60]
        self.drawString(MARGIN_L, H - 0.85 * cm, titulo)
        self.setFont("Helvetica", 8)
        cliente = self._laudo_info.get("cliente", "")[:50]
        self.drawRightString(W - MARGIN_R, H - 0.85 * cm, cliente)
        # Footer
        self.setFillColor(C_NAVY)
        self.rect(0, 0, W, 0.9 * cm, stroke=0, fill=1)
        self.setFillColor(C_WHITE)
        self.setFont("Helvetica", 8)
        self.drawString(MARGIN_L, 0.32 * cm,
                        "ENGELOGIC Automacao e Controle Industrial  |  www.engelogic.com.br")
        self.drawRightString(W - MARGIN_R, 0.32 * cm, "Pagina %d" % self._pageNumber)
        self.restoreState()


class SectionHeader(Flowable):
    def __init__(self, numero, titulo, width=None):
        super().__init__()
        self.numero = numero
        self.titulo = titulo
        self.width = width or (W - MARGIN_L - MARGIN_R)
        self.height = 0.75 * cm

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(C_NAVY)
        c.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        c.setFillColor(C_AMBER)
        c.rect(0, 0, 0.25 * cm, self.height, stroke=0, fill=1)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(0.55 * cm, 0.22 * cm, "%s  %s" % (self.numero, self.titulo))
        c.restoreState()

    def wrap(self, availW, availH):
        return self.width, self.height + 0.25 * cm


class NivelBadge(Flowable):
    def __init__(self, nivel, tag="", avail_w=None):
        super().__init__()
        self.nivel = float(nivel or 0.0)
        self.tag = tag
        self.width = avail_w or (W - MARGIN_L - MARGIN_R)
        self.height = 1.0 * cm

    def draw(self):
        c = self.canv
        c.saveState()
        cor = nivel_cor(self.nivel)
        pct = self.nivel * 100
        lbl = nivel_label(self.nivel)
        w, h = self.width, self.height
        c.setFillColor(HexColor("#f5f5f5"))
        c.rect(0, 0, w, h, stroke=0, fill=1)
        bar_w = w * self.nivel
        c.setFillColor(cor)
        c.rect(0, 0, bar_w, h * 0.35, stroke=0, fill=1)
        c.setFillColor(C_NAVY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(0.3 * cm, 0.55 * cm, "Nivel de Aderencia: %.1f%%  [%s]" % (pct, lbl))
        if self.tag:
            c.setFont("Helvetica", 8)
            c.setFillColor(C_MUTED)
            c.drawRightString(w - 0.3 * cm, 0.55 * cm, "Painel: %s" % self.tag)
        c.restoreState()

    def wrap(self, availW, availH):
        return self.width, self.height + 0.15 * cm


class CameraIcon(Flowable):
    """Icone vetorial de maquina fotografica, usado como placeholder quando nao ha foto."""
    def __init__(self, width, height):
        super().__init__()
        self.width = float(width)
        self.height = float(height)

    def draw(self):
        c = self.canv
        c.saveState()
        w, h = self.width, self.height
        side = min(w, h) * 0.6
        cx, cy = w / 2.0, h / 2.0
        cor = HexColor("#c8d0d8")
        body_w, body_h = side, side * 0.68
        bx, by = cx - body_w / 2.0, cy - body_h / 2.0
        c.setFillColor(cor)
        c.roundRect(bx, by, body_w, body_h, body_h * 0.12, stroke=0, fill=1)
        flash_w, flash_h = body_w * 0.32, body_h * 0.22
        c.roundRect(bx + body_w * 0.12, by + body_h - flash_h * 0.5,
                    flash_w, flash_h, flash_h * 0.2, stroke=0, fill=1)
        c.setFillColor(HexColor("#eef1f4"))
        lens_r = body_h * 0.32
        c.circle(cx, by + body_h * 0.46, lens_r, stroke=0, fill=1)
        c.setFillColor(cor)
        c.circle(cx, by + body_h * 0.46, lens_r * 0.55, stroke=0, fill=1)
        c.restoreState()

    def wrap(self, availW, availH):
        return self.width, self.height


def gerar_laudo_pdf(
    laudo_id: int,
    output_path: str,
    opcoes: dict,
    progress_cb: Callable[[int, str], None] = None,
):
    def prog(p, msg):
        if progress_cb:
            progress_cb(p, msg)

    import sys as _sys
    _sys.path.insert(0, str(BASE_DIR))
    import database as db

    prog(2, "Carregando dados do laudo...")
    laudo       = db.buscar_laudo(laudo_id)
    if not laudo:
        raise ValueError("Laudo ID %d nao encontrado" % laudo_id)
    cliente     = db.buscar_cliente(laudo["cliente_id"]) if laudo.get("cliente_id") else {}
    paineis     = db.listar_paineis(laudo_id)
    checklist_items = db.listar_checklist_items()
    estatisticas    = db.estatisticas_laudo(laudo_id)

    styles   = _build_styles()

    # Largura util (igual a largura das barras de secao, para alinhamento uniforme)
    _AW = W - MARGIN_L - MARGIN_R

    _canvas_maker = lambda *a, **kw: LaudoCanvas(*a, laudo_info=laudo, **kw)

    class _LaudoDocTemplate(BaseDocTemplate):
        """BaseDocTemplate + Frame com padding zero: SimpleDocTemplate usa por
        padrao 6pt de padding interno no frame, o que desalinha Tables (que
        ignoram esse padding e ficam rente a margem) em relacao a Flowables
        customizados como SectionHeader (que respeitam o padding) -- dai o
        desalinhamento entre barras e tabelas. Com padding zero, ambos ficam
        exatamente na margem.

        Tambem registra, em toc_registry, a pagina onde cada flowable marcado
        com ._toc_key foi desenhado -- usado para preencher o Sumario (2
        passadas: a 1a descobre a paginacao, a 2a gera o PDF final ja com o
        Sumario completo).
        """
        def afterFlowable(self, flowable):
            key = getattr(flowable, "_toc_key", None)
            if key is not None:
                self.toc_registry[key] = self.page

    def _make_doc(dest):
        d = _LaudoDocTemplate(
            dest, pagesize=A4,
            leftMargin=MARGIN_L, rightMargin=MARGIN_R,
            topMargin=MARGIN_T,  bottomMargin=MARGIN_B,
        )
        d.toc_registry = {}
        frame = Frame(MARGIN_L, MARGIN_B, _AW, H - MARGIN_T - MARGIN_B,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                      id="normal")
        d.addPageTemplates([PageTemplate(id="normal", frames=[frame])])
        return d

    def _build(toc_pages):
        story = []

        def add_spacer(cm_h=0.3):
            story.append(Spacer(1, cm_h * cm))

        def add_section(num, title):
            sh = SectionHeader(num, title, _AW)
            sh._toc_key = num
            story.append(sh)

        def add_subsection(num, title, style_key="subsecao"):
            p = Paragraph("%s  %s" % (num, title), styles[style_key])
            p._toc_key = num
            story.append(p)
            return p

        def _toc_pagenum(key):
            if not toc_pages:
                return ""
            pg = toc_pages.get(key)
            return str(pg) if pg else ""

        def _lbl(t): return Paragraph(t, styles["label"])
        def _val(t): return Paragraph(str(t) if t else "—", styles["value"])

        # ── CAPA ─────────────────────────────────────────────────────────────────
        if opcoes.get("capa", True):
            prog(5, "Gerando capa...")
            story.append(Spacer(1, 2 * cm))

            # Logo Engelogic
            logo_path = str(BASE_DIR / "resources" / "logo_engelogic.png")
            if os.path.exists(logo_path):
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(logo_path) as _pi:
                        lw, lh = _pi.size
                    r = lh / lw if lw else 1.0
                    max_w, max_h = 8.0 * cm, 3.2 * cm
                    if max_w * r <= max_h:
                        fw, fh = max_w, max_w * r
                    else:
                        fh, fw = max_h, max_h / r
                    logo_img = Image(logo_path, width=fw, height=fh)
                    logo_img.hAlign = "CENTER"
                    story.append(logo_img)
                except Exception:
                    pass
            add_spacer(1.6)  # espacamento duplo (logo -> titulo)

            # Titulo
            story.append(Paragraph("LAUDO TECNICO", styles["titulo_capa"]))
            story.append(Paragraph("SEGURANCA ELETRICA – NR-10", styles["subtitulo_capa"]))
            add_spacer(1.2)  # espacamento duplo (subtitulo -> faixa)

            # Faixa laranja com titulo do laudo
            faixa = Table([[ Paragraph(laudo.get("titulo", "Inspecao de Paineis Eletricos"),
                ParagraphStyle("_ft", parent=styles["white_bold"], fontSize=18, leading=24))
            ]], colWidths=[_AW])
            faixa.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), C_AMBER),
                ("TOPPADDING",    (0,0),(-1,-1), 14),
                ("BOTTOMPADDING", (0,0),(-1,-1), 14),
                ("LEFTPADDING",   (0,0),(-1,-1), 20),
            ]))
            story.append(faixa)
            add_spacer(1.0)  # espacamento duplo (faixa -> cliente)

            # Cliente
            if cliente:
                story.append(Paragraph(cliente.get("razao_social", ""), styles["cliente_capa"]))
                cnpj = cliente.get("cnpj", "")
                if cnpj:
                    story.append(Paragraph("CNPJ: %s" % cnpj,
                        ParagraphStyle("_cc", parent=styles["subtitulo_capa"], fontSize=11)))
            add_spacer(0.8)  # espacamento duplo (cliente/cnpj -> logo do cliente)

            # Logo do cliente
            cli_logo = cliente.get("logo_path", "") if cliente else ""
            if cli_logo and os.path.exists(cli_logo):
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(cli_logo) as _pi:
                        lw, lh = _pi.size
                    r = lh / lw if lw else 1.0
                    max_w, max_h = 5.0 * cm, 2.5 * cm
                    if max_w * r <= max_h:
                        fw, fh = max_w, max_w * r
                    else:
                        fh, fw = max_h, max_h / r
                    cli_img = Image(cli_logo, width=fw, height=fh)
                    cli_img.hAlign = "CENTER"
                    story.append(cli_img)
                except Exception:
                    pass
            add_spacer(1.2)  # espacamento duplo (logo do cliente -> periodo)

            # Periodo e data em formato brasileiro
            p_ini = _fmt_date(laudo.get("periodo_inicio"))
            p_fim = _fmt_date(laudo.get("periodo_fim"))
            periodo_txt = "%s a %s" % (p_ini, p_fim)
            story.append(Paragraph(periodo_txt, styles["center"]))
            story.append(Paragraph(
                "Emitido em: %s" % datetime.now().strftime("%d/%m/%Y"),
                ParagraphStyle("_dt", parent=styles["center"], textColor=C_MUTED)))
            add_spacer(4.5)  # espacamento triplo (emitido em -> rodape ENGELOGIC)

            # Rodape da capa
            razao_eng = "ENGELOGIC Automacao e Controle Industrial"
            eng_info = Table([[
                Paragraph(razao_eng, styles["center_white"]),
            ]], colWidths=[_AW])
            eng_info.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
                ("TOPPADDING",    (0,0),(-1,-1), 10),
                ("BOTTOMPADDING", (0,0),(-1,-1), 10),
                ("TEXTCOLOR",     (0,0),(-1,-1), C_WHITE),
            ]))
            story.append(eng_info)
            story.append(PageBreak())

        # ── INDICE ────────────────────────────────────────────────────────────────
        if opcoes.get("indice", True):
            prog(8, "Gerando indice...")
            add_section("", "SUMARIO")
            add_spacer(0.3)
            secoes = [
                ("1.",  "Identificacao", 0),
                ("1.1", "Empresa Contratante", 1),
                ("1.2", "Responsavel Tecnico pela Elaboracao", 1),
                ("1.3", "Fornecedores de Informacoes", 1),
                ("2.",  "Documento ART", 0),
                ("3.",  "Resumo Tecnico da Norma NR-10", 0),
                ("3.1", "Definicao e Objetivo da Norma", 1),
                ("3.2", "Responsaveis pela Aplicacao", 1),
                ("3.3", "Penalidades Legais pelo Descumprimento", 1),
                ("3.4", "Importancia da Conformidade", 1),
                ("3.5", "Suporte Tecnico", 1),
                ("4.",  "Criterios de Classificacao", 0),
                ("5.",  "Metodologia de Avaliacao", 0),
                ("6.",  "Avaliacoes Realizadas", 0),
                ("6.1", "Situacao Geral dos Paineis", 1),
                ("7.",  "Estratificacao dos Dados – Resultados Estatisticos", 0),
                ("7.1", "Avaliacao de Conformidades", 1),
                ("7.2", "Resumo Estatistico por Item", 1),
                ("8.",  "Conclusoes e Recomendacoes", 0),
                ("8.1", "Conclusao Tecnica", 1),
                ("8.2", "Recomendacoes Tecnicas", 1),
                ("8.3", "Plano de Acao – Prioridades", 1),
                ("8.4", "Plano de Acao Individual por Painel", 1),
            ]
            toc_data = [[Paragraph("<b>Secao</b>", styles["cell_bold_white"]),
                         Paragraph("<b>Descricao</b>", styles["cell_bold_white"]),
                         Paragraph("<b>Pag.</b>", styles["cell_bold_white"])]]
            for num, desc, level in secoes:
                desc_style = styles["cell_bold"] if level == 0 else styles["cell"]
                desc_txt = ("&nbsp;&nbsp;&nbsp;&nbsp;" * level) + desc
                toc_data.append([Paragraph(num, styles["cell_center"]),
                                  Paragraph(desc_txt, desc_style),
                                  Paragraph(_toc_pagenum(num), styles["cell_center"])])
            toc = Table(toc_data, colWidths=[1.8*cm, _AW - 1.8*cm - 1.8*cm, 1.8*cm])
            toc.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,0), C_NAVY),
                ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, HexColor("#f8fafc")]),
                ("GRID",          (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
                ("ALIGN",         (0,0),(0,-1), "CENTER"),
                ("ALIGN",         (2,0),(2,-1), "CENTER"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0,0),(-1,-1), 5),
                ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                ("LEFTPADDING",   (1,0),(1,-1), 8),
            ]))
            story.append(toc)

        # ── IDENTIFICACAO ────────────────────────────────────────────────────────
        if opcoes.get("identificacao", True):
            prog(15, "Gerando secao de identificacao...")
            story.append(PageBreak())
            add_section("1.", "IDENTIFICACAO")
            add_spacer(0.3)

            # Cliente
            add_subsection("1.1", "Empresa Contratante")
            cli_data = [
                [_lbl("Razão Social:"),       _val(cliente.get("razao_social", "—"))],
                [_lbl("CNPJ:"),               _val(cliente.get("cnpj", "—"))],
                [_lbl("Filial/Unidade:"),     _val(cliente.get("filial", "—"))],
                [_lbl("Endereço:"),           _val(cliente.get("endereco", "—"))],
                [_lbl("CEP:"),                _val(cliente.get("cep", "—"))],
                [_lbl("Cidade/UF:"),          _val("%s / %s" % (cliente.get("cidade",""), cliente.get("estado","")))],
                [_lbl("Telefone:"),           _val(cliente.get("telefone", "—"))],
            ]
            cli_t = Table(cli_data, colWidths=[3.5*cm, _AW - 3.5*cm])
            cli_t.setStyle(TableStyle([
                ("ROWBACKGROUNDS", (0,0),(-1,-1), [C_WHITE, HexColor("#f8fafc")]),
                ("GRID",           (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
                ("VALIGN",         (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING",     (0,0),(-1,-1), 5),
                ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
                ("LEFTPADDING",    (0,0),(-1,-1), 8),
            ]))
            story.append(cli_t)
            add_spacer(0.4)

            # Profissionais
            profissionais = db.profissionais_do_laudo(laudo_id)
            if profissionais:
                add_subsection("1.2", "Responsável Técnico pela Elaboração")
                for prof in profissionais:
                    prof_data = [
                        [_lbl("Nome:"),         _val(prof.get("nome","—"))],
                        [_lbl("Empresa:"),      _val(prof.get("empresa","—"))],
                        [_lbl("Habilitação:"),  _val(prof.get("habilitacao","—"))],
                        [_lbl("CREA:"),         _val(prof.get("crea","—"))],
                        [_lbl("E-mail:"),       _val(prof.get("email","—"))],
                        [_lbl("Telefone:"),     _val(prof.get("telefone","—"))],
                    ]
                    prof_t = Table(prof_data, colWidths=[3.5*cm, _AW - 3.5*cm])
                    prof_t.setStyle(TableStyle([
                        ("ROWBACKGROUNDS", (0,0),(-1,-1), [C_WHITE, HexColor("#f8fafc")]),
                        ("GRID",           (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
                        ("VALIGN",         (0,0),(-1,-1), "MIDDLE"),
                        ("TOPPADDING",     (0,0),(-1,-1), 5),
                        ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
                        ("LEFTPADDING",    (0,0),(-1,-1), 8),
                    ]))
                    story.append(prof_t)
                    add_spacer(0.3)

            # Participantes
            participantes = db.participantes_do_laudo(laudo_id)
            if participantes:
                add_subsection("1.3", "Fornecedores de Informações")
                part_data = [["Nome", "Empresa", "Cargo/Setor", "Contato"]]
                for p in participantes:
                    contato = p.get("email","") or p.get("telefone","") or "—"
                    cargo_setor = "%s  /  %s" % (p.get("cargo",""), p.get("setor","")) if p.get("cargo") else p.get("setor","—")
                    part_data.append([
                        Paragraph(p.get("nome","—"), styles["cell"]),
                        Paragraph(p.get("empresa","—"), styles["cell"]),
                        Paragraph(cargo_setor, styles["cell"]),
                        Paragraph(contato, styles["cell"]),
                    ])
                part_t = Table(part_data, colWidths=[3.5*cm, 3.5*cm, 4.5*cm, _AW-11.5*cm])
                part_t.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0),(-1,0), C_NAVY),
                    ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
                    ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",      (0,0),(-1,-1), 9),
                    ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, HexColor("#f8fafc")]),
                    ("GRID",          (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
                    ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                    ("TOPPADDING",    (0,0),(-1,-1), 5),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                    ("LEFTPADDING",   (0,0),(-1,-1), 6),
                ]))
                story.append(part_t)

        # ── ART ───────────────────────────────────────────────────────────────────
        if opcoes.get("art", True) and laudo.get("art_pdf_path"):
            prog(28, "Inserindo ART...")
            story.append(PageBreak())
            add_section("2.", "DOCUMENTO ART – ANOTACAO DE RESPONSABILIDADE TECNICA")
            add_spacer(0.3)
            art_path = laudo["art_pdf_path"]
            if os.path.exists(art_path):
                try:
                    import fitz  # PyMuPDF
                    art_doc = fitz.open(art_path)
                    _art_max_w = _AW
                    _art_full_h = H - MARGIN_T - MARGIN_B
                    _art_hdr_h = 1.3 * cm  # altura ja ocupada pela barra "2. DOCUMENTO ART" + espaco
                    for page_num in range(len(art_doc)):
                        if page_num > 0:
                            story.append(PageBreak())
                        _art_max_h = (_art_full_h - _art_hdr_h) if page_num == 0 else _art_full_h
                        art_page = art_doc[page_num]
                        pix = art_page.get_pixmap(dpi=150)
                        img_buf = io.BytesIO(pix.tobytes("png"))
                        _art_r = pix.height / pix.width if pix.width else 1.41
                        if _art_max_w * _art_r <= _art_max_h:
                            _art_w, _art_h = _art_max_w, _art_max_w * _art_r
                        else:
                            _art_h, _art_w = _art_max_h, _art_max_h / _art_r
                        art_img = Image(img_buf, width=float(_art_w), height=float(_art_h))
                        # Caixa do tamanho total da pagina util, centralizando a imagem
                        # tanto na horizontal quanto na vertical.
                        art_box = Table([[art_img]], colWidths=[_AW], rowHeights=[_art_max_h])
                        art_box.setStyle(TableStyle([
                            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
                            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                            ("TOPPADDING",    (0,0),(-1,-1), 0),
                            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
                            ("LEFTPADDING",   (0,0),(-1,-1), 0),
                            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
                        ]))
                        story.append(art_box)
                    art_doc.close()
                except Exception as e:
                    story.append(Paragraph("ART nao renderizada: %s" % str(e), styles["obs"]))
            else:
                story.append(Paragraph("Arquivo ART nao encontrado: %s" % art_path, styles["obs"]))

        # ── RESUMO NR-10 ──────────────────────────────────────────────────────────
        if opcoes.get("resumo_nr10", True):
            prog(35, "Gerando resumo tecnico NR-10...")
            story.append(PageBreak())
            add_section("3.", "RESUMO TECNICO DA NORMA REGULAMENTADORA NR-10")
            add_spacer(0.3)

            add_subsection("3.1", "Definicao e Objetivo da Norma")
            story.append(Paragraph(
                "A Norma Regulamentadora NR-10 – Seguranca em Instalacoes e Servicos em Eletricidade, "
                "aprovada pela Portaria MTb n° 3.214/1978 e atualizada pela Portaria n° 598/2004 do "
                "Ministerio do Trabalho e Emprego, estabelece os requisitos e condicoes minimas "
                "objetivando a implementacao de medidas de controle e sistemas preventivos, de forma a "
                "garantir a seguranca e a saude dos trabalhadores que interagem, direta ou indiretamente, "
                "em instalacoes eletricas e servicos com eletricidade.",
                styles["body"]))
            story.append(Paragraph(
                "A norma aplica-se a todas as fases de geracao, transmissao, distribuicao e consumo de "
                "energia eletrica, abrangendo as etapas de projeto, construcao, montagem, operacao, "
                "manutencao, reforma, ampliacao e desmontagem das instalacoes eletricas, bem como "
                "quaisquer trabalhos realizados em suas proximidades. Entre suas principais exigencias "
                "destacam-se: a elaboracao e manutencao atualizada do Prontuario de Instalacoes Eletricas "
                "(PIE) para estabelecimentos com carga instalada superior a 75 kW; a existencia de "
                "esquemas unifilares atualizados; a adocao de medidas de protecao coletiva "
                "(desenergizacao, aterramento, isolacao) e individual (EPIs adequados aos riscos "
                "eletricos); a capacitacao e autorizacao formal dos trabalhadores; e a implementacao de "
                "procedimentos de trabalho documentados.",
                styles["body"]))
            add_spacer(0.2)

            add_subsection("3.2", "Responsaveis pela Aplicacao")
            story.append(Paragraph(
                "A observancia da NR-10 e obrigacao legal do empregador, cabendo a este garantir que as "
                "instalacoes eletricas sob sua responsabilidade atendam aos requisitos normativos e que os "
                "servicos em eletricidade sejam executados exclusivamente por profissionais qualificados, "
                "habilitados, capacitados e formalmente autorizados. A responsabilidade e solidaria entre "
                "contratantes e contratados no que se refere ao cumprimento da norma, conforme item 10.13 "
                "da NR-10. Cabe aos trabalhadores, por sua vez, zelar pela propria seguranca e pela de "
                "terceiros, cumprindo os procedimentos estabelecidos e comunicando situacoes de risco. "
                "A responsabilidade tecnica pelo projeto, execucao e laudos das instalacoes eletricas e "
                "privativa de profissional legalmente habilitado, com registro no Conselho Regional de "
                "Engenharia e Agronomia (CREA).",
                styles["body"]))
            add_spacer(0.2)

            add_subsection("3.3", "Penalidades Legais pelo Descumprimento")
            story.append(Paragraph(
                "O descumprimento da NR-10 sujeita a empresa as penalidades previstas na Lei n° 6.514/1977 "
                "e na CLT (arts. 154 a 201), que incluem autuacoes e multas administrativas aplicadas pela "
                "Auditoria Fiscal do Trabalho, graduadas conforme o porte da empresa, a gravidade da "
                "infracao e a reincidencia. Em situacoes de grave e iminente risco, a fiscalizacao pode "
                "determinar o embargo da obra ou a interdicao do estabelecimento, setor, maquina ou "
                "equipamento, nos termos da NR-3, com paralisacao imediata das atividades. "
                "Adicionalmente, a ocorrencia de acidentes decorrentes da inobservancia das normas de "
                "seguranca pode ensejar responsabilizacao civil (indenizacoes por danos materiais, morais "
                "e esteticos a vitima ou seus dependentes), responsabilizacao criminal do empregador ou "
                "prepostos (art. 132 do Codigo Penal), alem de acoes regressivas do INSS para "
                "ressarcimento de beneficios previdenciarios pagos, conforme art. 120 da Lei "
                "n° 8.213/1991. O descumprimento pode ainda impactar contratos de seguro, certificacoes "
                "e a participacao da empresa em licitacoes e homologacoes junto a clientes.",
                styles["body"]))
            add_spacer(0.2)

            add_subsection("3.4", "Importancia da Conformidade")
            story.append(Paragraph(
                "Para alem das exigencias legais, a conformidade com a NR-10 constitui investimento "
                "direto na preservacao da vida e da integridade fisica dos trabalhadores e na continuidade "
                "operacional da empresa. Acidentes de origem eletrica apresentam elevado potencial de "
                "letalidade e de danos materiais, incluindo incendios, explosoes e paradas nao programadas "
                "de producao. Instalacoes eletricas adequadas, documentadas e mantidas por profissionais "
                "habilitados reduzem significativamente a probabilidade de sinistros, aumentam a "
                "confiabilidade dos sistemas produtivos, reduzem custos com manutencoes corretivas e "
                "passivos trabalhistas, e demonstram o compromisso da organizacao com a seguranca e a "
                "responsabilidade social.",
                styles["body"]))
            add_spacer(0.2)

            add_subsection("3.5", "Suporte Tecnico")
            story.append(Paragraph(
                "A ENGELOGIC AUTOMACAO E CONTROLE INDUSTRIAL LTDA mantem-se a inteira disposicao do "
                "cliente para prestar o suporte tecnico necessario a implementacao das medidas "
                "recomendadas neste laudo, bem como para a execucao das correcoes, adequacoes e "
                "melhorias que se fizerem necessarias nas instalacoes eletricas, contribuindo para o "
                "pleno atendimento aos requisitos da NR-10 e demais normas tecnicas aplicaveis.",
                styles["body"]))

        # ── CRITERIOS ─────────────────────────────────────────────────────────────
        if opcoes.get("criterios", True):
            prog(40, "Gerando criterios de classificacao...")
            story.append(PageBreak())
            add_section("4.", "CRITERIOS DE CLASSIFICACAO")
            add_spacer(0.3)
            story.append(Paragraph(
                "A avaliacao dos paineis eletricos utiliza uma escala de classificacao baseada no "
                "Nivel de Aderencia obtido, conforme tabela abaixo:",
                styles["body"]))
            add_spacer(0.2)
            _crit_hdr = ParagraphStyle("_crithdr", parent=styles["cell_bold_white"],
                                        alignment=TA_CENTER)
            crit_data = [
                [Paragraph("Classificacao", _crit_hdr),
                 Paragraph("Nivel de Aderencia", _crit_hdr),
                 Paragraph("Descricao", _crit_hdr)],
                ["BOM",      ">= 85%",  "Instalacoes em conformidade com a NR-10. Manutencao preventiva recomendada."],
                ["REGULAR",  "60% a 84%", "Nao conformidades identificadas. Plano de acao necessario em medio prazo."],
                ["CRITICO",  "< 60%",   "Risco elevado. Correcoes urgentes e imediatas sao imperativas."],
            ]
            crit_colors = [C_NAVY, C_SUCCESS, C_WARNING, C_DANGER]
            ct = Table(crit_data, colWidths=[3.0*cm, 3.5*cm, _AW - 6.5*cm])
            crit_style = [
                ("BACKGROUND",    (0,0),(-1,0), C_NAVY),
                ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
                ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0),(-1,-1), 9),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [HexColor("#f8fafc"), C_WHITE]),
                ("GRID",          (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
                ("ALIGN",         (0,0),(1,-1), "CENTER"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0,0),(-1,-1), 7),
                ("BOTTOMPADDING", (0,0),(-1,-1), 7),
                ("LEFTPADDING",   (2,0),(2,-1), 8),
            ]
            for row_i, color in enumerate(crit_colors[1:], 1):
                crit_style.append(("BACKGROUND", (0,row_i),(0,row_i), color))
                crit_style.append(("TEXTCOLOR",  (0,row_i),(0,row_i), C_WHITE))
                crit_style.append(("FONTNAME",   (0,row_i),(0,row_i), "Helvetica-Bold"))
            ct.setStyle(TableStyle(crit_style))

            # Recomendacao para o plano de acao por classificacao (mesma pagina do quadro acima)
            rec_title = Paragraph("Recomendacao para o Plano de Acao", styles["subsecao"])
            rec_data = [
                ["CRITICO", "Acao imediata — corrigir a nao conformidade sem demora."],
                ["REGULAR", "Acao em curto/medio prazo — planejar correcao em 30 a 45 dias."],
                ["BOM",     "Acao de conservacao — manutencao preventiva periodica."],
            ]
            rec_colors = [C_DANGER, C_WARNING, C_SUCCESS]
            rt2 = Table(rec_data, colWidths=[3.0*cm, _AW - 3.0*cm])
            rec_style = [
                ("FONTSIZE",      (0,0),(-1,-1), 9),
                ("FONTNAME",      (1,0),(1,-1),  "Helvetica"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                ("ALIGN",         (0,0),(0,-1),  "CENTER"),
                ("TOPPADDING",    (0,0),(-1,-1), 8),
                ("BOTTOMPADDING", (0,0),(-1,-1), 8),
                ("LEFTPADDING",   (1,0),(1,-1),  10),
                ("GRID",          (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
            ]
            for row_i, color in enumerate(rec_colors):
                rec_style.append(("BACKGROUND", (0,row_i),(0,row_i), color))
                rec_style.append(("TEXTCOLOR",  (0,row_i),(0,row_i), C_WHITE))
                rec_style.append(("FONTNAME",   (0,row_i),(0,row_i), "Helvetica-Bold"))
            rt2.setStyle(TableStyle(rec_style))

            story.append(KeepTogether([
                ct, Spacer(1, 0.5 * cm), rec_title, Spacer(1, 0.15 * cm), rt2,
            ]))

        # ── METODOLOGIA ──────────────────────────────────────────────────────────
        if opcoes.get("metodologia", True):
            prog(42, "Gerando metodologia...")
            story.append(PageBreak())
            add_section("5.", "METODOLOGIA DE AVALIACAO")
            add_spacer(0.3)
            story.append(Paragraph(
                "Buscando trazer uma análise quantitativa para este documento, nosso corpo "
                "técnico desenvolveu-se uma metodologia para inspeção e avaliação "
                "dos painéis em que cada painel avaliado recebe uma “nota”, denominada "
                "neste relatório por NÍVEL DE ADERÊNCIA. Tal taxa é composta pela "
                "média obtida durante a análise dos 10 questionamentos, formulados sobre os "
                "principais requisitos da NR-10, assim um painel que atende todos os requisitos da "
                "norma recebe um nível de aderência de 100%, e aquele que não atende, "
                "recebe um percentual proporcional com aquilo que está em concordância com o "
                "solicitado na norma.",
                styles["body"]))
            add_spacer(0.15)
            story.append(Paragraph(
                "Buscando melhor organização dentro do procedimento de avaliação, "
                "cada painel avaliado gera um formulário que contém o resultado da análise "
                "do mesmo. O quadro a seguir apresenta os 10 questionamentos utilizados para "
                "avaliação dos painéis e respostas com seus respectivos pesos para "
                "composição do nível de aderência de cada um dos painéis.",
                styles["body"]))
            add_spacer(0.25)

            # Quadro Item/Questao/Respostas/Peso -- item e questao ocupam uma unica
            # celula mesclada (SPAN) ao longo de todas as respostas daquele item,
            # seguindo a mesma formatacao grafica (navy/branco/faixas) do restante
            # do laudo.
            _meto_cell = ParagraphStyle("_metocell", parent=styles["cell"], alignment=TA_LEFT)
            _meto_item = ParagraphStyle("_metoitem", parent=styles["cell_bold"],
                                         alignment=TA_CENTER)
            chk_data = [["Item", "Questao", "Respostas", "Peso"]]
            _meto_spans = []
            _row = 1
            for idx_it, it in enumerate(checklist_items):
                opcoes_it = it["opcoes"]
                n_op = len(opcoes_it) or 1
                for i, opc in enumerate(opcoes_it):
                    peso = opc.get("peso")
                    peso_txt = "N/A" if peso is None else "%.0f%%" % (peso * 100)
                    if i == 0:
                        chk_data.append([
                            Paragraph(str(it["numero"]), _meto_item),
                            Paragraph(it["questao"], _meto_cell),
                            Paragraph(opc.get("descricao", "—"), _meto_cell),
                            peso_txt,
                        ])
                    else:
                        chk_data.append(["", "", Paragraph(opc.get("descricao", "—"), _meto_cell), peso_txt])
                if n_op > 1:
                    _meto_spans.append((_row, _row + n_op - 1))
                _row += n_op

            _meto_w_item = 1.3 * cm
            _meto_w_peso = 2.0 * cm
            _meto_w_resto = _AW - _meto_w_item - _meto_w_peso
            chk_t = Table(
                chk_data,
                colWidths=[_meto_w_item, _meto_w_resto * 0.5, _meto_w_resto * 0.5, _meto_w_peso],
                repeatRows=1,
            )
            chk_style = [
                ("BACKGROUND",    (0,0),(-1,0), C_NAVY),
                ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
                ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0),(-1,-1), 9),
                ("GRID",          (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
                ("ALIGN",         (0,0),(0,-1), "CENTER"),
                ("ALIGN",         (3,0),(3,-1), "CENTER"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0,0),(-1,-1), 5),
                ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                ("LEFTPADDING",   (1,0),(2,-1), 6),
            ]
            for span_i, (r0, r1) in enumerate(_meto_spans):
                chk_style.append(("SPAN", (0, r0), (0, r1)))
                chk_style.append(("SPAN", (1, r0), (1, r1)))
                shade = HexColor("#f8fafc") if span_i % 2 == 0 else C_WHITE
                chk_style.append(("BACKGROUND", (0, r0), (-1, r1), shade))
            chk_t.setStyle(TableStyle(chk_style))
            story.append(chk_t)
            add_spacer(0.3)

            story.append(Paragraph(
                "Deste modo, a composição dos “pesos” individuais obtidos em nossa "
                "avaliação de cada painel compõe o valor global que identifica de forma "
                "sistemática ao quanto o painel está em acordo com as diretrizes de "
                "segurança previstas na norma.",
                styles["body"]))
            add_spacer(0.15)
            story.append(Paragraph(
                "Esta metodologia foi desenvolvida por nossos engenheiros com expertise comprovada "
                "e aponta indicadores reais e confiáveis para tomada de decisão segura de "
                "nossos clientes.",
                styles["body"]))


        # ── RESUMO AVALIACOES ────────────────────────────────────────────────────
        if opcoes.get("resumo", True) and paineis:
            prog(45, "Gerando resumo das avaliacoes...")
            story.append(PageBreak())
            add_section("6.", "RESUMO DAS AVALIACOES")
            add_spacer(0.3)
            story.append(Paragraph(
                "Apresenta-se a seguir um resumo da avaliacao realizada nos paineis existentes "
                "na planta industrial, com o nivel de aderencia de cada painel e os detalhes "
                "de cada item avaliado.",
                styles["body"]))
            add_spacer(0.2)
            add_subsection("6.1", "Situacao Geral dos Paineis")

            st_data = [["Tag", "Setor", "Tipo", "Data", "Nivel"]]
            for p in paineis:
                nv = float(p.get("nivel_aderencia") or 0.0)
                nv_s = "%.1f%%" % (nv * 100)
                st_data.append([
                    Paragraph(p.get("tag", "—"), styles["cell_bold"]),
                    Paragraph(p.get("setor", "—"), styles["cell"]),
                    Paragraph(p.get("tipo_painel", "—"), styles["cell"]),
                    Paragraph(_fmt_date(p.get("data_avaliacao")), styles["cell_center"]),
                    Paragraph(nv_s + " " + nivel_label(nv),
                        styles["cell_success"] if nv >= 0.85
                        else styles["cell_warning"] if nv >= 0.60
                        else styles["cell_danger"]),
                ])
            st = Table(st_data, colWidths=[2.0*cm, 4.0*cm, 4.5*cm, 2.5*cm, _AW - 13*cm])
            st.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,0), C_NAVY),
                ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
                ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0),(-1,0), 9),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, HexColor("#f8fafc")]),
                ("GRID",          (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
                ("ALIGN",         (3,0),(4,-1), "CENTER"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0,0),(-1,-1), 5),
                ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                ("LEFTPADDING",   (0,0),(-1,-1), 6),
            ]))
            story.append(st)

        # ── DETALHES POR PAINEL (2 itens/pag) ──────────────────────────────────────
        if opcoes.get("avaliacoes", True) and paineis:
            prog(58, "Gerando detalhes por painel...")

            # Estilos inline dos blocos de item
            _st_num  = ParagraphStyle("_sn", parent=styles["cell_center"],
                           fontSize=20, leading=24, textColor=C_NAVY, fontName="Helvetica-Bold")
            _st_q    = ParagraphStyle("_sq", parent=styles["body"],
                           fontSize=11, leading=15, fontName="Helvetica-Bold",
                           textColor=HexColor("#1a1a1a"), spaceAfter=0, alignment=TA_LEFT)
            _st_jlbl = ParagraphStyle("_sjl", parent=styles["label"],
                           fontSize=8, textColor=C_NAVY, fontName="Helvetica-Bold")
            _st_j    = ParagraphStyle("_sj", parent=styles["body"],
                           fontSize=8, leading=11, fontName="Helvetica-Oblique",
                           textColor=HexColor("#555555"), spaceAfter=1)
            _st_rlbl = ParagraphStyle("_srl", parent=styles["label"],
                           fontSize=8, textColor=HexColor("#888"), fontName="Helvetica-Bold",
                           alignment=TA_CENTER)
            _st_resp = ParagraphStyle("_sr", parent=styles["body"],
                           fontSize=13, leading=17, fontName="Helvetica-Bold", alignment=TA_CENTER)
            _st_pct  = ParagraphStyle("_sp", parent=styles["body"],
                           fontSize=26, leading=30, fontName="Helvetica-Bold", alignment=TA_CENTER)
            _st_ol   = ParagraphStyle("_sol", parent=styles["label"],
                           fontSize=8, textColor=C_NAVY, fontName="Helvetica-Bold")
            _st_obs  = ParagraphStyle("_so", parent=styles["body"],
                           fontSize=9, leading=12, fontName="Helvetica",
                           textColor=HexColor("#333333"))

            for painel in paineis:
                nivel = float(painel.get("nivel_aderencia") or 0.0)
                avaliacoes   = db.listar_avaliacoes(painel["id"])
                fotos_painel = db.listar_fotos(painel["id"]) if opcoes.get("fotos", True) else []
                fotos_por_item = {}
                for _ft in fotos_painel:
                    fotos_por_item.setdefault(_ft.get("item_numero"), []).append(_ft)

                _tag = painel.get("tag", "—")
                _set = painel.get("setor") or "—"
                _tip = painel.get("tipo_painel") or "—"
                _tot = len(checklist_items)

                def _make_foto_cell(fd):
                    cam = fd.get("caminho", "")
                    _fcw = _AW / 4
                    _fimw = _fcw - 10
                    _fimh = 3.6 * cm
                    if not cam or not os.path.exists(cam):
                        return CameraIcon(float(_fimw), float(_fimh))
                    try:
                        from PIL import Image as PILImage
                        with PILImage.open(cam) as _pi:
                            pw, ph = _pi.size
                        r = ph / pw if pw else 1.0
                        if _fimw * r <= _fimh:
                            fw, fh = float(_fimw), float(_fimw * r)
                        else:
                            fh, fw = float(_fimh), float(_fimh / r)
                        return Image(cam, width=fw, height=fh)
                    except Exception:
                        return CameraIcon(float(_fimw), float(_fimh))

                def _item_blk(item):
                    aval = avaliacoes.get(item["numero"], {})
                    resp, peso_val, peso_txt = "Nao avaliado", None, "—"
                    if aval.get("opcao_id"):
                        for opc in item["opcoes"]:
                            if opc["id"] == aval.get("opcao_id"):
                                resp = opc["descricao"]
                                peso_val = opc.get("peso")
                                peso_txt = "N/A" if peso_val is None else "%.0f%%" % (peso_val*100)
                                break
                    obs = aval.get("observacoes", "") or ""
                    ac  = aval.get("acao_corretiva", "") or ""
                    all_fotos = fotos_por_item.get(item["numero"], []) if opcoes.get("fotos", True) else []
                    # Cor da resposta e pontuacao -> preta
                    src = ParagraphStyle("_src2", parent=_st_resp, textColor=HexColor("#1a1a1a"))
                    spc = ParagraphStyle("_spc2", parent=_st_pct,  textColor=HexColor("#1a1a1a"))
                    blks = []
                    # cabecalho mini
                    _h = Table([[
                        Paragraph("<b>PAINEL:</b> %s  |  %s  |  %s" % (_tag, _set, _tip), styles["white_bold"]),
                        Paragraph("<b>ITEM %02d/%02d</b>" % (item["numero"], _tot),
                                  ParagraphStyle("_hi2", parent=styles["white_bold"],
                                      fontSize=11, alignment=TA_RIGHT)),
                    ]], colWidths=[_AW - 2.8*cm, 2.8*cm])
                    _h.setStyle(TableStyle([
                        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
                        ("LINEAFTER",     (0,0),(0,0),   1.5, C_AMBER),
                        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                        ("TOPPADDING",    (0,0),(-1,-1), 6),
                        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                        ("LEFTPADDING",   (0,0),(-1,-1), 10),
                        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
                    ]))
                    blks.append(_h)
                    blks.append(Spacer(1, 0.2 * cm))
                    # questao
                    _q = Table([[
                        Paragraph("<b>%02d</b>" % item["numero"], _st_num),
                        Paragraph(item["questao"], _st_q),
                    ]], colWidths=[1.4*cm, _AW - 1.4*cm])
                    _q.setStyle(TableStyle([
                        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#f8f8f8")),
                        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                        ("TOPPADDING",    (0,0),(-1,-1), 7),
                        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
                        ("LEFTPADDING",   (0,0),(0,0),   6),
                        ("LEFTPADDING",   (1,0),(1,0),   10),
                        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
                        ("LINEBELOW",     (0,0),(-1,-1), 0.75, C_AMBER),
                        ("LINEAFTER",     (0,0),(0,0),   0.5, HexColor("#e0e0e0")),
                    ]))
                    blks.append(_q)
                    # justificativa NR-10
                    jraw = item.get("justificativa", "") or ""
                    jlines = [l.strip() for l in jraw.split("\n") if l.strip()]
                    if jlines:
                        je = [Paragraph("Base Legal NR-10:", _st_jlbl)]
                        for jl in jlines:
                            je.append(Paragraph("*  %s" % jl, _st_j))
                        _jt = Table([[je]], colWidths=[_AW])
                        _jt.setStyle(TableStyle([
                            ("BACKGROUND",    (0,0),(-1,-1), HexColor("#fffbf5")),
                            ("TOPPADDING",    (0,0),(-1,-1), 4),
                            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
                            ("LEFTPADDING",   (0,0),(-1,-1), 12),
                            ("RIGHTPADDING",  (0,0),(-1,-1), 10),
                            ("LINEBEFORE",    (0,0),(0,-1),  1.5, C_AMBER),
                            ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#e8d8c0")),
                        ]))
                        blks.append(_jt)
                    # resultado + pontuacao
                    _rs = Table([[
                        Paragraph("Resultado da Avaliacao", _st_rlbl),
                        Paragraph("PONTUACAO", _st_rlbl),
                    ],[
                        Paragraph(resp, src),
                        Paragraph(peso_txt, spc),
                    ]], colWidths=[_AW * 0.65, _AW * 0.35])
                    _rs.setStyle(TableStyle([
                        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#f5f5f5")),
                        ("BACKGROUND",    (1,0),(1,-1),  HexColor("#f0f0f0")),
                        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
                        ("TOPPADDING",    (0,0),(-1,-1), 6),
                        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                        ("LINEAFTER",     (0,0),(0,-1),  1, C_AMBER),
                        ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#d0d0d0")),
                        ("LINEBELOW",     (0,0),(-1,0),  0.5, HexColor("#d0d0d0")),
                    ]))
                    blks.append(_rs)
                    # obs / acao corretiva
                    if obs or ac:
                        oar = []
                        if obs: oar.append([Paragraph("Observacoes:", _st_ol), Paragraph(obs, _st_obs)])
                        if ac:  oar.append([Paragraph("Acao Corretiva:", _st_ol), Paragraph(ac, _st_obs)])
                        _oa = Table(oar, colWidths=[2.8*cm, _AW - 2.8*cm])
                        _oa.setStyle(TableStyle([
                            ("BACKGROUND",    (0,0),(-1,-1), HexColor("#fdf9f5")),
                            ("VALIGN",        (0,0),(-1,-1), "TOP"),
                            ("TOPPADDING",    (0,0),(-1,-1), 4),
                            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
                            ("LEFTPADDING",   (0,0),(-1,-1), 8),
                            ("RIGHTPADDING",  (0,0),(-1,-1), 8),
                            ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#e0d0c0")),
                        ]))
                        blks.append(_oa)
                    # fotos 4 por linha
                    if all_fotos:
                        _fcw = _AW / 4
                        foto_cells = [_make_foto_cell(f) for f in all_fotos[:4]]
                        while len(foto_cells) < 4:
                            foto_cells.append(Spacer(1, 1))
                        _ft2 = Table([foto_cells], colWidths=[_fcw]*4)
                        _ft2.setStyle(TableStyle([
                            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
                            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                            ("TOPPADDING",    (0,0),(-1,-1), 5),
                            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                            ("LEFTPADDING",   (0,0),(-1,-1), 4),
                            ("RIGHTPADDING",  (0,0),(-1,-1), 4),
                            ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#d0c0b0")),
                            ("INNERGRID",     (0,0),(-1,-1), 0.3, HexColor("#e8e0d8")),
                        ]))
                        blks.append(_ft2)
                    return KeepTogether(blks)

                # Cabecalho do painel (nova pagina para cada painel)
                story.append(PageBreak())

                # Barra de nivel do painel
                nivel_color = nivel_cor(nivel)
                nivel_pct   = "%.1f%%" % (nivel * 100)
                nivel_cat   = nivel_label(nivel)

                pan_hdr = Table([[
                    Paragraph(
                        "<b>PAINEL: %s</b>  |  %s  |  %s  |  Data: %s" % (
                            _tag, _set, _tip, _fmt_date(painel.get("data_avaliacao"))),
                        ParagraphStyle("_ph", parent=styles["white_bold"],
                            fontSize=12, alignment=TA_LEFT)),
                ]], colWidths=[_AW])
                pan_hdr.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
                    ("LEFTPADDING",   (0,0),(-1,-1), 14),
                    ("TOPPADDING",    (0,0),(-1,-1), 10),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 10),
                ]))
                story.append(pan_hdr)
                add_spacer(0.2)

                # Barra de nivel
                nivel_bar = Table([[
                    Paragraph("Nivel de Aderencia:", styles["white_bold"]),
                    Paragraph("<b>%s – %s</b>" % (nivel_pct, nivel_cat),
                        ParagraphStyle("_nb", parent=styles["white_bold"],
                            fontSize=16, alignment=TA_RIGHT)),
                ]], colWidths=[_AW * 0.5, _AW * 0.5])
                nivel_bar.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0),(-1,-1), nivel_color),
                    ("TOPPADDING",    (0,0),(-1,-1), 8),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 8),
                    ("LEFTPADDING",   (0,0),(-1,-1), 14),
                    ("RIGHTPADDING",  (0,0),(-1,-1), 14),
                    ("LINEABOVE",     (0,0),(-1,0),  1, C_AMBER),
                ]))
                story.append(nivel_bar)
                add_spacer(0.3)

                # Fotos de identificacao visual do painel — grade 2x2, imagens maiores
                if opcoes.get("fotos_painel", True):
                    fotos_id = db.buscar_fotos_identificacao(painel["id"])
                    angulos  = ["frontal", "lateral_dir", "lateral_esq", "traseira"]
                    titulos  = ["Frontal", "Lateral Direita", "Lateral Esquerda", "Traseira"]
                    _gutter = 0.5 * cm
                    _fw = (_AW - _gutter) / 2.0
                    _fh = 7.0 * cm
                    id_cells = []
                    for ang, tit in zip(angulos, titulos):
                        cam = (fotos_id or {}).get(ang, "")
                        if cam and os.path.exists(cam):
                            try:
                                from PIL import Image as PILImage
                                with PILImage.open(cam) as _pi:
                                    pw, ph = _pi.size
                                r = ph / pw if pw else 1.0
                                _iw = float(_fw - 16)
                                _ih = float(_iw * r)
                                if _ih > _fh:
                                    _ih = float(_fh)
                                    _iw = float(_fh / r)
                                cell_content = [Image(cam, width=_iw, height=_ih),
                                    Paragraph(tit, ParagraphStyle("_fit", parent=styles["cell_center"],
                                        fontSize=9, textColor=C_NAVY, fontName="Helvetica-Bold"))]
                            except Exception:
                                cell_content = [CameraIcon(float(_fw - 16), float(_fh)),
                                    Paragraph(tit, ParagraphStyle("_fit2", parent=styles["cell_center"],
                                        fontSize=9, textColor=C_MUTED))]
                        else:
                            cell_content = [
                                CameraIcon(float(_fw - 16), float(_fh)),
                                Paragraph(tit, ParagraphStyle("_fitp", parent=styles["cell_center"],
                                    fontSize=9, textColor=C_MUTED))]
                        id_cells.append(cell_content)
                    id_tbl = Table([id_cells[0:2], id_cells[2:4]],
                                    colWidths=[_fw] * 2, rowHeights=[_fh + 26] * 2)
                    id_tbl.setStyle(TableStyle([
                        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
                        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                        ("TOPPADDING",    (0,0),(-1,-1), 10),
                        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
                        ("LEFTPADDING",   (0,0),(-1,-1), 8),
                        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
                        ("INNERGRID",     (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
                    ]))
                    id_lbl = Table([[
                        Paragraph("Identificacao Visual do Painel", styles["white_bold"])
                    ]], colWidths=[_AW])
                    id_lbl.setStyle(TableStyle([
                        ("BACKGROUND",    (0,0),(-1,-1), C_DARK),
                        ("TOPPADDING",    (0,0),(-1,-1), 6),
                        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                        ("LEFTPADDING",   (0,0),(-1,-1), 14),
                    ]))
                    story.append(id_lbl)
                    add_spacer(0.25)
                    story.append(id_tbl)
                    add_spacer(0.3)

                add_spacer(0.3)

                # 2 itens por pagina
                items_do_painel = list(checklist_items)
                for i in range(0, len(items_do_painel), 2):
                    story.append(PageBreak())
                    story.append(_item_blk(items_do_painel[i]))
                    if i + 1 < len(items_do_painel):
                        add_spacer(0.4)
                        story.append(HRFlowable(width="100%", thickness=1, color=C_AMBER,
                                                spaceAfter=6))
                        add_spacer(0.2)
                        story.append(_item_blk(items_do_painel[i + 1]))


        # ── GRAFICOS ────────────────────────────────────────────────────────────────
        if opcoes.get("graficos", True) and paineis:
            prog(75, "Gerando graficos estatisticos...")
            story.append(PageBreak())
            add_section("7.", "ESTRATIFICACAO DOS DADOS – RESULTADOS ESTATISTICOS")
            add_spacer(0.3)
            story.append(Paragraph(
                "A seguir sao apresentados graficos com os resultados consolidados "
                "das avaliacoes realizadas, permitindo uma visao estrategica da situacao das instalacoes.",
                styles["body"]))
            add_spacer(0.3)

            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                from io import BytesIO

                # Grafico 1: nivel por painel
                tags = [p.get("tag", "P%d" % (i+1)) for i, p in enumerate(paineis)]
                niveis = [float(p.get("nivel_aderencia") or 0.0) for p in paineis]
                colors = [("#1a7f37" if n >= 0.85 else "#9a6700" if n >= 0.60 else "#b91c1c")
                          for n in niveis]
                fig, ax = plt.subplots(figsize=(10, 4))
                bars = ax.bar(tags, [n*100 for n in niveis], color=colors,
                              edgecolor="#d0d7de", linewidth=0.8)
                ax.axhline(y=85, color="#1a7f37", linestyle="--", alpha=0.7, label="BOM (>=85%)")
                ax.axhline(y=60, color="#9a6700", linestyle="--", alpha=0.7, label="REGULAR (>=60%)")
                ax.set_ylabel("Nivel de Aderencia (%)", fontsize=9)
                ax.set_title("Nivel de Aderencia por Painel", fontsize=11,
                              fontweight="bold", color="#1a1a1a")
                ax.set_ylim(0, 110)
                ax.legend(fontsize=8)
                for bar, nv in zip(bars, niveis):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                            "%.1f%%" % (nv*100), ha="center", va="bottom",
                            fontsize=8, fontweight="bold")
                plt.xticks(rotation=30, ha="right", fontsize=8)
                plt.tight_layout()
                buf = BytesIO()
                plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
                plt.close(fig)
                buf.seek(0)
                chart1 = Image(buf, width=15*cm, height=6*cm)
                chart1.hAlign = "CENTER"
                story.append(chart1)
                add_spacer(0.4)

                # Grafico 2: conformidade media por item
                item_nums = []
                item_medias = []
                for it in checklist_items:
                    stats = estatisticas["item_stats"].get(it["numero"], {})
                    item_nums.append("Item %02d" % it["numero"])
                    item_medias.append(float(stats.get("media") or 0.0) * 100)
                fig2, ax2 = plt.subplots(figsize=(10, 4))
                colors2 = [("#1a7f37" if m >= 85 else "#9a6700" if m >= 60 else "#b91c1c")
                            for m in item_medias]
                ax2.bar(item_nums, item_medias, color=colors2, edgecolor="#d0d7de", linewidth=0.8)
                ax2.axhline(y=85, color="#1a7f37", linestyle="--", alpha=0.5)
                ax2.axhline(y=60, color="#9a6700", linestyle="--", alpha=0.5)
                ax2.set_ylabel("Conformidade Media (%)", fontsize=9)
                ax2.set_title("Conformidade Media por Item de Avaliacao", fontsize=11,
                              fontweight="bold", color="#1a1a1a")
                ax2.set_ylim(0, 110)
                for bar, med in zip(ax2.patches, item_medias):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                             "%.0f%%" % med, ha="center", va="bottom", fontsize=7, fontweight="bold")
                plt.xticks(rotation=20, ha="right", fontsize=8)
                plt.tight_layout()
                buf2 = BytesIO()
                plt.savefig(buf2, format="png", dpi=150, bbox_inches="tight")
                plt.close(fig2)
                buf2.seek(0)
                chart2 = Image(buf2, width=15*cm, height=6*cm)
                chart2.hAlign = "CENTER"
                story.append(chart2)
                add_spacer(0.4)

                # Grafico 3: pizzas por item (somente quando > 1 painel)
                if len(paineis) > 1:
                    story.append(PageBreak())
                    add_subsection("7.1", "Avaliacao de Conformidades")
                    story.append(Paragraph(
                        "Distribuicao de conformidade de cada item avaliado "
                        "entre os paineis inspecionados (verde=Conforme, laranja=Parcial, vermelho=Nao Conforme).",
                        styles["body"]))
                    add_spacer(0.2)

                    pie_data = {it["numero"]: {"C": 0, "P": 0, "N": 0} for it in checklist_items}
                    for _pan in paineis:
                        _avs = db.listar_avaliacoes(_pan["id"])
                        for it in checklist_items:
                            aval = _avs.get(it["numero"], {})
                            if not aval.get("opcao_id"):
                                continue
                            peso_v = None
                            for opc in it["opcoes"]:
                                if opc["id"] == aval.get("opcao_id"):
                                    peso_v = opc.get("peso")
                                    break
                            if peso_v is None:
                                continue
                            if peso_v >= 0.9:   pie_data[it["numero"]]["C"] += 1
                            elif peso_v > 0:    pie_data[it["numero"]]["P"] += 1
                            else:               pie_data[it["numero"]]["N"] += 1

                    COLS = 3
                    n_items = len(checklist_items)
                    n_rows = (n_items + COLS - 1) // COLS
                    fig3, axes = plt.subplots(n_rows, COLS, figsize=(10, n_rows * 3.6))
                    if n_rows == 1:
                        axes = list(axes) if COLS > 1 else [axes]
                    else:
                        axes = [ax for row in axes for ax in (list(row) if COLS > 1 else [row])]
                    pie_cols = ["#1a7f37", "#e8820c", "#b91c1c"]
                    pie_lbls = ["Conforme", "Parcial", "Nao conf."]
                    for idx, it in enumerate(checklist_items):
                        ax = axes[idx]
                        d = pie_data[it["numero"]]
                        vals = [d["C"], d["P"], d["N"]]
                        total = sum(vals)
                        if total == 0:
                            ax.pie([1], colors=["#e0e0e0"])
                            ax.set_title("Item %02d\n(sem resposta)" % it["numero"],
                                         fontsize=8, color="#888")
                        else:
                            nz = [(v,c,l) for v,c,l in zip(vals, pie_cols, pie_lbls) if v > 0]
                            _v = [x[0] for x in nz]
                            _c = [x[1] for x in nz]
                            _l = ["%s\n(%d)" % (x[2], x[0]) for x in nz]
                            wedges, texts, auts = ax.pie(
                                _v, labels=_l, colors=_c,
                                autopct=lambda p: ("%.0f%%" % p) if p > 0 else "",
                                startangle=90, textprops={"fontsize": 7},
                                wedgeprops={"linewidth": 0.5, "edgecolor": "white"})
                            for at in auts:
                                at.set_fontsize(7)
                                at.set_fontweight("bold")
                                at.set_color("white")
                            import textwrap as _tw
                            q_s = _tw.fill(it["questao"], width=30)
                            ax.set_title("Item %02d\n%s" % (it["numero"], q_s),
                                         fontsize=7, fontweight="bold", color="#1a1a1a", pad=4)
                    for idx in range(n_items, len(axes)):
                        axes[idx].set_visible(False)
                    plt.tight_layout(pad=1.2)
                    buf3 = BytesIO()
                    plt.savefig(buf3, format="png", dpi=150, bbox_inches="tight")
                    plt.close(fig3)
                    buf3.seek(0)
                    _pie_w = 16 * cm
                    _pie_h = _pie_w * (n_rows * 3.6 / 10.0)
                    chart3 = Image(buf3, width=_pie_w, height=_pie_h)
                    chart3.hAlign = "CENTER"
                    story.append(chart3)

            except ImportError:
                story.append(Paragraph(
                    "Instale matplotlib para visualizacao de graficos: pip install matplotlib",
                    styles["obs"]))

            # Tabela resumo por item (em pagina propria, para nao quebrar a tabela ao meio)
            story.append(PageBreak())
            add_subsection("7.2", "Resumo Estatistico por Item")
            stat_data = [["Item", "Questao (resumo)", "Conformes", "Parciais", "Nao conf.", "Media"]]
            for it in checklist_items:
                stats = estatisticas["item_stats"].get(it["numero"], {})
                cont = stats.get("contagens", {})
                media = float(stats.get("media") or 0.0)
                stat_data.append([
                    str(it["numero"]),
                    it["questao"][:45] + ("..." if len(it["questao"]) > 45 else ""),
                    str(cont.get("Sim", 0)),
                    str(cont.get("Parcial", 0)),
                    str(cont.get("Nao", 0)),
                    "%.1f%%" % (media*100),
                ])
            stt = Table(stat_data, colWidths=[0.8*cm, 8*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.8*cm])
            stt.setStyle(TableStyle([
                ("BACKGROUND",  (0,0),(-1,0), C_NAVY),
                ("TEXTCOLOR",   (0,0),(-1,0), C_WHITE),
                ("FONTNAME",    (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",    (0,0),(-1,-1), 8),
                ("GRID",        (0,0),(-1,-1), 0.5, HexColor("#d0d7de")),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, HexColor("#f8fafc")]),
                ("ALIGN",       (0,0),(-1,-1), "CENTER"),
                ("ALIGN",       (1,0),(1,-1),  "LEFT"),
                ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING",  (0,0),(-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("LEFTPADDING", (1,0),(1,-1),  4),
            ]))
            story.append(stt)


        # ── CONCLUSOES ───────────────────────────────────────────────────────────────
        if opcoes.get("conclusoes", True):
            prog(85, "Gerando conclusoes e recomendacoes...")
            story.append(PageBreak())
            add_section("8.", "CONCLUSOES E RECOMENDACOES")
            add_spacer(0.3)

            # Resultado geral
            nivel_geral = estatisticas.get("media_geral", 0.0)
            nivel_label_txt = nivel_label(nivel_geral)
            nivel_color = nivel_cor(nivel_geral)

            res_data = [
                ["RESULTADO GERAL DA AVALIACAO", "NIVEL DE ADERENCIA", "CLASSIFICACAO"],
                [laudo.get("titulo", "Laudo NR-10"),
                 "%.1f%%" % (float(nivel_geral or 0) * 100),
                 nivel_label_txt]
            ]
            rt = Table(res_data, colWidths=[_AW * 0.5, _AW * 0.25, _AW * 0.25])
            rt.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, 0), C_NAVY),
                ("TEXTCOLOR",    (0, 0), (-1, 0), C_WHITE),
                ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",     (0, 0), (-1, 0), 9),
                ("BACKGROUND",   (1, 1), (1, 1), nivel_color),
                ("BACKGROUND",   (2, 1), (2, 1), nivel_color),
                ("TEXTCOLOR",    (1, 1), (-1, -1), C_WHITE),
                ("FONTNAME",     (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE",     (0, 1), (-1, 1), 10),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ("GRID",         (0, 0), (-1, -1), 0.5, C_WHITE),
                ("TOPPADDING",   (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
            ]))
            story.append(rt)
            add_spacer(0.4)

            # Texto de conclusoes
            conclusoes_txt = laudo.get("conclusoes", "") or (
                "Com base nas avaliacoes realizadas nas instalacoes eletricas da empresa "
                + (cliente.get("razao_social", "") or "") + ", conclui-se que o nivel de aderencia "
                "as exigencias da NR-10 e de " + ("%.1f%%" % (float(nivel_geral or 0) * 100))
                + ", classificado como " + nivel_label_txt + ". "
                "Recomenda-se que as nao conformidades identificadas sejam tratadas de forma "
                "prioritaria conforme plano de acao proposto."
            )
            add_subsection("8.1", "Conclusao Tecnica")
            for para in conclusoes_txt.split(chr(10) + chr(10)):
                txt = para.strip()
                if txt:
                    story.append(Paragraph(txt, styles["body"]))
                    add_spacer(0.15)
            add_spacer(0.3)

            # Texto de recomendacoes
            recomendacoes_txt = laudo.get("recomendacoes", "") or (
                "Recomenda-se a implementacao imediata de um Plano de Acao estruturado, "
                "priorizando os itens classificados como Nao Conformes, seguidos pelos Parcialmente "
                "Conformes. Os itens de alta criticidade devem ser corrigidos em prazo maximo de 30 dias, "
                "itens de media criticidade em 60 dias e os demais em ate 90 dias. "
                "Alem disso, recomenda-se a capacitacao continua dos profissionais envolvidos com "
                "instalacoes eletricas, conforme exigido pela NR-10."
            )
            add_subsection("8.2", "Recomendacoes Tecnicas")
            for para in recomendacoes_txt.split(chr(10) + chr(10)):
                txt = para.strip()
                if txt:
                    story.append(Paragraph(txt, styles["body"]))
                    add_spacer(0.15)
            add_spacer(0.3)

            # Tabela de prioridades
            add_subsection("8.3", "Plano de Acao – Prioridades")
            pri_data = [
                ["Nivel", "Criterio", "Prazo Recomendado", "Responsavel"],
                ["CRITICO",  "Risco imediato de acidente", "Imediato (ate 7 dias)",  "Eng. Responsavel"],
                ["ALTO",     "Nao conformidade grave",     "Curto prazo (30 dias)",  "Manutencao Eletrica"],
                ["MEDIO",    "Conformidade parcial",        "Medio prazo (60 dias)",  "Manutencao Eletrica"],
                ["BAIXO",    "Melhoria recomendada",        "Longo prazo (90 dias)",  "Gestao de Facilities"],
            ]
            pri_colors = [C_NAVY, HexColor("#b91c1c"), HexColor("#9a6700"),
                          HexColor("#1a7f37"), HexColor("#1d4ed8")]
            pt = Table(pri_data, colWidths=[_AW*0.15, _AW*0.35, _AW*0.28, _AW*0.22])
            pri_style = [
                ("BACKGROUND",   (0, 0), (-1, 0), C_NAVY),
                ("TEXTCOLOR",    (0, 0), (-1, 0), C_WHITE),
                ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",     (0, 0), (-1, -1), 8),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("ALIGN",        (1, 0), (1, -1), "LEFT"),
                ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ("GRID",         (0, 0), (-1, -1), 0.5, HexColor("#d0d7de")),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [HexColor("#f8fafc"), C_WHITE]),
                ("TOPPADDING",   (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
                ("LEFTPADDING",  (1, 0), (1, -1), 4),
            ]
            for row_idx, color in enumerate(pri_colors[1:], 1):
                pri_style.append(("BACKGROUND", (0, row_idx), (0, row_idx), color))
                pri_style.append(("TEXTCOLOR",  (0, row_idx), (0, row_idx), C_WHITE))
                pri_style.append(("FONTNAME",   (0, row_idx), (0, row_idx), "Helvetica-Bold"))
            pt.setStyle(TableStyle(pri_style))
            story.append(pt)

            # Plano de Acao Individual por Painel: grafico de barras horizontais,
            # ordenado do painel mais critico para o mais adequado, para indicar
            # ao usuario a prioridade de correcao.
            if paineis:
                story.append(PageBreak())
                add_subsection("8.4", "Plano de Acao Individual por Painel")
                story.append(Paragraph(
                    "O grafico abaixo apresenta o nivel de aderencia obtido por cada painel "
                    "avaliado, ordenado do mais critico para o mais adequado, indicando a "
                    "prioridade de correcao recomendada para cada um.",
                    styles["body"]))
                add_spacer(0.3)
                try:
                    import matplotlib
                    matplotlib.use("Agg")
                    import matplotlib.pyplot as plt
                    from io import BytesIO

                    paineis_ord = sorted(
                        paineis, key=lambda p: float(p.get("nivel_aderencia") or 0.0))
                    tags4 = [p.get("tag") or ("Painel %d" % (i + 1))
                             for i, p in enumerate(paineis_ord)]
                    niveis4 = [float(p.get("nivel_aderencia") or 0.0) * 100 for p in paineis_ord]
                    colors4 = [("#1a7f37" if n >= 85 else "#9a6700" if n >= 60 else "#b91c1c")
                               for n in niveis4]

                    fig4_h = max(2.6, 0.6 * len(paineis_ord) + 1.2)
                    fig4, ax4 = plt.subplots(figsize=(10, fig4_h))
                    bars4 = ax4.barh(tags4, niveis4, color=colors4,
                                      edgecolor="#d0d7de", linewidth=0.8)
                    ax4.axvline(x=85, color="#1a7f37", linestyle="--", alpha=0.6,
                                label="BOM (>=85%)")
                    ax4.axvline(x=60, color="#9a6700", linestyle="--", alpha=0.6,
                                label="REGULAR (>=60%)")
                    ax4.set_xlim(0, 128)
                    ax4.set_xlabel("Nivel de Aderencia (%)", fontsize=9)
                    ax4.set_title("Prioridade de Correcao por Painel (do mais critico ao mais adequado)",
                                  fontsize=11, fontweight="bold", color="#1a1a1a")
                    ax4.invert_yaxis()  # painel mais critico no topo
                    ax4.legend(fontsize=8, loc="upper right")
                    for bar, nv in zip(bars4, niveis4):
                        ax4.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2,
                                  "%.1f%%" % nv, va="center", fontsize=8, fontweight="bold")
                    plt.tight_layout()
                    buf4 = BytesIO()
                    plt.savefig(buf4, format="png", dpi=150, bbox_inches="tight")
                    plt.close(fig4)
                    buf4.seek(0)
                    _c4w = _AW
                    _c4h = _c4w * (fig4_h / 10.0)
                    chart4 = Image(buf4, width=_c4w, height=_c4h)
                    chart4.hAlign = "CENTER"
                    story.append(chart4)
                except ImportError:
                    story.append(Paragraph(
                        "Instale matplotlib para visualizacao do grafico: pip install matplotlib",
                        styles["obs"]))

        # ── ASSINATURAS ──────────────────────────────────────────────────────────────
        if opcoes.get("assinaturas", True):
            story.append(PageBreak())

            profissionais_lc = db.profissionais_do_laudo(laudo_id)
            participantes_lc = db.participantes_do_laudo(laudo_id)

            _sig_style = ParagraphStyle("_sig", parent=styles["body"],
                                         alignment=TA_CENTER, fontSize=9, leading=12)

            def _sig_cell(nome, sub, papel):
                return [
                    HRFlowable(width=6.5 * cm, thickness=0.75, color=HexColor("#1a2332"),
                               hAlign="CENTER", spaceAfter=6),
                    Paragraph("<b>%s</b><br/>%s" % (nome, sub or "&nbsp;"), _sig_style),
                    Paragraph(papel, ParagraphStyle("_sigrole", parent=_sig_style,
                                                     fontSize=8, textColor=C_MUTED)),
                ]

            signatarios = []
            for prof in profissionais_lc:
                nome  = prof.get("nome", "-")
                crea  = prof.get("crea", "")
                cargo = prof.get("habilitacao", "") or prof.get("cargo", "")
                sub = cargo
                if crea:
                    sub = (sub + "  |  CREA: " + crea) if sub else ("CREA: " + crea)
                signatarios.append(_sig_cell(nome, sub, "Responsavel Tecnico pela Elaboracao do Laudo"))
            for part in participantes_lc:
                nome  = part.get("nome", "-")
                empresa = part.get("empresa", "")
                cargo_setor = "%s / %s" % (part.get("cargo", ""), part.get("setor", "")) \
                    if part.get("cargo") else part.get("setor", "")
                sub = cargo_setor
                if empresa:
                    sub = (sub + "  |  " + empresa) if sub else empresa
                signatarios.append(_sig_cell(nome, sub, "Fornecedor de Informacoes"))

            # Matriz fixa de 2 colunas x 4 linhas (8 posicoes), alinhada e
            # centralizada dentro das margens, ocupando a maior parte da
            # altura util da folha -- se houver mais de 8 assinantes, gera
            # grades adicionais em novas paginas seguindo o mesmo padrao.
            _n_cols, _n_rows = 2, 4
            _top_gap    = 1.5 * cm
            _bottom_gap = 1.3 * cm
            _note_h     = 1.0 * cm
            _row_h = ((H - MARGIN_T - MARGIN_B) - _top_gap - _bottom_gap - _note_h) / _n_rows

            if signatarios:
                for start in range(0, len(signatarios), _n_cols * _n_rows):
                    if start > 0:
                        story.append(PageBreak())
                    add_spacer(_top_gap / cm)
                    grupo = signatarios[start:start + _n_cols * _n_rows]
                    grid_data = []
                    for r in range(_n_rows):
                        linha = []
                        for c in range(_n_cols):
                            idx = r * _n_cols + c
                            linha.append(grupo[idx] if idx < len(grupo) else "")
                        grid_data.append(linha)
                    sig_tbl = Table(grid_data, colWidths=[_AW / _n_cols] * _n_cols,
                                    rowHeights=[_row_h] * _n_rows)
                    sig_tbl.setStyle(TableStyle([
                        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                    ]))
                    story.append(sig_tbl)
            else:
                add_spacer(_top_gap / cm)

            add_spacer(_bottom_gap / cm)
            story.append(Paragraph(
                "Documento poderá ser assinado de forma eletrônica, nos termos da MP 2200-2/2001",
                ParagraphStyle("_mp2200", parent=styles["obs"], alignment=TA_CENTER)))

        return story

    # Passada 1: constroi o documento inteiro uma vez (saida descartavel, em
    # memoria) apenas para descobrir em que pagina cada secao/subsecao caiu,
    # via _LaudoDocTemplate.afterFlowable(). So depois disso da para saber os
    # numeros de pagina que devem aparecer no Sumario.
    prog(6, "Calculando paginacao do sumario...")
    story_pass1 = _build(toc_pages=None)
    doc1 = _make_doc(io.BytesIO())
    doc1.build(story_pass1, canvasmaker=_canvas_maker)
    toc_pages = doc1.toc_registry

    # Passada 2: reconstroi a lista de flowables do zero (Platypus consome/
    # muta os flowables durante o build, entao nao da para reusar a mesma
    # lista) e gera o PDF definitivo, agora com o Sumario completo.
    story_pass2 = _build(toc_pages=toc_pages)
    doc2 = _make_doc(output_path)
    prog(95, "Compilando documento PDF...")
    doc2.build(story_pass2, canvasmaker=_canvas_maker)
    prog(100, "PDF gerado com sucesso!")
    return output_path
