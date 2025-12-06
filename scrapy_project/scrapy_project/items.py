"""Scrapy items for scraped data."""
import scrapy
from typing import Optional, List


class CourseItem(scrapy.Item):
    """Item for course data."""
    course_id = scrapy.Field()
    title = scrapy.Field()
    code = scrapy.Field()
    department = scrapy.Field()
    description = scrapy.Field()
    credits = scrapy.Field()
    level = scrapy.Field()
    url = scrapy.Field()
    instructors = scrapy.Field()


class ProfessorItem(scrapy.Item):
    """Item for professor data."""
    professor_id = scrapy.Field()
    name = scrapy.Field()
    department = scrapy.Field()
    university = scrapy.Field()
    rmp_id = scrapy.Field()
    average_rating = scrapy.Field()
    total_ratings = scrapy.Field()


class ReviewItem(scrapy.Item):
    """Item for review data."""
    review_id = scrapy.Field()
    professor_id = scrapy.Field()
    rating = scrapy.Field()
    difficulty = scrapy.Field()
    would_take_again = scrapy.Field()
    text = scrapy.Field()
    date = scrapy.Field()
    course_name = scrapy.Field()

