@echo off
title Student Records Management System (SRMS)
cd /d "%~dp0"
cls
echo ===============================================================================
echo            🎓  STUDENT RECORDS MANAGEMENT SYSTEM (SRMS)  🎓
echo ===============================================================================
echo.
echo   How would you like to run the system?
echo.
echo   [1] 🌐 Interactive Web Dashboard (Modern Browser UI, Charts & Modals)
echo   [2] 💻 Interactive Terminal CLI (Menu-driven Console)
echo   [3] 🧪 Run Automated Security & CRUD Tests
echo   [0] 🚪 Exit
echo.
echo ===============================================================================
set /p choice="Enter your choice [1, 2, 3, or 0]: "

if "%choice%"=="1" (
    cls
    echo Starting Interactive Web Application...
    echo Opening browser at http://127.0.0.1:5000
    python app.py
    goto end
)

if "%choice%"=="2" (
    cls
    python main.py
    goto end
)

if "%choice%"=="3" (
    cls
    echo Running all unit and security test suites...
    python -m unittest discover tests -v
    echo.
    pause
    goto end
)

:end
