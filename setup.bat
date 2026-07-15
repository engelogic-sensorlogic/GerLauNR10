@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
chcp 65001 >nul

echo ============================================================
echo   GerLauNR10 - Setup e Instalação de Dependências
echo   Engelogic Automação e Controle Industrial
echo ============================================================
echo.

:: Verifica Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python não encontrado. Instale Python 3.10+ em:
    echo        https://www.python.org/downloads/
    pause
    exit /b 1
)

FOR /F "tokens=2 delims= " %%V IN ('python --version 2^>^&1') DO SET PY_VER=%%V
echo [OK] Python encontrado: %PY_VER%

:: Cria pasta de dados
IF NOT EXIST "data" mkdir data
IF NOT EXIST "resources" mkdir resources
echo [OK] Pastas criadas.

:: Atualiza pip
echo.
echo [INFO] Atualizando pip...
python -m pip install --upgrade pip --quiet

:: Instala dependências
echo.
echo [INFO] Instalando dependências...
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao instalar dependências.
    pause
    exit /b 1
)

echo.
echo [OK] Todas as dependências instaladas com sucesso!
echo.

:: Inicializa banco de dados
echo [INFO] Inicializando banco de dados...
python -c "import database; database.init_db(); print('[OK] Banco de dados inicializado.')"
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao inicializar banco de dados.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Setup concluído com sucesso!
echo   Execute: python main.py
echo ============================================================
echo.
pause
