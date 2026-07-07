@echo off
echo MERA Setup
echo ==========
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
echo.
echo Installing optional terminal dashboard...
pip install rich 2>nul
echo.
if exist .env (
    echo .env already exists
) else (
    copy .env.example .env
    echo Created .env from .env.example
    echo Open .env to verify Ollama settings (defaults should work)
)
echo.
echo ================
echo Setup complete!
echo ================
echo.
echo Quick start:
echo   1. Ensure Ollama is running with: ollama serve
echo   2. Ensure llama3.2:3b is pulled: ollama pull llama3.2:3b
echo   3. Deploy SigNoz: foundryctl cast -f casting.yaml
echo   4. Run MERA:   python run.py
echo   5. Dashboard:  http://localhost:9000
echo   6. SigNoz:     http://localhost:8080
echo.
pause
