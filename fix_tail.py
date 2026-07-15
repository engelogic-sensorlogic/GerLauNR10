"""Script para corrigir truncamento do pdf_generator.py"""
import os

filepath = os.path.join(os.path.dirname(__file__), "pdf_generator.py")
with open(filepath, encoding='utf-8') as f:
    content = f.read()

# Localiza o ponto de corte
marker = '            story.append(Paragraph(\n                "<b>%s</b><br/>%s%s" % (nome, cargo, crea_str),\n                ParagraphStyle("_sig", par'
pos = content.rfind('            story.append(Paragraph(\n                "<b>%s</b><br/>%s%s" % (nome, cargo, crea_str),')
if pos < 0:
    print("Marcador nao encontrado — procurando alternativo")
    pos = content.rfind('crea_str = "  |  CREA: " + crea if crea else ""')
    pos = content.find('\n', pos) + 1  # linha seguinte

content = content[:pos]

TAIL = '''            story.append(Paragraph(
                "<b>%s</b><br/>%s%s" % (nome, cargo, crea_str),
                ParagraphStyle("_sig", parent=styles["body"], alignment=TA_CENTER, fontSize=9)
            ))
            add_spacer(0.3)

    # -- BUILD ---------------------------------------------------------------
    prog(95, "Compilando documento PDF...")
    doc.build(story, canvasmaker=_canvas_maker)
    prog(100, "PDF gerado com sucesso!")
    return output_path
'''

content = content + TAIL

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

import ast
ast.parse(content)
print("pdf_generator.py OK — %d linhas" % content.count('\n'))
