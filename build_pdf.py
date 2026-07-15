"""
Script para reconstruir o pdf_generator.py a partir de partes em /tmp/
Execute: python build_pdf.py
"""
import os, ast, shutil

parts_dir = "/tmp"
target = os.path.join(os.path.dirname(__file__), "pdf_generator.py")

# Lê todas as partes em ordem
parts = []
for i in range(1, 20):
    p = os.path.join(parts_dir, "pdf_part%d.py" % i)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            parts.append(f.read())
        print("  Leu parte %d (%d chars)" % (i, len(parts[-1])))
    else:
        break

if not parts:
    print("ERRO: nenhuma parte encontrada em /tmp/pdf_part*.py")
    raise SystemExit(1)

content = "\n".join(parts)
# Verifica sintaxe
ast.parse(content)
print("Sintaxe OK — %d linhas" % content.count("\n"))

with open(target, "w", encoding="utf-8") as f:
    f.write(content)
print("Escrito em:", target)
