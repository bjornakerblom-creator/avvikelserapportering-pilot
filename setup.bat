@echo off
REM Forsta gangens installation - kors en gang per dator.
REM
REM Den virtuella miljon (.venv) skapas UTANFOR denna mapp, i
REM %%LOCALAPPDATA%%\Avvikelserapportering\venv. Anledningen: den har mappen
REM ligger i OneDrive, och OneDrive synkar/laser ofta filer samtidigt som
REM Python forsoker skriva de tusentals sma filerna i en venv, vilket ger
REM "Atkomst nekad"-fel. Sjalva koden/appen ligger kvar har som vanligt.
REM (Databasen och uppladdade bilder lagras av samma anledning ocksa i
REM %%LOCALAPPDATA%%\Avvikelserapportering\data, se backend/db.py.)
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python hittades inte. Installera Python 3 fran https://www.python.org/downloads/
    echo och kryssa i "Add python.exe to PATH" under installationen. Kor sedan om detta skript.
    pause
    exit /b 1
)

set "VENV_DIR=%LOCALAPPDATA%\Avvikelserapportering\venv"

echo Skapar virtuell miljo i %VENV_DIR% ...
if exist "%VENV_DIR%" (
    echo Hittade en befintlig miljo - tar bort och skapar om for att undvika gamla fel.
    rmdir /s /q "%VENV_DIR%"
)
python -m venv "%VENV_DIR%"

echo Installerar paket ...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo Klart! Dubbelklicka pa run_app.bat for att starta appen.
pause
