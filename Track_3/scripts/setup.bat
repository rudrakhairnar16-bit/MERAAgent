@echo off
echo MERA Setup
echo ==========
echo.
pip install -r requirements.txt
if exist .env (
    echo .env exists
) else (
    copy .env.example .env
    echo Created .env - add your OPENAI_API_KEY
)
echo.
echo Setup complete! Run: python run.py
