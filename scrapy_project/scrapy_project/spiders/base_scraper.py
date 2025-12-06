"""Abstract base class for all scrapers."""
from abc import ABC, abstractmethod
from typing import Any, Generator
import scrapy
from scrapy.http import Request, Response


class ScraperBase(scrapy.Spider, ABC):
    """Abstract base class that defines core scraper methods."""
    
    @abstractmethod
    def start_requests(self) -> Generator[Request, None, None]:
        """Generate initial requests to start scraping.
        
        Yields:
            Request: Initial requests to begin scraping.
        """
        pass
    
    @abstractmethod
    def parse(self, response: Response) -> Generator[Request | dict[str, Any], None, None]:
        """Parse the response and extract data.
        
        Args:
            response: The response object from the request.
            
        Yields:
            Request or dict: Either follow-up requests or item dictionaries.
        """
        pass
    
    @abstractmethod
    def save(self, item: dict[str, Any]) -> None:
        """Save the scraped item to storage.
        
        Args:
            item: Dictionary containing scraped data.
        """
        pass
    
    def validate_data(self, data: dict[str, Any]) -> bool:
        """Validate scraped data before saving.
        
        Args:
            data: Dictionary containing scraped data.
            
        Returns:
            bool: True if data is valid, False otherwise.
        """
        return bool(data and isinstance(data, dict))

