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
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name NeonRift test.py
if errorlevel 1 exit /b 1

echo Building NeonRiftServer.exe...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --name NeonRiftServer server.py
if errorlevel 1 exit /b 1

if not exist "release" mkdir release
copy /y "dist\NeonRift.exe" "release\NeonRift.exe" >nul
if not exist "server-release" mkdir server-release
copy /y "dist\NeonRiftServer.exe" "server-release\NeonRiftServer.exe" >nul

echo.
echo Build complete: %CD%\release\NeonRift.exe
echo Player ZIP contents: NeonRift.exe and README.txt
echo Server executable: %CD%\server-release\NeonRiftServer.exe
endlocal