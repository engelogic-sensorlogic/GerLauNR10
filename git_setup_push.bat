@echo off
echo ================================================
echo  GerLauNR10 - Inicializar e enviar para GitHub
echo ================================================
echo.

cd /d "Z:\Claude\.Claude NR10\GerLauNR10"

echo [1/6] Verificando instalacao do Git...
git --version
if errorlevel 1 (
    echo ERRO: Git nao encontrado. Instale em https://git-scm.com
    pause
    exit /b 1
)

echo.
echo [2/6] Inicializando repositorio local...
git init
git branch -M main

echo.
echo [3/6] Configurando remote...
git remote remove origin 2>nul
git remote add origin https://github.com/engelogic-sensorlogic/GerLauNR10.git

echo.
echo [4/6] Adicionando arquivos...
git add .

echo.
echo [5/6] Criando commit inicial...
git commit -m "feat: versao inicial GerLauNR10 - estrutura completa PyQt6 + PDF"

echo.
echo [6/6] Enviando para GitHub (main)...
git push -u origin main

echo.
echo ================================================
echo  Concluido! Verifique em:
echo  https://github.com/engelogic-sensorlogic/GerLauNR10
echo ================================================
pause
