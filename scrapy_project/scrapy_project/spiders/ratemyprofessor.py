"""Spider for scraping RateMyProfessor data.

NOTE: This Scrapy spider cannot effectively scrape RateMyProfessor because the site
uses JavaScript to dynamically load content. Scrapy's HTTP client only fetches static
HTML and cannot execute JavaScript.

For working RateMyProfessor scraping, use the Selenium-based script:
    scripts/scrape_ratemyprofessor_selenium.py

This spider is kept for reference and structure, but the Selenium implementation
is the recommended approach for RateMyProfessor.
"""
from typing import Any, Generator
import re
from urllib.parse import urljoin, quote
from datetime import datetime
import scrapy
from scrapy.http import Request, Response
from scrapy_project.spiders.base_scraper import ScraperBase
from scrapy_project.items import ProfessorItem, ReviewItem


class RateMyProfessorSpider(ScraperBase):
    """Spider to scrape professor and review data from RateMyProfessor.
    
    WARNING: This spider cannot effectively scrape RateMyProfessor due to JavaScript
    requirements. Use scripts/scrape_ratemyprofessor_selenium.py instead.
    """
    
    name = "ratemyprofessor"
    allowed_domains = ["ratemyprofessors.com", "www.ratemyprofessors.com"]
    
    # Start with a search for a popular university (MIT as example)
    start_urls = ["https://www.ratemyprofessors.com/search.jsp?query=MIT"]
    
    def start_requests(self) -> Generator[Request, None, None]:
        """Start requests from search page."""
        # Search for professors at MIT
        search_url = "https://www.ratemyprofessors.com/search.jsp?query=Massachusetts+Institute+of+Technology"
        yield Request(url=search_url, callback=self.parse_search_results)
    
    def parse(self, response: Response) -> Generator[Request | dict[str, Any], None, None]:
        """Parse method required by base class."""
        yield from self.parse_search_results(response)
    
    def parse_search_results(self, response: Response) -> Generator[Request | dict[str, Any], None, None]:
        """Parse search results page for professor links."""
        # RateMyProfessor uses dynamic content, so we'll look for professor links
        # The actual structure may vary, but we'll try common patterns
        
        # Look for professor profile links
        professor_links = response.css("a[href*='/ShowRatings.jsp']::attr(href)").getall()
        
        for link in professor_links:
            full_url = urljoin(response.url, link)
            yield Request(url=full_url, callback=self.parse_professor_detail)
        
        # Also try alternative selectors
        alt_links = response.css("a::attr(href)").getall()
        for link in alt_links:
            if "/ShowRatings.jsp" in link or "/professor" in link.lower():
                full_url = urljoin(response.url, link)
                yield Request(url=full_url, callback=self.parse_professor_detail)
    
    def parse_professor_detail(self, response: Response) -> Generator[Request | dict[str, Any], None, None]:
        """Parse individual professor detail page."""
        # Extract professor name
        name_elem = response.css("h1.nameTitle::text, h1::text, div.name::text").get()
        name = name_elem.strip() if name_elem else ""
        
        # Extract RMP ID from URL
        rmp_id = None
        tid_match = re.search(r"tid=(\d+)", response.url)
        if tid_match:
            rmp_id = tid_match.group(1)
        
        # Extract department
        department = ""
        dept_elem = response.css("div.school::text, span.department::text").get()
        if dept_elem:
            department = dept_elem.strip()
        
        # Extract university
        university = ""
        uni_elem = response.css("div.school::text, a.school::text").get()
        if uni_elem:
            university = uni_elem.strip()
        
        # Extract average rating
        avg_rating = None
        rating_elem = response.css("div.rating::text, span.rating::text").get()
        if rating_elem:
            rating_match = re.search(r"(\d+\.?\d*)", rating_elem)
            if rating_match:
                avg_rating = float(rating_match.group(1))
        
        # Extract total ratings count
        total_ratings = 0
        count_elem = response.css("div.rating-count::text, span.count::text").get()
        if count_elem:
            count_match = re.search(r"(\d+)", count_elem)
            if count_match:
                total_ratings = int(count_match.group(1))
        
        # Create professor item
        if name and rmp_id:
            professor_item = ProfessorItem(
                professor_id=rmp_id,
                name=name,
                department=department,
                university=university,
                rmp_id=rmp_id,
                average_rating=avg_rating,
                total_ratings=total_ratings
            )
            
            if self.validate_data(dict(professor_item)):
                yield professor_item
        
        # Parse reviews on the same page
        review_sections = response.css("div.review, tr.review, div.rating-item")
        for review_section in review_sections:
            review_data = self.parse_review_section(review_section, rmp_id)
            if review_data and self.validate_data(review_data):
                review_item = ReviewItem(**review_data)
                yield review_item
    
    def parse_review_section(self, review_elem: Any, professor_rmp_id: str | None) -> dict[str, Any] | None:
        """Parse a single review section."""
        # Extract rating
        rating = 0.0
        rating_elem = review_elem.css("div.rating::text, span.rating::text").get()
        if rating_elem:
            rating_match = re.search(r"(\d+\.?\d*)", rating_elem)
            if rating_match:
                rating = float(rating_match.group(1))
        
        # Extract difficulty
        difficulty = None
        diff_elem = review_elem.css("div.difficulty::text, span.difficulty::text").get()
        if diff_elem:
            diff_match = re.search(r"(\d+\.?\d*)", diff_elem)
            if diff_match:
                difficulty = float(diff_match.group(1))
        
        # Extract would take again
        would_take_again = None
        take_again_elem = review_elem.css("div.take-again::text").get()
        if take_again_elem:
            would_take_again = "yes" in take_again_elem.lower()
        
        # Extract review text
        text = " ".join(review_elem.css("div.comment::text, p.comment::text").getall()).strip()
        
        # Extract date
        date = None
        date_elem = review_elem.css("div.date::text, span.date::text").get()
        if date_elem:
            # Try to parse date
            try:
                date = datetime.strptime(date_elem.strip(), "%m/%d/%Y")
            except ValueError:
                pass
        
        # Extract course name
        course_name = ""
        course_elem = review_elem.css("div.course::text, span.course::text").get()
        if course_elem:
            course_name = course_elem.strip()
        
        # Note: professor_id will be resolved by pipeline using rmp_id
        return {
            "review_id": None,
            "professor_id": professor_rmp_id,  # Pipeline will resolve this
            "rating": rating,
            "difficulty": difficulty,
            "would_take_again": would_take_again,
            "text": text,
            "date": date,
            "course_name": course_name
        }
    
    def save(self, item: dict[str, Any]) -> None:
        """Save item - handled by pipeline."""
        # The actual saving is done by the pipeline
        pass

