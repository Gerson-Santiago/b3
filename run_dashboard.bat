@echo off
cd /d "%~dp0"
set PYTHONPATH=%CD%
".venv\Scripts\python.exe" -m streamlit run dashboard/app.py
pause