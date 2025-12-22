@echo off
echo ========================================
echo Scale Weight Server - EXE Builder
echo ========================================
echo.

echo [1/4] Installing PyInstaller...
pip install pyinstaller

echo.
echo [2/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo [3/4] Building EXE file...
pyinstaller --clean --onefile --windowed --name "ScaleWeightServer" --exclude-module pkg_resources --hidden-import=flask --hidden-import=werkzeug --hidden-import=jinja2 --hidden-import=click --hidden-import=itsdangerous --hidden-import=serial --hidden-import=serial.tools.list_ports --hidden-import=pystray --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageDraw --collect-all pystray ScaleWeightServer.py

echo.
echo [4/4] Build complete!
echo.
echo ========================================
echo Your EXE file is ready in the 'dist' folder
echo File: dist\ScaleWeightServer.exe
echo ========================================
echo.
pause
