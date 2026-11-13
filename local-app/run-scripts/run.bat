@echo off
setlocal
cd /d "%~dp0\.."

where python >nul 2>nul
if errorlevel 1 (
	where winget >nul 2>nul
	if errorlevel 1 (
		echo Python 3 is required but not installed.
		echo Please install Python 3 and run this again.
		pause
		exit /b 1
	) else (
		winget install -e --id Python.Python.3.12
	)
)

if not exist .venv (
	python -m venv .venv
)

".\.venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
".\.venv\Scripts\python.exe" main.py
pause
