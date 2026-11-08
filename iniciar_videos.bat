@echo off
title VideoStudio AI - Creador de Videos Cortos (TikTok / Shorts / Reels)
color 0A
echo ========================================================
echo   VIDEOSTUDIO AI (2026)
echo   Estudio de Produccion de Videos Cortos Verticales
echo ========================================================
echo.
cd /d "%~dp0"

powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [1/2] Abriendo navegador en http://localhost:8001...
start "" http://localhost:8001

echo [2/2] Iniciando servidor en http://0.0.0.0:8001 (accesible en localhost y por Tailscale)...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo iniciar el servidor.
    pause
)

