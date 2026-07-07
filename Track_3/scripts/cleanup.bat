@echo off
echo MERA Cleanup
echo =============
echo.
echo This will stop and remove all MERA-related resources.
echo.

set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" exit /b

echo.
echo 1. Stopping Foundry deployment...
foundryctl destroy -f casting.yaml 2>nul && echo    Foundry deployment stopped.

echo.
echo 2. Stopping Docker Compose (if used)...
docker compose -f docker-compose.yml down 2>nul && echo    Docker Compose stopped.

echo.
echo 3. Removing state files...
if exist data\mera_state.json (
    del data\mera_state.json
    echo    State file removed
)

echo.
echo 4. Removing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d"

echo.
echo ================
echo Cleanup complete!
echo ================
echo.
echo To fully reset, also delete .env and data/ folder manually.
pause
