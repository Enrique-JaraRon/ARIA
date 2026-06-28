@echo off
title ARIA - Controle qualite

echo.
echo ================================================
echo Controle qualite ARIA
echo ================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERREUR : environnement virtuel introuvable.
    echo Chemin attendu : .venv\Scripts\python.exe
    pause
    exit /b 1
)

".venv\Scripts\python.exe" quality_check.py

pause