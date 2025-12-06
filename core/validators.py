"""Validation utilities for scraped data."""
from typing import Any
from core.dataclasses import Course, Professor, Review


def validate_course_data(data: dict[str, Any]) -> Course:
    """Validate and create a Course instance from scraped data."""
    try:
        return Course(
            course_id=data.get("course_id"),
            title=data.get("title", "").strip(),
            code=data.get("code", "").strip(),
            department=data.get("department", "").strip(),
            description=data.get("description", "").strip(),
            credits=data.get("credits"),
            level=data.get("level", "").strip(),
            url=data.get("url", "").strip(),
            instructors=data.get("instructors", [])
        )
    except Exception as e:
        raise ValueError(f"Invalid course data: {e}") from e


def validate_professor_data(data: dict[str, Any]) -> Professor:
    """Validate and create a Professor instance from scraped data."""
    try:
        return Professor(
            professor_id=data.get("professor_id"),
            name=data.get("name", "").strip(),
            department=data.get("department", "").strip(),
            university=data.get("university", "").strip(),
            rmp_id=data.get("rmp_id"),
            average_rating=data.get("average_rating"),
            total_ratings=data.get("total_ratings", 0)
        )
    except Exception as e:
        raise ValueError(f"Invalid professor data: {e}") from e


def validate_review_data(data: dict[str, Any]) -> Review:
    """Validate and create a Review instance from scraped data."""
    try:
        return Review(
            review_id=data.get("review_id"),
            professor_id=data.get("professor_id"),
            rating=float(data.get("rating", 0.0)),
            difficulty=data.get("difficulty"),
            would_take_again=data.get("would_take_again"),
            text=data.get("text", "").strip(),
            date=data.get("date"),
            course_name=data.get("course_name", "").strip()
        )
    except Exception as e:
        raise ValueError(f"Invalid review data: {e}") from e

