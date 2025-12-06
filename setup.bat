@echo off
echo ====================================
echo University Scraper Project Setup
echo ====================================
echo.

echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [2/4] Installing dependencies...
pip install -r requirements.txt

echo [3/4] Creating database tables...
python -c "from app.database import init_db; init_db(); print('Database initialized successfully!')"

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Edit .env file with your PostgreSQL password
echo 2. Run spiders: cd scrapy_project ^&^& scrapy crawl mit_courses
echo 3. Start API: uvicorn app.main:app --reload
echo.
pause

