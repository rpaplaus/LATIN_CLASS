@echo off
cd /d "C:\Users\rpapl\.gemini\antigravity-ide\scratch\LATIN_CLASS"

echo Subindo todos os containers do Latin Class em background...
docker compose up -d

echo.
echo Aguardando o banco de dados iniciar para aplicar as migracoes...
timeout /t 5 /nobreak >nul

echo Executando Alembic dentro do container...
docker compose exec backend alembic upgrade head

echo.
echo Tudo pronto! O Latin Class esta rodando silenciosamente via Docker.
echo Frontend: http://localhost:3001
echo Backend:  http://localhost:8001
echo.
echo Voce ja pode fechar esta janela.
pause