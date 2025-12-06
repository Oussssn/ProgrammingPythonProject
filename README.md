# University Course Scraper Backend

A comprehensive backend system that scrapes university course and professor data from public sources (MIT OpenCourseWare and RateMyProfessor), stores them in PostgreSQL using SQLAlchemy ORM, and exposes the data via a REST API built with FastAPI.

## Features

- **Web Scraping**: 
  - Scrapy spider for MIT OpenCourseWare courses (static HTML)
  - Selenium-based scraper for RateMyProfessor reviews (JavaScript-rendered content)
- **Object-Oriented Design**: Abstract base scraper class with concrete implementations
- **Type Safety**: Full type hints with mypy type checking
- **Database**: PostgreSQL with SQLAlchemy ORM models
- **REST API**: FastAPI endpoints with pagination and filtering
- **Data Validation**: Dataclasses with validation logic

### Note on RateMyProfessor Scraping

RateMyProfessor uses JavaScript to dynamically load content after the initial page load. Scrapy's default HTTP client only fetches static HTML and cannot execute JavaScript. Therefore, we use **Selenium WebDriver** for RateMyProfessor scraping, which can render full pages including JavaScript-generated content.

- **MIT OpenCourseWare**: Uses Scrapy (static HTML, no JavaScript required)
- **RateMyProfessor**: Uses Selenium (JavaScript-rendered content)

## Project Structure

```
ScraperProject/
├── venv/                          # Virtual environment
├── scrapy_project/                # Scrapy project
│   ├── scrapy.cfg
│   └── scrapy_project/
│       ├── items.py               # Scrapy items
│       ├── pipelines.py           # Data processing pipelines
│       ├── settings.py            # Scrapy settings
│       └── spiders/
│           ├── base_scraper.py    # Abstract ScraperBase class
│           ├── mit_courses.py     # MIT OpenCourseWare spider
│           └── ratemyprofessor.py # RateMyProfessor spider
├── app/                           # FastAPI application
│   ├── main.py                    # FastAPI app entry point
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── schemas.py                 # Pydantic schemas for API
│   ├── database.py                # Database connection & session
│   └── routers/
│       ├── courses.py             # /api/courses endpoints
│       ├── professors.py          # /api/professors endpoints
│       └── reviews.py             # /api/reviews endpoints
├── core/                          # Core business logic
│   ├── dataclasses.py             # Course, Professor, Review dataclasses
│   └── validators.py              # Data validation logic
├── requirements.txt               # Python dependencies
├── .mypy.ini                      # Mypy configuration
└── README.md                      # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- PostgreSQL installed and running locally
- Virtual environment (recommended)

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE university_scraper_db;
```

Set up environment variables. Create a `.env` file in the project root:

```
DATABASE_URL=postgresql://username:password@localhost:5432/university_scraper_db
```

Replace `username` and `password` with your PostgreSQL credentials.

### 4. Initialize Database

The database tables will be created automatically when you run the application or spiders. You can also initialize manually:

```python
from app.database import init_db
init_db()
```

## Usage

### Running the Spiders

To scrape data from MIT OpenCourseWare (uses Scrapy):

```bash
cd scrapy_project
scrapy crawl mit_courses
```

To scrape data from RateMyProfessor (uses Selenium - see note below):

```bash
# Install Chrome/Chromium browser first
python scripts/scrape_ratemyprofessor_selenium.py
```

**Note**: The RateMyProfessor spider in `scrapy_project/scrapy_project/spiders/ratemyprofessor.py` uses Scrapy but cannot scrape RateMyProfessor effectively because the site loads content via JavaScript. The working implementation is in `scripts/scrape_ratemyprofessor_selenium.py` which uses Selenium WebDriver to render JavaScript.

### Running the API Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Courses

- `GET /api/courses` - List courses with pagination and filters
  - Query parameters:
    - `page` (int): Page number (default: 1)
    - `page_size` (int): Items per page (default: 10, max: 100)
    - `department` (str, optional): Filter by department
    - `level` (str, optional): Filter by level (e.g., "Undergraduate", "Graduate")
- `GET /api/courses/{course_id}` - Get course details by ID

### Professors

- `GET /api/professors` - List professors with pagination and filters
  - Query parameters:
    - `page` (int): Page number (default: 1)
    - `page_size` (int): Items per page (default: 10, max: 100)
    - `department` (str, optional): Filter by department
    - `university` (str, optional): Filter by university
- `GET /api/professors/{professor_id}` - Get professor details by ID (includes reviews)

### Reviews

- `GET /api/reviews` - List reviews with pagination and filters
  - Query parameters:
    - `page` (int): Page number (default: 1)
    - `page_size` (int): Items per page (default: 10, max: 100)
    - `professor_id` (int, optional): Filter by professor ID
    - `min_rating` (float, optional): Filter by minimum rating (0-5)
- `GET /api/reviews/{review_id}` - Get review details by ID

## Type Checking

Run mypy to check type hints:

```bash
mypy .
```

## Testing

Run the test scripts to populate the database with sample data:

```bash
python scripts/run_spiders.py
```

## Architecture

### Abstract Base Scraper

All spiders inherit from `ScraperBase` which defines:
- `start_requests()`: Initial requests
- `parse()`: Response parsing
- `save()`: Data persistence
- `validate_data()`: Data validation

### Data Flow

1. **Scraping**: Spiders extract data from websites
2. **Validation**: Data is validated using dataclasses
3. **Transformation**: Validated data is converted to ORM models
4. **Persistence**: Data is saved to PostgreSQL
5. **API**: FastAPI exposes data via REST endpoints

## Technologies

- **Scrapy**: Web scraping framework (for static HTML sites like MIT OCW)
- **Selenium**: WebDriver for JavaScript-rendered content (for RateMyProfessor)
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Relational database
- **FastAPI**: Modern web framework for APIs
- **Pydantic**: Data validation
- **mypy**: Static type checking

## Scraping Approach

### MIT OpenCourseWare
- **Method**: Scrapy (static HTML scraping)
- **Why**: MIT OCW serves static HTML that Scrapy can parse directly
- **Spider**: `scrapy_project/scrapy_project/spiders/mit_courses.py`

### RateMyProfessor
- **Method**: Selenium WebDriver (JavaScript rendering)
- **Why**: RateMyProfessor loads content dynamically via JavaScript after page load. Scrapy's HTTP client cannot execute JavaScript, so we use Selenium to render the full page.
- **Script**: `scripts/scrape_ratemyprofessor_selenium.py`
- **Note**: The Scrapy spider (`ratemyprofessor.py`) exists but cannot effectively scrape RateMyProfessor due to JavaScript requirements.
- **MIT School ID**: 580 (URL: `https://www.ratemyprofessors.com/search/professors/580?q=*`)
- **Features**:
  - Clicks "Show More" button multiple times to load all professors (MIT has 452 professors)
  - Can search for specific professors by name: `https://www.ratemyprofessors.com/search/professors/580?q=PROFESSOR_NAME`
  - Extracts professor profiles and student reviews

## License

This project is for educational purposes.

