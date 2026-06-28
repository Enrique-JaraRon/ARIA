@echo off
title ARIA - Lancement Streamlit

echo.
echo ================================================
echo Lancement de ARIA
echo ================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERREUR : environnement virtuel introuvable.
    echo Chemin attendu : .venv\Scripts\python.exe
    pause
    exit /b 1
)

".venv\Scripts\python.exe" run_aria.py

pause