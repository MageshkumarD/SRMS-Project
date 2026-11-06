@echo off
title Student Records Management System - Interactive Web Dashboard
cd /d "%~dp0"
echo =====================================================================
echo    Starting SRMS Interactive Web Dashboard...
echo    Opening your web browser automatically at http://127.0.0.1:5000
echo =====================================================================
python app.py
pause
