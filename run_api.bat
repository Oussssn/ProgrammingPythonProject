@echo off
echo Starting API Server...
call venv\Scripts\activate.bat
uvicorn app.main:app --reload

