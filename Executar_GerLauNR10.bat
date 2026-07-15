@echo off
SETLOCAL
chcp 65001 >nul
cd /d "%~dp0"

title GerLauNR10 - Gerador de Laudos NR-10

python main.py
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo   O aplicativo encerrou com erro ^(veja a mensagem acima^).
    echo ============================================================
    pause
)
