"""
Confere se o pacote gerado pelo PyInstaller esta completo e realmente abre.

Rodado pelo build_installer.bat logo apos a compilacao. Um pacote incompleto
so falha na maquina do cliente, ja instalado, e aparece como uma janela que
nao abre -- sem mensagem nenhuma, porque o executavel e "windowed".

A checagem tem duas partes:

1. Arquivos de dados. Bibliotecas Python puras (reportlab, qrcode, fitz...)
   nao aparecem como pastas: ficam compactadas dentro do proprio executavel.
   So faz sentido procurar no disco o que o PyInstaller copia como dado --
   os recursos do projeto e os pacotes que trazem DLLs.

2. Execucao real. E o unico jeito de saber se algum modulo ficou de fora:
   o programa e aberto de verdade e precisa continuar vivo alguns segundos.
   Faltando um import, ele morre imediatamente.
"""
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).parent
DIST = RAIZ / "dist" / "GerLauNR10"
EXE = DIST / "GerLauNR10.exe"
SEGUNDOS_VIVO = 12

# (caminho dentro do pacote, descricao, obrigatorio)
ARQUIVOS = [
    ("GerLauNR10.exe",                          "executavel principal",       True),
    ("_internal/Icone.ico",                     "icone da aplicacao",         True),
    ("_internal/resources/logo_engelogic.png",  "logo da Engelogic",          True),
    ("_internal/resources/logo_sensorlogic.png", "logo da Sensorlogic",       True),
    ("_internal/campo/GerLauNR10_Campo.html",   "aplicativo de campo",        True),
    ("_internal/PyQt6",                         "PyQt6 (interface)",          True),
    ("_internal/PIL",                           "Pillow (imagens)",           True),
    ("_internal/matplotlib",                    "matplotlib (graficos)",      True),
    ("_internal/base_library.zip",              "biblioteca padrao",          True),
]


def conferir_arquivos() -> bool:
    ok = True
    for rel, descricao, obrigatorio in ARQUIVOS:
        if (DIST / rel).exists():
            print("  ok      %-42s %s" % (rel, descricao))
        else:
            print("  %s %-42s %s" % ("FALTA  " if obrigatorio else "aviso  ", rel, descricao))
            ok = ok and not obrigatorio
    return ok


def conferir_execucao() -> bool:
    """Abre o programa e verifica se ele se mantem em pe."""
    print("\n  Abrindo o programa para conferir se inicia...")
    try:
        proc = subprocess.Popen([str(EXE)], cwd=str(DIST),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        print("  FALHA   nao foi possivel executar: %s" % e)
        return False

    fim = time.time() + SEGUNDOS_VIVO
    while time.time() < fim:
        if proc.poll() is not None:
            saida = (proc.stderr.read() or b"").decode("utf-8", "replace").strip()
            print("  FALHA   o programa fechou sozinho (codigo %s)" % proc.returncode)
            if saida:
                print("          %s" % saida.splitlines()[-1][:200])
            return False
        time.sleep(0.5)

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("  ok      continuou aberto por %d segundos" % SEGUNDOS_VIVO)
    return True


def main() -> int:
    if not DIST.exists():
        print("[ERRO] pasta nao encontrada: %s" % DIST)
        return 1

    arquivos_ok = conferir_arquivos()
    n = sum(1 for f in DIST.rglob("*") if f.is_file())
    tam = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print("\n  pacote: %d arquivos, %.0f MB" % (n, tam / 1e6))

    execucao_ok = conferir_execucao() if arquivos_ok else False

    if arquivos_ok and execucao_ok:
        print("\n[OK] Pacote completo e funcional.")
        return 0
    print("\n[ERRO] Pacote com problema -- nao gere o instalador assim.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
