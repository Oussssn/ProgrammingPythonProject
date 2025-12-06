# Technical Notes

## RateMyProfessor Scraping Approach

### Problem
RateMyProfessor uses JavaScript to dynamically load professor and review content after the initial page load. When you visit a RateMyProfessor page:
1. Initial HTML is served (minimal content)
2. JavaScript executes to fetch and render the actual content
3. Content appears in the DOM

### Solution: Selenium WebDriver
We use Selenium WebDriver to:
1. Launch a real browser (Chrome/Chromium in headless mode)
2. Navigate to MIT's professor listing: `https://www.ratemyprofessors.com/search/professors/580?q=*`
3. Click "Show More" button multiple times (up to 20 times) to load all professors
4. Wait for JavaScript to execute and content to load
5. Extract professor URLs from the fully-rendered page
6. For each professor, visit their profile and extract:
   - Professor information (name, department, ratings)
   - Student reviews (rating, difficulty, comments, course name)

### MIT School ID
- **MIT School ID on RateMyProfessor**: 580
- **URL Format**: `https://www.ratemyprofessors.com/search/professors/580?q=*` (all professors)
- **Search by Name**: `https://www.ratemyprofessors.com/search/professors/580?q=PROFESSOR_NAME`

### "Show More" Button Implementation
- **Selector**: `button[class*='PaginationButton']`
- **Strategy**: 
  - Find button with "Show More" text
  - Scroll to button
  - Click using JavaScript (more reliable than regular click)
  - Wait 4 seconds for content to load
  - Repeat until no more button found
- **Result**: Can load up to 105+ professors per run (MIT has 452 total)

### Alternative Search Method
If "Show More" doesn't work, the scraper can search for professors by name using instructor names from MIT courses. This allows finding specific professors even if the listing page doesn't load properly.

### Alternative Approaches Considered
1. **Scrapy-Splash**: Could work but requires additional service setup
2. **Playwright**: Similar to Selenium, modern alternative
3. **API**: RateMyProfessor does not provide a public API
4. **Headless Browser**: Selenium with headless Chrome (current approach)

### Windows Console Encoding
Windows console cannot display Unicode characters like `✓`. We replaced them with ASCII equivalents:
- `✓` → `[OK]`
- `✗` → `[ERROR]`

## MIT OpenCourseWare Scraping

MIT OCW serves static HTML, making it perfect for Scrapy:
- No JavaScript required for basic content
- Fast and efficient scraping
- Uses sitemap for course discovery
- Extracts both courses and instructors (professors)

