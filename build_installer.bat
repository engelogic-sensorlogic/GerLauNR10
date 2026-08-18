@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
chcp 65001 >nul

echo ============================================================
echo   GerLauNR10 - Gerador de Instalador
echo   Engelogic Automacao e Controle Industrial
echo ============================================================
echo.

cd /d "%~dp0"

:: ---------------------------------------------------------------
:: 1) Dependencias do projeto
:: ---------------------------------------------------------------
echo [INFO] Conferindo dependencias do requirements.txt...
pip install -r requirements.txt --quiet --disable-pip-version-check
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao instalar as dependencias do requirements.txt
    pause
    exit /b 1
)

pip show pyinstaller >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [INFO] Instalando PyInstaller...
    pip install pyinstaller --quiet --disable-pip-version-check
)

:: ---------------------------------------------------------------
:: 2) Limpeza dos artefatos anteriores
:: ---------------------------------------------------------------
echo [INFO] Limpando build anterior...
IF EXIST "build" rmdir /s /q "build"
IF EXIST "dist"  rmdir /s /q "dist"

:: ---------------------------------------------------------------
:: 3) Compilacao
::    Usa GerLauNR10.spec, que ja define icone, arquivos de dados e
::    os modulos que a analise estatica nao alcanca. Repetir essas
::    opcoes aqui faria as duas configuracoes divergirem com o tempo.
:: ---------------------------------------------------------------
:: O PyInstaller falha com OSError(22) ao montar o executavel quando a area
:: de trabalho fica em unidade de rede -- e este projeto costuma ficar em Z:.
:: Por isso o build acontece em disco local e o resultado e copiado de volta.
SET "BUILD_TMP=%TEMP%\gerlau_build"
IF EXIST "%BUILD_TMP%" rmdir /s /q "%BUILD_TMP%"

echo [INFO] Compilando com PyInstaller (GerLauNR10.spec)...
echo        area de trabalho: %BUILD_TMP%
pyinstaller --noconfirm --clean ^
    --workpath "%BUILD_TMP%\work" ^
    --distpath "%BUILD_TMP%\dist" ^
    GerLauNR10.spec
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] PyInstaller falhou. Verifique os erros acima.
    pause
    exit /b 1
)

IF NOT EXIST "%BUILD_TMP%\dist\GerLauNR10\GerLauNR10.exe" (
    echo [ERRO] O executavel nao foi gerado.
    pause
    exit /b 1
)

echo [INFO] Copiando o pacote para dist\GerLauNR10 ...
robocopy "%BUILD_TMP%\dist\GerLauNR10" "dist\GerLauNR10" /E /NFL /NDL /NJH /NJS /NP >nul
IF %ERRORLEVEL% GEQ 8 (
    echo [ERRO] Falha ao copiar o pacote para a pasta do projeto.
    pause
    exit /b 1
)

IF NOT EXIST "dist\GerLauNR10\GerLauNR10.exe" (
    echo [ERRO] O executavel nao foi gerado em dist\GerLauNR10\
    pause
    exit /b 1
)
echo [OK] Executavel gerado: dist\GerLauNR10\GerLauNR10.exe

:: ---------------------------------------------------------------
:: 4) Conferencia do conteudo empacotado
:: ---------------------------------------------------------------
echo [INFO] Conferindo arquivos essenciais no pacote...
python verificar_build.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] O pacote esta incompleto. Veja a lista acima.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------
:: 5) Script do Inno Setup
:: ---------------------------------------------------------------
echo [INFO] Gerando script Inno Setup (.iss)...
python generate_iss.py
IF %ERRORLEVEL% NEQ 0 GOTO ISS_FALHOU
echo [OK] Script gerado: GerLauNR10_installer.iss

:: ---------------------------------------------------------------
:: 6) Compilacao do instalador
::    O caminho padrao do Inno Setup tem parenteses ("Program Files
::    (x86)"), que quebram o parser do cmd dentro de blocos IF( ) --
::    por isso o fluxo usa GOTO.
:: ---------------------------------------------------------------
SET "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
IF NOT EXIST "%INNO_PATH%" SET "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
IF NOT EXIST "%INNO_PATH%" GOTO INNO_NAO_ENCONTRADO

echo [INFO] Compilando instalador com Inno Setup...
"%INNO_PATH%" GerLauNR10_installer.iss
IF %ERRORLEVEL% NEQ 0 GOTO INNO_FALHOU
echo [OK] Instalador gerado na pasta Output\
GOTO FIM_ISS

:INNO_FALHOU
echo [ERRO] Inno Setup falhou ao compilar o instalador.
GOTO FIM_ISS

:INNO_NAO_ENCONTRADO
echo [INFO] Inno Setup nao encontrado. Instale em https://jrsoftware.org/isinfo.php
echo        ou abra GerLauNR10_installer.iss no Inno Setup IDE.
GOTO FIM_ISS

:ISS_FALHOU
echo [AVISO] Geracao do .iss falhou. Execute generate_iss.py manualmente.

:FIM_ISS
echo.
echo ============================================================
echo   Build concluido!
echo ============================================================
pause
