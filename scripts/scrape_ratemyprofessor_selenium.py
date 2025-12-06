"""Selenium-based scraper for RateMyProfessor reviews.

Note: RateMyProfessor uses JavaScript to dynamically load content, which Scrapy's
default HTTP client cannot execute. This script uses Selenium WebDriver to render
JavaScript and extract professor and review data.

Why Selenium instead of Scrapy?
- RateMyProfessor loads content via JavaScript after page load
- Scrapy only fetches static HTML, cannot execute JavaScript
- Selenium WebDriver can render full pages including JavaScript-generated content
"""
import sys
import time
from pathlib import Path
from typing import Any
import re
from datetime import datetime
from urllib.parse import urljoin

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from app.database import SessionLocal, init_db
from app.models import Professor, Review
from core.validators import validate_professor_data, validate_review_data


class RateMyProfessorSeleniumScraper:
    """Selenium-based scraper for RateMyProfessor."""
    
    def __init__(self, headless: bool = True):
        """Initialize the scraper with Chrome WebDriver.
        
        Args:
            headless: Run browser in headless mode (no GUI).
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.db = SessionLocal()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        self.db.close()
    
    def search_professor_by_name(self, professor_name: str, school_id: int = 580) -> str | None:
        """Search for a specific professor by name at a school.
        
        Args:
            professor_name: Name of the professor to search for.
            school_id: RateMyProfessor school ID (580 for MIT).
            
        Returns:
            Professor profile URL if found, None otherwise.
        """
        # URL format: https://www.ratemyprofessors.com/search/professors/580?q=PROFESSOR_NAME
        from urllib.parse import quote
        search_url = f"https://www.ratemyprofessors.com/search/professors/{school_id}?q={quote(professor_name)}"
        
        print(f"    Searching for: {professor_name}")
        print(f"    URL: {search_url}")
        
        try:
            self.driver.get(search_url)
            time.sleep(3)
            print(f"    Page loaded, looking for professor links...")
            
            # Look for professor link in search results
            # The first result should be the professor if found
            selectors = [
                "a[href*='/professor/']",
                ".TeacherCard__StyledTeacherCard a",
                "[class*='TeacherCard'] a"
            ]
            
            all_links_found = []
            for selector in selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"    Selector '{selector}': found {len(links)} links")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and "/professor/" in href:
                            link_text = link.text.strip()
                            all_links_found.append((href, link_text))
                            # Check if the link text contains the professor name
                            name_parts = professor_name.lower().split()
                            if any(part in link_text.lower() for part in name_parts if len(part) > 2):
                                print(f"    [OK] Found match: {link_text} -> {href}")
                                return href
                except Exception as e:
                    print(f"    [ERROR] Error with selector '{selector}': {e}")
                    continue
            
            if all_links_found:
                print(f"    Found {len(all_links_found)} professor links but no name match")
                print(f"    First link: {all_links_found[0][1]} -> {all_links_found[0][0]}")
            else:
                        print(f"    [ERROR] No professor links found")
            
            return None
            
        except Exception as e:
            print(f"    [ERROR] Error searching for professor {professor_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def search_professors(self, university: str = "Massachusetts Institute of Technology") -> list[str]:
        """Search for professors at a university.
        
        Args:
            university: University name to search for.
            
        Returns:
            List of professor profile URLs.
        """
        # MIT's RateMyProfessor school ID is 580
        # Direct URL to MIT professors page with all professors
        if "MIT" in university.upper() or "Massachusetts" in university:
            # MIT school ID: 580 - this URL shows all 452 professors
            professors_url = "https://www.ratemyprofessors.com/search/professors/580?q=*"
            print(f"Using direct MIT professors URL: {professors_url}")
            self.driver.get(professors_url)
            time.sleep(5)
        else:
            # For other universities, search first
            search_url = f"https://www.ratemyprofessors.com/search.jsp?query={university.replace(' ', '+')}"
            self.driver.get(search_url)
            time.sleep(5)
            
            # Try to find and click on the university link
            school_url = None
            try:
                school_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/school']")
                for link in school_links:
                    link_text = link.text.strip()
                    if university.split()[0].upper() in link_text.upper():
                        school_url = link.get_attribute("href")
                        break
                
                if school_url:
                    professors_url = school_url.rstrip("/") + "/professors"
                    self.driver.get(professors_url)
                    time.sleep(5)
            except Exception as e:
                print(f"Could not navigate to school page: {e}")
        
        professor_urls = []
        try:
            # Wait longer for page to fully load
            print("Waiting for page to load...")
            time.sleep(5)
            
            # Click "Show More" button to load more professors
            print("Loading more professors by clicking 'Show More'...")
            click_attempts = 0
            max_clicks = 20  # More clicks to get all 452 professors
            
            while click_attempts < max_clicks:
                try:
                    # Wait a bit for page to be ready
                    time.sleep(2)
                    print(f"  Attempt {click_attempts + 1}/{max_clicks}: Looking for 'Show More' button...")
                    
                    # Method 1: Use CSS selector that we know works (from test)
                    clicked = False
                    try:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[class*='PaginationButton']")
                        print(f"    Found {len(buttons)} buttons with 'PaginationButton' class")
                        for btn in buttons:
                            try:
                                btn_text = btn.text.strip().lower()
                                print(f"    Button text: '{btn_text}'")
                                if "show more" in btn_text:
                                    is_displayed = btn.is_displayed()
                                    is_enabled = btn.is_enabled()
                                    print(f"    Button state: displayed={is_displayed}, enabled={is_enabled}")
                                    # Check if button is visible and enabled
                                    if is_displayed and is_enabled:
                                        # Scroll to button
                                        print(f"    Scrolling to button...")
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                        time.sleep(1)
                                        # Click using JavaScript (more reliable)
                                        print(f"    Clicking button...")
                                        self.driver.execute_script("arguments[0].click();", btn)
                                        time.sleep(4)  # Wait for new professors to load
                                        clicked = True
                                        click_attempts += 1
                                        print(f"  [OK] Clicked 'Show More' ({click_attempts}/{max_clicks})")
                                        break
                                    else:
                                        print(f"    Button not clickable (displayed={is_displayed}, enabled={is_enabled})")
                            except Exception as e:
                                print(f"    Error processing button: {e}")
                                continue
                    except Exception as e:
                        print(f"  [ERROR] Error finding PaginationButton: {e}")
                    
                    # Method 2: Fallback - try all buttons
                    if not clicked:
                        try:
                            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                            print(f"    Fallback: Found {len(all_buttons)} total buttons")
                            show_more_buttons = [btn for btn in all_buttons if "show more" in btn.text.strip().lower()]
                            print(f"    Found {len(show_more_buttons)} buttons with 'Show More' text")
                            for btn in show_more_buttons:
                                try:
                                    if btn.is_displayed() and btn.is_enabled():
                                        print(f"    Clicking fallback button...")
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                        time.sleep(1)
                                        self.driver.execute_script("arguments[0].click();", btn)
                                        time.sleep(4)
                                        clicked = True
                                        click_attempts += 1
                                        print(f"  [OK] Clicked 'Show More' via fallback ({click_attempts}/{max_clicks})")
                                        break
                                except Exception as e:
                                    print(f"    Error clicking fallback button: {e}")
                                    continue
                        except Exception as e:
                            print(f"  [ERROR] Error in fallback: {e}")
                    
                    if not clicked:
                        # No more "Show More" button found
                        print(f"  [INFO] No more 'Show More' button found after {click_attempts} clicks")
                        break
                        
                except Exception as e:
                    print(f"  [ERROR] Error in click loop: {e}")
                    import traceback
                    traceback.print_exc()
                    break
            
            # Try multiple selectors for professor links
            print("Extracting professor URLs from page...")
            selectors = [
                "a[href*='/professor/']",  # New URL format
                "a[href*='/ShowRatings.jsp']",
                ".TeacherCard__StyledTeacherCard a",
                "[class*='TeacherCard'] a",
                "a[href*='tid=']"
            ]
            
            for selector in selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"  Selector '{selector}': found {len(links)} links")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and ("/professor/" in href or "/ShowRatings.jsp" in href or "tid=" in href):
                            # Normalize URL
                            if "/professor/" in href:
                                if href not in professor_urls:
                                    professor_urls.append(href)
                                    print(f"    Added: {href}")
                except Exception as e:
                    print(f"  ✗ Error with selector '{selector}': {e}")
                    continue
            
            # Also try to find all links with professor in href
            if not professor_urls:
                print("  Trying fallback: all links with '/professor/' in href...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"    Found {len(all_links)} total links")
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and "/professor/" in href:
                        if href not in professor_urls:
                            professor_urls.append(href)
                            print(f"    Added: {href}")
            
            print(f"[OK] Found {len(professor_urls)} total professor URLs")
            
        except Exception as e:
            print(f"Error finding professor links: {e}")
        
        return professor_urls
    
    def scrape_professor(self, url: str, max_reviews: int = 10) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Scrape a single professor's profile and reviews.
        
        Args:
            url: Professor profile URL.
            max_reviews: Maximum number of reviews to scrape.
            
        Returns:
            Tuple of (professor_data, reviews_data).
        """
        self.driver.get(url)
        time.sleep(5)  # Wait longer for JavaScript to load reviews
        
        # Save page source for debugging if no reviews found
        page_saved = False
        
        professor_data = None
        reviews_data = []
        
        try:
            # Extract professor name
            name_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.nameTitle, h1, .NameTitle")
            name = name_elem.text.strip() if name_elem else ""
            
            # Extract RMP ID from URL
            # Format can be: /professor/175057 or ?tid=175057
            rmp_id = None
            tid_match = re.search(r"tid=(\d+)", url)
            if tid_match:
                rmp_id = tid_match.group(1)
            else:
                # Try /professor/ID format
                prof_match = re.search(r"/professor/(\d+)", url)
                if prof_match:
                    rmp_id = prof_match.group(1)
            
            # Extract department and university - try multiple selectors
            department = ""
            university = ""
            school_selectors = [
                ".School",
                ".school",
                "[data-testid='school-name']",
                ".professor-school",
                "a[href*='/school']"
            ]
            for selector in school_selectors:
                try:
                    school_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    school_text = school_elem.text.strip()
                    # Format: "Department, University" or just "University"
                    if "," in school_text:
                        parts = school_text.split(",")
                        department = parts[0].strip()
                        university = parts[1].strip() if len(parts) > 1 else ""
                    else:
                        university = school_text
                    if university:
                        break
                except:
                    continue
            
            # If no university found, default to MIT
            if not university:
                university = "MIT"
            
            # Extract average rating - try multiple selectors
            avg_rating = None
            rating_selectors = [
                ".RatingValue",
                ".rating",
                "[data-testid='overall-rating']",
                ".overall-rating",
                ".Rating"
            ]
            for selector in rating_selectors:
                try:
                    rating_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r"(\d+\.?\d*)", rating_text)
                    if rating_match:
                        avg_rating = float(rating_match.group(1))
                        if avg_rating:
                            break
                except:
                    continue
            
            # Extract total ratings
            total_ratings = 0
            try:
                count_elem = self.driver.find_element(By.CSS_SELECTOR, ".RatingCount, .rating-count")
                count_text = count_elem.text.strip()
                count_match = re.search(r"(\d+)", count_text)
                if count_match:
                    total_ratings = int(count_match.group(1))
            except:
                pass
            
            # Debug: print what we found
            print(f"  Name: {name}, RMP ID: {rmp_id}, University: {university}")
            
            if name and rmp_id:
                professor_data = {
                    "professor_id": rmp_id,
                    "name": name,
                    "department": department,
                    "university": university,
                    "rmp_id": rmp_id,
                    "average_rating": avg_rating,
                    "total_ratings": total_ratings
                }
            else:
                print(f"  WARNING: Missing name or RMP ID. Name: '{name}', RMP ID: '{rmp_id}'")
            
            # Extract reviews - try multiple selectors
            review_elements = []
            review_selectors = [
                ".Rating__StyledRating-sc-1rhvpxz-1",  # Main review container
                "li .Rating__StyledRating-sc-1rhvpxz-1",  # Review in list
                ".Rating__RatingBody-sc-1rhvpxz-0",  # Review body
                "[class*='Rating__StyledRating']",  # Any rating styled element
                ".Review",
                ".review",
                "tr.review"
            ]
            for selector in review_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        review_elements = elements[:max_reviews]
                        print(f"  Found {len(review_elements)} reviews using selector: {selector}")
                        break
                except:
                    continue
            
            if not review_elements:
                print(f"  No reviews found with standard selectors, trying alternative approach...")
                # Save page for debugging
                if not page_saved:
                    with open(f"rmp_professor_{rmp_id}.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print(f"  Saved page source to rmp_professor_{rmp_id}.html")
                    page_saved = True
                
                # Try to find any review-like elements
                all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                for div in all_divs:
                    div_class = div.get_attribute("class") or ""
                    if "review" in div_class.lower() or "rating" in div_class.lower():
                        review_elements.append(div)
                        if len(review_elements) >= max_reviews:
                            break
                
                # Also try to scroll down to load more reviews
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    # Try selectors again after scroll
                    for selector in review_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                review_elements = elements[:max_reviews]
                                break
                        except:
                            continue
                except:
                    pass
            
            print(f"  Processing {len(review_elements)} review elements")
            for review_elem in review_elements:
                review_data = self._parse_review(review_elem, rmp_id)
                if review_data:
                    reviews_data.append(review_data)
                    print(f"    Parsed review: {review_data.get('rating', 'N/A')}/5.0")
                    
        except Exception as e:
            print(f"Error scraping professor {url}: {e}")
        
        return professor_data, reviews_data
    
    def _parse_review(self, review_elem: Any, professor_rmp_id: str | None) -> dict[str, Any] | None:
        """Parse a single review element.
        
        Args:
            review_elem: Selenium WebElement for the review.
            professor_rmp_id: RMP ID of the professor.
            
        Returns:
            Review data dictionary or None.
        """
        try:
            # Extract rating - RateMyProfessor uses CardNumRating
            rating = 0.0
            rating_selectors = [
                ".CardNumRating__CardNumRatingNumber-sc-17t4b9u-2",  # Rating number
                "[class*='CardNumRating'] .CardNumRating__CardNumRatingNumber",
                ".RatingValues .CardNumRating__CardNumRatingNumber",
                ".Rating, .rating, .star"
            ]
            for selector in rating_selectors:
                try:
                    rating_elem = review_elem.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r"(\d+\.?\d*)", rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                        if rating > 0:
                            break
                except:
                    continue
            
            # Extract difficulty - also uses CardNumRating
            difficulty = None
            try:
                # Find all CardNumRating elements, second one is usually difficulty
                rating_containers = review_elem.find_elements(By.CSS_SELECTOR, ".RatingValues__RatingContainer-sc-6dc747-1")
                if len(rating_containers) >= 2:
                    # Second container is difficulty
                    diff_elem = rating_containers[1].find_element(By.CSS_SELECTOR, ".CardNumRating__CardNumRatingNumber-sc-17t4b9u-2")
                    diff_text = diff_elem.text.strip()
                    diff_match = re.search(r"(\d+\.?\d*)", diff_text)
                    if diff_match:
                        difficulty = float(diff_match.group(1))
            except:
                pass
            
            # Extract would take again - RateMyProfessor uses MetaItem
            would_take_again = None
            try:
                # Look for "Would Take Again" in MetaItem
                meta_items = review_elem.find_elements(By.CSS_SELECTOR, ".MetaItem__StyledMetaItem-y0ixml-0")
                for item in meta_items:
                    item_text = item.text.strip().lower()
                    if "would take again" in item_text:
                        would_take_again = "yes" in item_text
                        break
            except:
                pass
            
            # Extract review text - RateMyProfessor uses Comments__StyledComments
            text = ""
            text_selectors = [
                ".Comments__StyledComments-dzzyvm-0",
                "[class*='Comments__StyledComments']",
                ".Comments, .comment, .review-text"
            ]
            for selector in text_selectors:
                try:
                    text_elem = review_elem.find_element(By.CSS_SELECTOR, selector)
                    text = text_elem.text.strip()
                    if text:
                        break
                except:
                    continue
            
            # Extract date - RateMyProfessor uses TimeStamp
            date = None
            try:
                date_elem = review_elem.find_element(By.CSS_SELECTOR, ".TimeStamp__StyledTimeStamp-sc-9q2r30-0")
                date_text = date_elem.text.strip()
                # RateMyProfessor format: "Dec 5th, 2025" or "Dec 5, 2025"
                # Clean up ordinal suffixes (th, st, nd, rd)
                date_text = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_text)
                # Try various date formats
                for fmt in ["%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d"]:
                    try:
                        date = datetime.strptime(date_text, fmt)
                        break
                    except ValueError:
                        continue
            except:
                pass
            
            # Extract course name - RateMyProfessor uses RatingHeader__StyledClass
            course_name = ""
            course_selectors = [
                ".RatingHeader__StyledClass-sc-1dlkqw1-3",
                "[class*='RatingHeader__StyledClass']",
                ".Course, .course"
            ]
            for selector in course_selectors:
                try:
                    course_elem = review_elem.find_element(By.CSS_SELECTOR, selector)
                    course_text = course_elem.text.strip()
                    # Remove icon text if present
                    course_name = re.sub(r'<!--.*?-->', '', course_text).strip()
                    if course_name:
                        break
                except:
                    continue
            
            # Try to get rating from different sources if not found
            if rating == 0.0:
                # Try to find stars or rating indicators
                try:
                    stars = review_elem.find_elements(By.CSS_SELECTOR, ".star, [class*='star'], [class*='Star']")
                    if stars:
                        # Count filled stars
                        filled = sum(1 for star in stars if "filled" in (star.get_attribute("class") or "").lower())
                        if filled > 0:
                            rating = float(filled)
                except:
                    pass
            
            # Return review if we have at least text or rating
            if rating > 0 or text:
                return {
                    "review_id": None,
                    "professor_id": professor_rmp_id,
                    "rating": rating if rating > 0 else 3.0,  # Default rating if not found
                    "difficulty": difficulty,
                    "would_take_again": would_take_again,
                    "text": text,
                    "date": date,
                    "course_name": course_name
                }
        except Exception as e:
            print(f"    Error parsing review: {e}")
        
        return None
    
    def save_to_database(self, professor_data: dict[str, Any], reviews_data: list[dict[str, Any]]) -> None:
        """Save professor and reviews to database.
        
        Args:
            professor_data: Professor data dictionary.
            reviews_data: List of review data dictionaries.
        """
        try:
            # Validate and save professor
            if professor_data:
                prof_validated = validate_professor_data(professor_data)
                
                # Check if professor exists
                existing_prof = self.db.query(Professor).filter(
                    Professor.rmp_id == prof_validated.rmp_id
                ).first()
                
                if existing_prof:
                    # Update existing
                    existing_prof.name = prof_validated.name
                    existing_prof.department = prof_validated.department
                    existing_prof.university = prof_validated.university
                    existing_prof.average_rating = prof_validated.average_rating
                    existing_prof.total_ratings = prof_validated.total_ratings
                    professor = existing_prof
                else:
                    # Create new
                    professor = Professor(
                        name=prof_validated.name,
                        department=prof_validated.department,
                        university=prof_validated.university,
                        rmp_id=prof_validated.rmp_id,
                        average_rating=prof_validated.average_rating,
                        total_ratings=prof_validated.total_ratings
                    )
                    self.db.add(professor)
                
                self.db.commit()
                self.db.refresh(professor)
                print(f"Saved professor: {professor.name}")
                
                # Save reviews
                for review_data in reviews_data:
                    review_validated = validate_review_data(review_data)
                    
                    # Find professor by RMP ID
                    prof = self.db.query(Professor).filter(
                        Professor.rmp_id == review_validated.professor_id
                    ).first()
                    
                    if prof:
                        review = Review(
                            professor_id=prof.id,
                            rating=review_validated.rating,
                            difficulty=review_validated.difficulty,
                            would_take_again=review_validated.would_take_again,
                            text=review_validated.text,
                            date=review_validated.date,
                            course_name=review_validated.course_name
                        )
                        self.db.add(review)
                        print(f"  Saved review: {review.rating}/5.0")
                
                self.db.commit()
                
        except Exception as e:
            self.db.rollback()
            print(f"Error saving to database: {e}")
            raise


def main():
    """Main function to run the scraper."""
    print("RateMyProfessor Selenium Scraper")
    print("=" * 50)
    print("Note: This scraper uses Selenium because RateMyProfessor")
    print("loads content via JavaScript, which Scrapy cannot execute.")
    print("=" * 50)
    
    init_db()
    
    university = "Massachusetts Institute of Technology"
    max_professors = 10  # Start with fewer for testing
    max_reviews_per_professor = 5  # Fewer reviews per professor for testing
    
    print(f"Max professors to scrape: {max_professors}")
    print(f"Max reviews per professor: {max_reviews_per_professor}")
    
    # Use headless mode for production
    with RateMyProfessorSeleniumScraper(headless=True) as scraper:
        print(f"\nSearching for professors at {university}...")
        professor_urls = scraper.search_professors(university)
        
        print(f"Found {len(professor_urls)} professors from search")
        
        # Alternative: Search by professor names from database
        if len(professor_urls) < 10:
            print("\nTrying alternative: searching by professor names from MIT courses...")
            from app.database import SessionLocal
            from app.models import CourseInstructor, Course
            db = SessionLocal()
            try:
                # Get unique instructor names from MIT courses
                # Note: Course model doesn't have university field, so we'll get all instructors
                instructors = db.query(CourseInstructor.instructor_name).filter(
                    CourseInstructor.instructor_name.isnot(None),
                    CourseInstructor.instructor_name != ""
                ).distinct().limit(30).all()
                
                instructor_names = [inst[0] for inst in instructors if inst[0]]
                print(f"Found {len(instructor_names)} instructor names from MIT courses")
                
                for name in instructor_names[:max_professors]:
                    if name and len(name.strip()) > 2:
                        prof_url = scraper.search_professor_by_name(name.strip(), school_id=580)
                        if prof_url and prof_url not in professor_urls:
                            professor_urls.append(prof_url)
                            print(f"  Found: {name} -> {prof_url}")
                        time.sleep(1)  # Be polite
                
                print(f"Total professors found: {len(professor_urls)}")
            finally:
                db.close()
        
        # If no professors found from search, try known MIT professor URLs
        if not professor_urls and ("MIT" in university.upper() or "MASSACHUSETTS" in university.upper()):
            print("No professors found from search, using known MIT professor URLs...")
            # Known MIT professor RMP IDs with good review counts
            known_mit_professors = [
                "https://www.ratemyprofessors.com/professor/800239",   # Gilbert Strang - Math
                "https://www.ratemyprofessors.com/professor/334553",   # Denis Auroux - Math
                "https://www.ratemyprofessors.com/professor/81483",    # Donald Sadoway - Materials Science
                "https://www.ratemyprofessors.com/professor/1665093",  # Robert Gallager - EECS
                "https://www.ratemyprofessors.com/professor/1056912",  # Patrick Winston - EECS/AI
                "https://www.ratemyprofessors.com/professor/180633",   # Eric Lander - Biology
                "https://www.ratemyprofessors.com/professor/97981",    # Walter Lewin - Physics
                "https://www.ratemyprofessors.com/professor/2115704",  # David Jerison - Math
                "https://www.ratemyprofessors.com/professor/1665068",  # Tomás Lozano-Pérez - EECS
                "https://www.ratemyprofessors.com/professor/1056926",  # Hal Abelson - EECS
            ]
            professor_urls = known_mit_professors[:max_professors]
        
        # Fallback if still no URLs
        if not professor_urls:
            print("Using fallback professor URLs...")
            professor_urls = [
                "https://www.ratemyprofessors.com/professor/800239",  # Gilbert Strang (MIT)
            ]
        
        if professor_urls:
            for i, url in enumerate(professor_urls[:max_professors], 1):
                print(f"\n[{i}/{min(max_professors, len(professor_urls))}] Scraping: {url}")
                professor_data, reviews_data = scraper.scrape_professor(url, max_reviews_per_professor)
                
                if professor_data:
                    scraper.save_to_database(professor_data, reviews_data)
                    print(f"  Scraped {len(reviews_data)} reviews")
                
                time.sleep(2)  # Be respectful with delays
        else:
            print("No professor URLs found to scrape.")
    
    print("\nScraping completed!")


if __name__ == "__main__":
    main()

