"""Script to run spiders and populate database."""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Set up Scrapy settings
os.chdir(project_root / "scrapy_project")
settings = get_project_settings()

# Create crawler process
process = CrawlerProcess(settings)

# Add spiders
process.crawl("mit_courses")
process.crawl("ratemyprofessor")

# Start crawling
print("Starting spiders...")
process.start()

print("Spider execution completed!")

