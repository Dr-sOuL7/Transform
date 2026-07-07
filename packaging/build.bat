@echo off
REM ============================================================
REM  Build the single-file Windows executable.
REM  Self-contained: creates a venv, installs deps, builds.
REM  Just double-click this file (or run it from a terminal).
REM ============================================================
setlocal
cd /d "%~dp0\.."

echo ============================================================
echo   Building Offline Text Transformation for Windows
echo ============================================================
echo.

REM --- 1. Check Python is available -------------------------------------
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found on your PATH.
  echo         Install Python 3.10 or newer from:
  echo             https://www.python.org/downloads/
  echo         During setup, tick "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

REM --- 2. Create a build virtual environment (reused if present) --------
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 ( echo [ERROR] Could not create the virtual environment. & pause & exit /b 1 )
)
set "PY=.venv\Scripts\python.exe"

REM --- 3. Install dependencies + PyInstaller ---------------------------
echo Installing dependencies. This can take a couple of minutes...
"%PY%" -m pip install --upgrade pip >nul
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERROR] Dependency installation failed. & pause & exit /b 1 )

REM --- 4. Build the executable -----------------------------------------
echo.
echo Building executable...
"%PY%" -m PyInstaller --clean --noconfirm packaging\transform.spec
if errorlevel 1 ( echo [ERROR] PyInstaller build failed. & pause & exit /b 1 )

echo.
echo ============================================================
echo   Done!  Your app is:   dist\TextTransform.exe
echo   Double-click it; it opens the app in your browser.
echo   Close the black console window to stop the app.
echo ============================================================
echo.
pause
endlocal
