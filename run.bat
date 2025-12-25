@echo off
REM ClaRA RAG System - Startup Script for Windows

echo Starting ClaRA RAG System...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo WARNING: Please edit .env and add your API keys before running again!
    echo.
    pause
    exit /b 1
)

REM Install/update dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Create necessary directories
if not exist "uploads" mkdir uploads
if not exist "vector_db" mkdir vector_db
if not exist "static" mkdir static

REM Run the application
echo.
echo Starting server...
echo Access the interface at: http://localhost:8000
echo API documentation at: http://localhost:8000/docs
echo.

python main.py
