@echo off
echo Installing required packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Package installation failed. Check your internet connection or Python installation.
  pause
  exit /b 1
)
echo Starting Smart Invoice Web App...
python run_browser.py
pause
