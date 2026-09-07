@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Missing .venv. Create it with: uv venv
    exit /b 1
)

echo Installing build dependencies...
uv pip install --python ".venv\Scripts\python.exe" -r requirements.txt
if errorlevel 1 exit /b 1

echo Building NeonRift.exe...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name NeonRift space_game.py
if errorlevel 1 exit /b 1

if not exist "release" mkdir release
copy /y "dist\NeonRift.exe" "release\NeonRift.exe" >nul

echo.
echo Build complete: %CD%\release\NeonRift.exe
echo Player executable copied to: %CD%\release\NeonRift.exe
endlocal