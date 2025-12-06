"""Scrapy pipelines for data processing and persistence."""
import sys
from pathlib import Path
from typing import Any
from datetime import datetime
import logging

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.validators import validate_course_data, validate_professor_data, validate_review_data
from core.dataclasses import Course, Professor, Review
from app.database import get_db_session, init_db
from app.models import Course as CourseModel, Professor as ProfessorModel, Review as ReviewModel, CourseInstructor

# Initialize database
init_db()

logger = logging.getLogger(__name__)


class DatabasePipeline:
    """Pipeline to validate and persist scraped data to PostgreSQL."""
    
    def __init__(self) -> None:
        """Initialize the pipeline."""
        self.db = None
    
    def open_spider(self, spider: Any) -> None:
        """Called when spider is opened."""
        self.db = get_db_session()
        logger.info("Database pipeline opened")
    
    def close_spider(self, spider: Any) -> None:
        """Called when spider is closed."""
        if self.db:
            self.db.close()
        logger.info("Database pipeline closed")
    
    def process_item(self, item: dict[str, Any], spider: Any) -> dict[str, Any]:
        """Process each item scraped by the spider.
        
        Args:
            item: Scraped item dictionary.
            spider: The spider that scraped the item.
            
        Returns:
            dict: The processed item.
        """
        try:
            # Determine item type and process accordingly
            if "course_id" in item or "code" in item:
                self._process_course(item)
            elif ("professor_id" in item or "name" in item) and "university" in item:
                # Professor item: has professor_id or name, and university
                self._process_professor(item)
            elif "professor_id" in item and "rating" in item:
                self._process_review(item)
            else:
                logger.warning(f"Unknown item type: {item.keys()}")
        
        except Exception as e:
            logger.error(f"Error processing item: {e}", exc_info=True)
        
        return item
    
    def _process_course(self, item: dict[str, Any]) -> None:
        """Process and save a course item."""
        try:
            # Validate using dataclass
            course_data = validate_course_data(item)
            
            # Check if course already exists
            existing_course = None
            if course_data.course_id:
                existing_course = self.db.query(CourseModel).filter(
                    CourseModel.course_id == course_data.course_id
                ).first()
            elif course_data.code:
                existing_course = self.db.query(CourseModel).filter(
                    CourseModel.code == course_data.code
                ).first()
            
            if existing_course:
                # Update existing course
                existing_course.title = course_data.title
                existing_course.department = course_data.department
                existing_course.description = course_data.description
                existing_course.credits = course_data.credits
                existing_course.level = course_data.level
                existing_course.url = course_data.url
                course_model = existing_course
            else:
                # Create new course
                course_model = CourseModel(
                    course_id=course_data.course_id,
                    title=course_data.title,
                    code=course_data.code,
                    department=course_data.department,
                    description=course_data.description,
                    credits=course_data.credits,
                    level=course_data.level,
                    url=course_data.url
                )
                self.db.add(course_model)
            
            self.db.commit()
            
            # Handle instructors
            if course_data.instructors:
                # Remove old instructors
                self.db.query(CourseInstructor).filter(
                    CourseInstructor.course_id == course_model.id
                ).delete()
                
                # Add new instructors
                for instructor_name in course_data.instructors:
                    instructor = CourseInstructor(
                        course_id=course_model.id,
                        instructor_name=instructor_name
                    )
                    self.db.add(instructor)
                
                self.db.commit()
            
            logger.info(f"Saved course: {course_data.code} - {course_data.title}")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving course: {e}", exc_info=True)
            raise
    
    def _process_professor(self, item: dict[str, Any]) -> None:
        """Process and save a professor item."""
        try:
            # Validate using dataclass
            professor_data = validate_professor_data(item)
            
            # Check if professor already exists
            existing_professor = None
            if professor_data.rmp_id:
                existing_professor = self.db.query(ProfessorModel).filter(
                    ProfessorModel.rmp_id == professor_data.rmp_id
                ).first()
            
            # Also check by name and university (for MIT OCW professors without rmp_id)
            if not existing_professor and professor_data.name:
                existing_professor = self.db.query(ProfessorModel).filter(
                    ProfessorModel.name == professor_data.name,
                    ProfessorModel.university == professor_data.university
                ).first()
            
            # Fallback: check by name and department
            if not existing_professor and professor_data.name:
                existing_professor = self.db.query(ProfessorModel).filter(
                    ProfessorModel.name == professor_data.name,
                    ProfessorModel.department == professor_data.department
                ).first()
            
            if existing_professor:
                # Update existing professor
                existing_professor.name = professor_data.name
                existing_professor.department = professor_data.department
                existing_professor.university = professor_data.university
                existing_professor.average_rating = professor_data.average_rating
                existing_professor.total_ratings = professor_data.total_ratings
                professor_model = existing_professor
            else:
                # Create new professor
                professor_model = ProfessorModel(
                    name=professor_data.name,
                    department=professor_data.department,
                    university=professor_data.university,
                    rmp_id=professor_data.rmp_id,
                    average_rating=professor_data.average_rating,
                    total_ratings=professor_data.total_ratings
                )
                self.db.add(professor_model)
            
            self.db.commit()
            logger.info(f"Saved professor: {professor_data.name}")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving professor: {e}", exc_info=True)
            raise
    
    def _process_review(self, item: dict[str, Any]) -> None:
        """Process and save a review item."""
        try:
            # Validate using dataclass
            review_data = validate_review_data(item)
            
            # Find professor by RMP ID or name
            professor = None
            if review_data.professor_id:
                # Try to find by RMP ID first
                professor = self.db.query(ProfessorModel).filter(
                    ProfessorModel.rmp_id == review_data.professor_id
                ).first()
            
            if not professor:
                logger.warning(f"Professor not found for review: {review_data.professor_id}")
                return
            
            # Create new review
            review_model = ReviewModel(
                professor_id=professor.id,
                rating=review_data.rating,
                difficulty=review_data.difficulty,
                would_take_again=review_data.would_take_again,
                text=review_data.text,
                date=review_data.date,
                course_name=review_data.course_name
            )
            
            self.db.add(review_model)
            self.db.commit()
            logger.info(f"Saved review for professor ID: {professor.id}")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving review: {e}", exc_info=True)
            raise

