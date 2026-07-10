@echo off
REM Startar Avvikelserapportering-appen och oppnar den i ett eget app-
REM liknande fonster (utan adressfalt/flikar). Stang bade appfonstret och
REM detta kommandofonster nar du ar klar for att stanga ner servern helt.
cd /d "%~dp0"

set "VENV_DIR=%LOCALAPPDATA%\Avvikelserapportering\venv"

if exist "%VENV_DIR%\Scripts\python.exe" (
    set "PYEXE=%VENV_DIR%\Scripts\python.exe"
) else (
    echo Hittar ingen installerad miljo i %VENV_DIR%.
    echo Kor setup.bat forst ^(bara nodvandigt forsta gangen, eller efter uppdateringar^).
    pause
    exit /b 1
)

REM Kontrollera FORST om alla paket redan finns (snabb, ror inte filsystemet
REM alls). Bara om nagot saknas forsoker vi installera.
"%PYEXE%" -c "import fastapi, uvicorn, multipart" 2>nul
if errorlevel 1 (
    echo Ett eller flera paket saknas - installerar fran requirements.txt ...
    "%PYEXE%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Installationen misslyckades - se felet ovan. Prova att kora
        echo run_app.bat som administrator, eller kontakta support.
        pause
        exit /b 1
    )
)

start "Avvikelserapportering - server (stang detta fonster for att avsluta)" cmd /k ""%PYEXE%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8600"

echo Startar servern, vantar ett par sekunder ...
timeout /t 4 /nobreak >nul

set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"

if exist "%EDGE%" (
    start "" "%EDGE%" --app=http://127.0.0.1:8600 --proxy-bypass-list="127.0.0.1;localhost" --window-size=480,860
) else if exist "%CHROME%" (
    start "" "%CHROME%" --app=http://127.0.0.1:8600 --proxy-bypass-list="127.0.0.1;localhost" --window-size=480,860
) else (
    start "" "http://127.0.0.1:8600"
)

echo.
echo Vill du testa fran din mobiltelefon (samma Wi-Fi som denna dator)?
echo Kor "ipconfig" i en kommandoprompt, leta upp "IPv4-adress" och gao till
echo http://DIN-IP:8600 i mobilens webblasare.
echo.
