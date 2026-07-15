@echo off
chcp 65001 > nul
echo ================================================
echo  GerLauNR10 - Commit e Push para GitHub
echo ================================================

cd /d "%~dp0"

:: Remove lock se existir
if exist ".git\index.lock" (
    echo Removendo index.lock...
    del /f ".git\index.lock"
)

:: Configura usuario se necessario
git config user.email "engenharia@engelogic.com.br" 2>nul
git config user.name "Engelogic" 2>nul

:: Stage e commit
git add -A
git status

git commit -m "feat: reconstrucao completa pdf_generator + fotos + graficos + fixes UI

- pdf_generator.py: reconstruido do zero (1217 linhas, 60KB)
- Secao 6: fotos restauradas, 4 por linha dentro das margens
- Secao 7: graficos de barras por painel e por item (7.1 tabela, 7.2 pizzas)
- Secao 8: conclusoes, recomendacoes, tabela prioridades, assinaturas
- ui/pdf_widget.py: logo cliente, botao refresh, contraste melhorado
- ui/laudos_widget.py: layout vertical empilhado, colunas ajustadas
- styles.py: card_header cor branca explicita"

echo.
echo Fazendo push para GitHub...
git push origin main

echo.
echo ================================================
if %ERRORLEVEL% == 0 (
    echo  SUCESSO! Codigo enviado para GitHub.
) else (
    echo  Erro no push. Verifique credenciais GitHub.
    echo  Tente: git push origin main
)
echo ================================================
pause
