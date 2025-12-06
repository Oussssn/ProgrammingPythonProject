@echo off
echo Running MIT Courses Spider...
call venv\Scripts\activate.bat
cd scrapy_project
scrapy crawl mit_courses
cd ..
pause

