@echo off
echo Running RateMyProfessor Spider...
call venv\Scripts\activate.bat
cd scrapy_project
scrapy crawl ratemyprofessor
cd ..
pause

