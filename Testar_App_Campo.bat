@echo off
SETLOCAL
chcp 65001 >nul
cd /d "%~dp0"

title GerLauNR10 - Teste do aplicativo de campo

echo ============================================================
echo   GerLauNR10 Campo - teste no PC
echo ============================================================
echo.
echo   Endereco: http://127.0.0.1:8790
echo.
echo   No navegador: F12 e depois Ctrl+Shift+M para ver como celular.
echo   Escolha o modelo do aparelho no topo da tela e aperte F5.
echo.
echo   Mantenha esta janela aberta durante o teste.
echo   Para encerrar, feche esta janela ou aperte Ctrl+C.
echo ============================================================
echo.

python -c "import functools, webbrowser, http.server as h; s = h.ThreadingHTTPServer(('127.0.0.1', 8790), functools.partial(h.SimpleHTTPRequestHandler, directory='docs')); webbrowser.open('http://127.0.0.1:8790/'); s.serve_forever()"
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo   Nao foi possivel iniciar o servidor ^(veja a mensagem acima^).
    echo   Se a porta 8790 ja estiver em uso, feche a outra janela de teste.
    echo ============================================================
    pause
)
