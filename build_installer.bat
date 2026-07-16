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
    --icon "Icone.ico" ^
    --add-data "resources;resources" ^
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
IF %ERRORLEVEL% NEQ 0 GOTO ISS_FALHOU

echo [OK] Script Inno Setup gerado: GerLauNR10_installer.iss

:: Tenta compilar com Inno Setup (se instalado). O caminho padrao contem
:: parenteses ("Program Files (x86)"), por isso essa etapa usa GOTO em vez
:: de blocos IF/ELSE com parenteses -- parenteses dentro de um bloco IF( )
:: quebram o parser do cmd.exe.
SET "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
IF NOT EXIST "%INNO_PATH%" GOTO INNO_NAO_ENCONTRADO

echo [INFO] Compilando instalador com Inno Setup...
"%INNO_PATH%" GerLauNR10_installer.iss
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Inno Setup falhou ao compilar o instalador.
) ELSE (
    echo [OK] Instalador gerado em: Output\
)
GOTO FIM_ISS

:INNO_NAO_ENCONTRADO
echo [INFO] Inno Setup nao encontrado automaticamente em:
echo        %INNO_PATH%
echo        Abra o arquivo GerLauNR10_installer.iss no Inno Setup IDE
echo        ou instale em: https://jrsoftware.org/isinfo.php
GOTO FIM_ISS

:ISS_FALHOU
echo [AVISO] Geracao do .iss falhou. Execute generate_iss.py manualmente.

:FIM_ISS
echo.
echo ============================================================
echo   Build concluido!
echo ============================================================
pause
