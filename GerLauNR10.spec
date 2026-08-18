# -*- mode: python ; coding: utf-8 -*-
"""
Build do GerLauNR10 (PyInstaller).

Este arquivo e a fonte unica da configuracao de build -- build_installer.bat
chama "pyinstaller GerLauNR10.spec" em vez de repetir as opcoes na linha de
comando, para que as duas formas de compilar nunca divirjam.
"""

# Arquivos de dados que precisam acompanhar o executavel.
datas = [
    ('resources', 'resources'),          # logo usado na interface e no PDF
    ('Icone.ico', '.'),                  # icone do atalho e do instalador
    ('campo/GerLauNR10_Campo.html', 'campo'),  # aplicativo de coleta em campo
]

# Modulos que a analise estatica pode nao alcancar.
# - qrcode: importado dentro de uma funcao em ui/celular_widget.py
# - PIL.*: usado por qrcode e pelo redimensionamento de fotos do PDF
# - fitz/pymupdf: importado sob demanda ao inserir a ART no laudo
hiddenimports = [
    'qrcode',
    'qrcode.image.pil',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageOps',
    'fitz',
    'pymupdf',
    'reportlab.graphics.barcode',
    'openpyxl',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt5', 'PySide6'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GerLauNR10',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Icone.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GerLauNR10',
)
