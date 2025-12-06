"""Spider for scraping MIT OpenCourseWare courses."""
from typing import Any, Generator
import re
from urllib.parse import urljoin
import scrapy
from scrapy.http import Request, Response
from scrapy_project.spiders.base_scraper import ScraperBase
from scrapy_project.items import CourseItem, ProfessorItem


class MitCoursesSpider(ScraperBase):
    """Spider to scrape course data from MIT OpenCourseWare."""
    
    name = "mit_courses"
    allowed_domains = ["ocw.mit.edu"]
    # Use sitemap to get course URLs (search page uses JavaScript)
    sitemap_urls = ["https://ocw.mit.edu/sitemap.xml"]
    
    def start_requests(self) -> Generator[Request, None, None]:
        """Start requests from sitemap."""
        for sitemap_url in self.sitemap_urls:
            yield Request(url=sitemap_url, callback=self.parse_sitemap)
    
    def parse_sitemap(self, response: Response) -> Generator[Request | dict[str, Any], None, None]:
        """Parse sitemap to find course URLs."""
        # MIT OCW sitemap is a sitemap index with course sitemaps
        # Format: <sitemap><loc>https://ocw.mit.edu/courses/COURSE-ID/sitemap.xml</loc></sitemap>
        
        # Remove namespaces for easier parsing
        response.selector.remove_namespaces()
        
        sitemap_links = response.xpath("//sitemap/loc/text()").getall()
        
        if sitemap_links:
            # This is a sitemap index - extract course URLs from sitemap links
            course_count = 0
            max_courses = 20
            
            self.logger.info(f"Found {len(sitemap_links)} sitemap entries, extracting first {max_courses} courses")
            
            for sitemap_url in sitemap_links:
                if course_count >= max_courses:
                    break
                
                if not sitemap_url:
                    continue
                
                # Extract course URL from sitemap URL: 
                # https://ocw.mit.edu/courses/COURSE-ID/sitemap.xml -> https://ocw.mit.edu/courses/COURSE-ID/
                if "/courses/" in sitemap_url and "/sitemap.xml" in sitemap_url:
                    course_url = sitemap_url.replace("/sitemap.xml", "/")
                    # Validate course URL
                    course_match = re.search(r"/courses/([^/]+)/", course_url)
                    if course_match:
                        course_id = course_match.group(1)
                        # Skip non-course entries (like res-, ec-, es-, hst-, ids-, sts-, wgs-, cms-, etc.)
                        # But allow numeric course IDs (like 6-0001, 18-06, 12-010, etc.)
                        if course_id.startswith(("res-", "ec-", "es-", "hst-", "ids-", "sts-", "wgs-", "cms-", "mas-", "introduction-to")):
                            continue
                        # Valid course IDs: numeric format (6-0001, 18-06, 12-010) or alphanumeric with dash
                        # Must start with a number
                        if re.match(r"^\d+", course_id) and ("-" in course_id or len(course_id) > 3):
                            course_count += 1
                            self.logger.info(f"Found course {course_count} from sitemap: {course_url}")
                            yield Request(url=course_url, callback=self.parse_course_detail)
        else:
            # This is an individual sitemap - extract course URLs
            course_urls = response.css("url loc::text").getall()
            
            course_count = 0
            max_courses = 20
            
            for url in course_urls:
                if not url or course_count >= max_courses:
                    break
                
                # Filter for main course pages (not sub-pages)
                if "/courses/" in url and "/pages/" not in url and "/video_galleries/" not in url and "/download" not in url:
                    course_match = re.search(r"/courses/([^/]+)/?", url)
                    if course_match:
                        course_id = course_match.group(1)
                        if "-" in course_id and len(course_id) > 3:
                            course_count += 1
                            self.logger.info(f"Found course {course_count} from sitemap: {url}")
                            yield Request(url=url, callback=self.parse_course_detail)
    
    def parse(self, response: Response) -> Generator[Request | dict[str, Any], None, None]:
        """Parse method required by base class - delegates to parse_course_list."""
        yield from self.parse_course_list(response)
    
    def parse_course_list(self, response: Response) -> Generator[Request | dict[str, Any], None, None]:
        """Parse the course listing page with card-contents divs."""
        # MIT OCW uses card-contents divs for course listings
        # Format: <div class="card-contents">credits | level title instructors departments</div>
        
        course_cards = response.css("div.card-contents")
        course_count = 0
        max_courses = 20
        
        self.logger.info(f"Found {len(course_cards)} course cards on page")
        
        for card in course_cards:
            if course_count >= max_courses:
                break
            
            # Get the full text content
            card_text = " ".join(card.css("::text").getall()).strip()
            
            # Find the parent link (course URL is usually in a parent <a> tag)
            parent_link = card.xpath("./ancestor::a[1]/@href").get() or card.xpath("./following::a[1]/@href").get() or card.xpath("./preceding::a[1]/@href").get()
            
            if not parent_link:
                # Try to find link in nearby elements
                parent_link = card.xpath("./../a/@href").get() or card.xpath("./../../a/@href").get()
            
            if parent_link and "/courses/" in parent_link:
                full_url = urljoin(response.url, parent_link)
                # Normalize URL
                if "/pages/" not in full_url and "/video_galleries/" not in full_url:
                    normalized_url = full_url.split("/pages/")[0].split("/video_galleries/")[0]
                    if not normalized_url.endswith("/"):
                        normalized_url += "/"
                    
                    course_count += 1
                    self.logger.info(f"Found course {course_count} from card: {normalized_url}")
                    yield Request(url=normalized_url, callback=self.parse_course_detail)
            else:
                # Try to extract course info directly from card text and create a search
                # Parse card text: "1.00 | UNDERGRADUATE, GRADUATE Introduction to Computers..."
                # Extract title (usually after the level info)
                card_parts = card_text.split("|")
                if len(card_parts) >= 2:
                    # Title is usually after the second part
                    title_part = "|".join(card_parts[1:]).strip()
                    # Title is usually the first line after level
                    title_lines = [line.strip() for line in title_part.split("\n") if line.strip()]
                    if title_lines:
                        # First non-empty line after level is usually the title
                        potential_title = title_lines[0]
                        self.logger.debug(f"Could not find link for card with title: {potential_title}")
        
        # Also try to find course links in the page
        course_links = response.css("a[href*='/courses/']::attr(href)").getall()
        seen_urls = set()
        
        for link in course_links:
            if course_count >= max_courses:
                break
                
            full_url = urljoin(response.url, link)
            if "/courses/" in full_url and "/pages/" not in full_url and "/video_galleries/" not in full_url:
                normalized_url = full_url.split("/pages/")[0].split("/video_galleries/")[0]
                if not normalized_url.endswith("/"):
                    normalized_url += "/"
                
                course_match = re.search(r"/courses/([^/]+)/", normalized_url)
                if course_match:
                    course_id = course_match.group(1)
                    if "-" in course_id and len(course_id) > 3 and normalized_url not in seen_urls:
                        seen_urls.add(normalized_url)
                        course_count += 1
                        self.logger.info(f"Found course {course_count} from link: {normalized_url}")
                        yield Request(url=normalized_url, callback=self.parse_course_detail)
        
        # Try pagination
        if course_count < max_courses:
            next_page = response.css("a.next::attr(href), a[aria-label*='next']::attr(href), a[rel='next']::attr(href)").get()
            if next_page:
                yield Request(url=urljoin(response.url, next_page), callback=self.parse_course_list)
    
    def parse_course_detail(self, response: Response) -> Generator[dict[str, Any], None, None]:
        """Parse individual course detail page."""
        # Skip sub-pages (pages/, video_galleries/, etc.) - only process main course pages
        if "/pages/" in response.url or "/video_galleries/" in response.url:
            return
        
        # Extract course code and title - try multiple selectors
        title_elem = (
            response.css("h1.course-title::text").get() or 
            response.css("h1::text").get() or
            response.css("title::text").get() or
            response.css(".course-title::text").get() or
            response.css("h2.course-title::text").get()
        )
        title = title_elem.strip() if title_elem else ""
        
        # If still no title, try to extract from URL
        if not title:
            # Extract from URL: /courses/6-0001-introduction-to-computer-science.../
            url_parts = response.url.split("/")
            if "courses" in url_parts:
                idx = url_parts.index("courses")
                if idx + 1 < len(url_parts):
                    course_slug = url_parts[idx + 1]
                    # Convert slug to title (e.g., "6-0001-introduction-to-computer-science" -> "Introduction to Computer Science")
                    title_parts = course_slug.split("-")
                    # Skip course number parts and join the rest
                    title_words = [part.capitalize() for part in title_parts if not part[0].isdigit()]
                    if title_words:
                        title = " ".join(title_words)
        
        # If still no title, skip this page
        if not title:
            return
        
        # Extract course code from URL (MIT OCW uses format like: /courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/)
        url_parts = response.url.split("/")
        course_code = ""
        course_id_from_url = ""
        
        if "courses" in url_parts:
            idx = url_parts.index("courses")
            if idx + 1 < len(url_parts):
                course_id_from_url = url_parts[idx + 1]
                # Extract course number from URL (e.g., "6-0001" from "6-0001-introduction-to...")
                code_match = re.match(r"^(\d+[A-Z]?-\d+[A-Z]?)", course_id_from_url)
                if code_match:
                    course_code = code_match.group(1)
        
        # Try to extract from page content if not found in URL
        if not course_code:
            code_match = re.search(r"([A-Z]{1,4}\s?\d+[A-Z]?-\d+[A-Z]?|\d+[A-Z]?-\d+[A-Z]?)", title)
            if code_match:
                course_code = code_match.group(1).strip().replace(" ", "")
        
        # Extract department (usually first part of course code, e.g., "6" from "6-0001")
        department = ""
        if course_code:
            # MIT format: number-letter-number (e.g., 6-0001, 18-06)
            dept_match = re.match(r"^(\d+[A-Z]?)", course_code)
            if dept_match:
                department = dept_match.group(1)
            else:
                # Try letter format (e.g., "CS" from "CS101")
                dept_match = re.match(r"^([A-Z]{2,4})", course_code)
                if dept_match:
                    department = dept_match.group(1)
        
        # Extract description
        description = " ".join(
            response.css("div.course-description::text, div.description::text, p::text").getall()
        ).strip()[:1000]  # Limit description length
        
        # Extract instructors from course page
        instructors = []
        # MIT OCW uses: <a class="course-info-instructor">Instructor Name</a>
        instructor_links = response.css("a.course-info-instructor::text, li a.course-info-instructor::text").getall()
        for instructor_name in instructor_links:
            if instructor_name and instructor_name.strip():
                instructors.append(instructor_name.strip())
        
        # Also try alternative selectors
        if not instructors:
            instructor_elems = response.css("div.instructor::text, span.instructor::text, h5:contains('Instructor') + div::text").getall()
            for elem in instructor_elems:
                if elem.strip():
                    instructors.append(elem.strip())
        
        # Extract department from course info section
        course_dept = ""
        dept_links = response.css("a.course-info-department::text").getall()
        if dept_links:
            course_dept = dept_links[0].strip() if dept_links else ""
        
        # If no department from course info, use the one extracted from course code
        if not course_dept:
            course_dept = department
        
        # Extract level (undergraduate/graduate)
        level = ""
        level_text = " ".join(response.css("body::text").getall()).lower()
        if "graduate" in level_text:
            level = "Graduate"
        elif "undergraduate" in level_text:
            level = "Undergraduate"
        
        # Extract credits if available
        credits = None
        credits_text = response.css("div.credits::text, span.credits::text").get()
        if credits_text:
            credits_match = re.search(r"(\d+(?:\.\d+)?)", credits_text)
            if credits_match:
                credits = float(credits_match.group(1))
        
        # Only process if we have both title and code
        if not title or not course_code:
            return
        
        # Create course item
        item: dict[str, Any] = {
            "course_id": course_code.lower().replace(" ", "-") if course_code else None,
            "title": title,
            "code": course_code,
            "department": department,
            "description": description,
            "credits": credits,
            "level": level,
            "url": response.url,
            "instructors": instructors
        }
        
        if self.validate_data(item) and title and course_code:
            self.save(item)
            yield item
        
        # Also create professor items for each instructor
        for instructor_name in instructors:
            if instructor_name:
                # Generate a unique ID for professor (based on name and department)
                prof_id = f"mit_{instructor_name.lower().replace(' ', '_').replace('.', '').replace(',', '')}"
                
                professor_item = ProfessorItem(
                    professor_id=prof_id,
                    name=instructor_name,
                    department=course_dept or department,
                    university="MIT",
                    rmp_id=None,  # No RMP ID for MIT OCW instructors
                    average_rating=None,
                    total_ratings=0
                )
                
                if self.validate_data(dict(professor_item)):
                    yield professor_item
    
    def save(self, item: dict[str, Any]) -> None:
        """Save item - handled by pipeline."""
        # The actual saving is done by the pipeline
        pass

