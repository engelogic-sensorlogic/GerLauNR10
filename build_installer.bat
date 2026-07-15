@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
chcp 65001 >nul

echo ============================================================
echo   GerLauNR10 - Gerador de Instalador (Inno Setup)
echo   Engelogic Automação e Controle Industrial
echo ============================================================
echo.

:: Verifica PyInstaller
pip show pyinstaller >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [INFO] Instalando PyInstaller...
    pip install pyinstaller
)

:: Build com PyInstaller
echo [INFO] Compilando executável com PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name "GerLauNR10" ^
    --icon "resources\icon.ico" ^
    --add-data "resources;resources" ^
    --add-data "data;data" ^
    main.py

IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] PyInstaller falhou. Verifique os erros acima.
    pause
    exit /b 1
)

echo [OK] Executável gerado em: dist\GerLauNR10\

:: Gera arquivo .iss para Inno Setup
echo [INFO] Gerando script Inno Setup (.iss)...
python generate_iss.py

IF %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Geração do .iss falhou. Execute generate_iss.py manualmente.
) ELSE (
    echo [OK] Script Inno Setup gerado: GerLauNR10_installer.iss

    :: Tenta compilar com Inno Setup (se instalado)
    SET INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
    IF EXIST "!INNO_PATH!" (
        echo [INFO] Compilando instalador com Inno Setup...
        "!INNO_PATH!" GerLauNR10_installer.iss
        echo [OK] Instalador gerado: Output\GerLauNR10_Setup.exe
    ) ELSE (
        echo [INFO] Inno Setup não encontrado automaticamente.
        echo        Abra o arquivo GerLauNR10_installer.iss no Inno Setup IDE
        echo        ou instale em: https://jrsoftware.org/isinfo.php
    )
)

echo.
echo ============================================================
echo   Build concluído!
echo ============================================================
pause
