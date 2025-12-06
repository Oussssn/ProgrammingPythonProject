# University Course & Professor Scraper - Project Report

## Overview

This project is a backend system that collects university course and professor data from public sources, stores them in a PostgreSQL database, and exposes the data through a REST API. The main goal was to demonstrate web scraping techniques, object-oriented design patterns, and API development.

## What We Built

### Data Sources
- **MIT OpenCourseWare**: 
  - Course information (titles, codes, departments, descriptions)
  - Professor/Instructor data (extracted from course pages)
- **RateMyProfessor**: 
  - Professor profiles and ratings
  - Student reviews (quality ratings, difficulty, comments)

### Tech Stack
- **Scrapy**: Web scraping framework for static HTML pages
- **Selenium**: WebDriver for JavaScript-rendered content
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Database storage
- **FastAPI**: REST API framework
- **Pydantic**: Data validation

## How It Works

### 1. Course Scraping (MIT OCW)

The MIT OpenCourseWare spider uses Scrapy to:
1. Fetch the sitemap from `ocw.mit.edu/sitemap.xml`
2. Extract course URLs from sitemap entries
3. Visit each course page and parse:
   - Course title and code
   - Department information
   - Course description
   - Instructor names (also saved as professors)

This works well because MIT OCW serves static HTML - no JavaScript needed.

### 2. Professor Reviews (RateMyProfessor)

Here's where things got interesting. RateMyProfessor loads all its content via JavaScript after the page loads. Scrapy only fetches the initial HTML, which is basically empty.

**The Problem:**
```
Scrapy request → Gets empty HTML shell → No data to parse
```

**Our Solution:**
We built a separate Selenium-based scraper (`scripts/scrape_ratemyprofessor_selenium.py`) that:
1. Opens a real Chrome browser (headless mode)
2. Navigates to MIT's professor listing page: `https://www.ratemyprofessors.com/search/professors/580?q=*`
3. Clicks "Show More" button multiple times to load all professors (MIT has 452 professors)
4. Waits for JavaScript to load the content
5. Extracts professor URLs from the page
6. For each professor:
   - Visits their profile page
   - Parses the fully-rendered page
   - Extracts professor info (name, department, ratings)
   - Extracts student reviews (rating, difficulty, comments, course name)

**Alternative Search Method:**
If the "Show More" button approach doesn't work, the scraper can also search for professors by name using the URL format:
`https://www.ratemyprofessors.com/search/professors/580?q=PROFESSOR_NAME`

This allows searching for specific professors by name, which is useful when we have instructor names from MIT courses.

### 3. Data Storage

All scraped data goes into PostgreSQL with these tables:
- `courses`: Course information
- `professors`: Professor details
- `reviews`: Student reviews linked to professors
- `course_instructors`: Links courses to their instructors

### 4. REST API

FastAPI exposes the data with these endpoints:

| Endpoint | What it does |
|----------|--------------|
| `GET /api/courses` | List courses (paginated, filterable) |
| `GET /api/courses/{id}` | Get single course |
| `GET /api/professors` | List professors (paginated, filterable) |
| `GET /api/professors/{id}` | Get professor with reviews |
| `GET /api/reviews` | List reviews (paginated, filterable) |

All endpoints support pagination (`page`, `page_size`) and various filters.

## Design Decisions

### Abstract Base Class for Spiders

We created `ScraperBase` as an abstract class that all spiders inherit from:

```python
class ScraperBase(scrapy.Spider, ABC):
    @abstractmethod
    def start_requests(self) -> Generator[Request, None, None]: ...
    
    @abstractmethod
    def parse(self, response: Response) -> Generator[...]: ...
    
    @abstractmethod
    def save(self, item: dict[str, Any]) -> None: ...
```

This enforces a consistent interface across all scrapers.

### Dataclasses for Data Modeling

We use Python dataclasses with validation:

```python
@dataclass
class Course:
    course_id: Optional[str] = None
    title: str = ""
    code: str = ""
    # ... with validation in __post_init__
```

### Why Two Scraping Approaches?

| Site | Content Type | Solution |
|------|--------------|----------|
| MIT OCW | Static HTML | Scrapy (fast, efficient) |
| RateMyProfessor | JavaScript-rendered | Selenium (slower but necessary) |

We tried Scrapy first for RateMyProfessor, but it just couldn't get the data. The site's `robots.txt` also blocks some paths, and even when bypassed, the content isn't in the initial HTML response.

**MIT School ID on RateMyProfessor**: 580 (not 1249 as initially thought)

## Current Stats

After running the scrapers:
- **35 courses** from MIT OCW
- **43 professors** (from both sources)
- **85 reviews** from RateMyProfessor

The scraper can find up to **105+ professor URLs** from MIT's RateMyProfessor page by clicking "Show More" multiple times. MIT has 452 professors total on RateMyProfessor, so the scraper can potentially collect data for all of them.

## Running the Project

### Quick Start
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run MIT course spider
cd scrapy_project
scrapy crawl mit_courses

# Run RateMyProfessor scraper (uses Selenium)
python scripts/scrape_ratemyprofessor_selenium.py

# Start API server
uvicorn app.main:app --reload
```

### API Documentation
Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Challenges We Faced

1. **JavaScript-rendered content**: RateMyProfessor was our biggest challenge. We had to switch from Scrapy to Selenium.

2. **Dynamic selectors**: RateMyProfessor uses CSS classes like `.Rating__StyledRating-sc-1rhvpxz-1` which might change. We added multiple fallback selectors.

3. **Duplicate handling**: Same professor might appear in multiple courses. We added checks to update existing records instead of creating duplicates (based on `rmp_id` or `name` + `university`).

4. **MIT search page**: The search page at `ocw.mit.edu/search/` also uses JavaScript. We solved this by using the sitemap instead.

5. **"Show More" button**: RateMyProfessor uses infinite scroll with a "Show More" button. We had to:
   - Find the button using CSS selector `button[class*='PaginationButton']`
   - Click it multiple times (up to 20 times) to load all professors
   - Wait for content to load after each click
   - Handle Windows console encoding issues (replaced Unicode checkmarks with ASCII)

6. **Windows console encoding**: Windows console couldn't display Unicode characters like `✓`. We replaced them with ASCII equivalents like `[OK]` and `[ERROR]` for better compatibility.

## What Could Be Improved

- Add more error handling and retry logic
- Implement rate limiting more robustly
- Add unit tests for parsers
- Cache responses to avoid re-scraping
- Add more universities/sources
- Optimize "Show More" clicking to load all 452 MIT professors
- Add progress tracking for long-running scrapes
- Implement resume functionality if scraper is interrupted

## File Structure

```
ScraperProject/
├── app/                    # FastAPI application
│   ├── main.py            # API entry point
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   └── routers/           # API endpoints
├── core/                   # Business logic
│   ├── dataclasses.py     # Data models
│   └── validators.py      # Validation logic
├── scrapy_project/         # Scrapy spiders
│   └── spiders/
│       ├── base_scraper.py    # Abstract base class
│       ├── mit_courses.py     # MIT OCW spider
│       └── ratemyprofessor.py # RMP spider (limited)
├── scripts/
│   └── scrape_ratemyprofessor_selenium.py  # Selenium scraper
└── requirements.txt        # Dependencies
```

## Conclusion

The project successfully demonstrates:
- Web scraping with both static and dynamic content
- Object-oriented design with abstract classes and dataclasses
- Database design with SQLAlchemy ORM
- REST API development with FastAPI
- Problem-solving when initial approaches don't work (Scrapy → Selenium)

The main takeaway: not all websites are created equal. Some serve static HTML that's easy to scrape, while others require a browser to render JavaScript. Always check the page source before choosing your scraping approach!

---

*Questions? Check the code comments or ask the team.*

