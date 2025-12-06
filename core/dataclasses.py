"""Core dataclasses for Course, Professor, and Review entities."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Course:
    """Represents a university course."""
    course_id: Optional[str] = None
    title: str = ""
    code: str = ""
    department: str = ""
    description: str = ""
    credits: Optional[float] = None
    level: str = ""
    url: str = ""
    instructors: list[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate course data after initialization."""
        if not self.title:
            raise ValueError("Course title is required")
        if not self.code:
            raise ValueError("Course code is required")


@dataclass_json
@dataclass
class Professor:
    """Represents a university professor."""
    professor_id: Optional[str] = None
    name: str = ""
    department: str = ""
    university: str = ""
    rmp_id: Optional[str] = None
    average_rating: Optional[float] = None
    total_ratings: int = 0
    
    def __post_init__(self) -> None:
        """Validate professor data after initialization."""
        if not self.name:
            raise ValueError("Professor name is required")
        if self.average_rating is not None and (self.average_rating < 0 or self.average_rating > 5):
            raise ValueError("Average rating must be between 0 and 5")
        if self.total_ratings < 0:
            raise ValueError("Total ratings cannot be negative")


@dataclass_json
@dataclass
class Review:
    """Represents a professor review."""
    review_id: Optional[str] = None
    professor_id: Optional[str] = None
    rating: float = 0.0
    difficulty: Optional[float] = None
    would_take_again: Optional[bool] = None
    text: str = ""
    date: Optional[datetime] = None
    course_name: str = ""
    
    def __post_init__(self) -> None:
        """Validate review data after initialization."""
        if not self.professor_id:
            raise ValueError("Professor ID is required for review")
        if self.rating < 0 or self.rating > 5:
            raise ValueError("Rating must be between 0 and 5")
        if self.difficulty is not None and (self.difficulty < 0 or self.difficulty > 5):
            raise ValueError("Difficulty must be between 0 and 5")

