@echo off
echo MERA Demo Runner
echo ================
echo.
echo This runs 3 self-healing cycles of Main + Mirror agents.
echo.
echo Prerequisites:
echo   1. Ollama running with llama3.2:3b pulled
echo   2. SigNoz deployed via: foundryctl cast -f casting.yaml
echo   3. .env configured (copy from .env.example)
echo.
echo Or just run without SigNoz to see the agents work:
echo   python run.py
echo.
pause
python run.py
pause
