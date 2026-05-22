@echo off
REM ============================================================================
REM  Visual Field Labeling Tool - launcher
REM  Double-click this file to start. No manual Python install needed.
REM  The first run downloads Python and the required packages automatically
REM  (a few minutes, needs internet once). Later runs start in seconds.
REM ============================================================================
setlocal
cd /d "%~dp0"

REM Use the uv.exe bundled in this folder if present, otherwise a system uv.
set "UV=uv"
if exist "%~dp0uv.exe" set "UV=%~dp0uv.exe"

where %UV% >nul 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: uv was not found.
    echo Make sure "uv.exe" is in this folder, or install uv from https://astral.sh/uv
    echo.
    pause
    exit /b 1
)

echo Starting the Visual Field Labeling Tool...
echo (Keep this window open while you work. Close it to stop the app.)
echo.

%UV% run --native-tls streamlit run app.py

echo.
echo The app has stopped.
pause
