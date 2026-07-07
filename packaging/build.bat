@echo off
REM Build the single-file Windows executable (run on Windows).
setlocal
cd /d "%~dp0\.."

python -m pip install --upgrade pyinstaller
python -m PyInstaller --clean --noconfirm packaging\transform.spec
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

echo.
echo Built: dist\TextTransform.exe
echo Double-click it; it opens the app in your browser.
endlocal
