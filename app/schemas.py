"""Pydantic schemas for API request/response models."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CourseInstructorSchema(BaseModel):
    """Schema for course instructor."""
    id: int
    instructor_name: str
    
    model_config = {"from_attributes": True}


class CourseSchema(BaseModel):
    """Schema for course response."""
    id: int
    course_id: Optional[str] = None
    title: str
    code: str
    department: str
    description: Optional[str] = None
    credits: Optional[float] = None
    level: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime
    instructors: List[CourseInstructorSchema] = []
    
    model_config = {"from_attributes": True}


class CourseCreateSchema(BaseModel):
    """Schema for course creation."""
    course_id: Optional[str] = None
    title: str
    code: str
    department: str
    description: Optional[str] = None
    credits: Optional[float] = None
    level: Optional[str] = None
    url: Optional[str] = None
    instructors: List[str] = []


class ReviewSchema(BaseModel):
    """Schema for review response."""
    id: int
    professor_id: int
    rating: float = Field(..., ge=0, le=5)
    difficulty: Optional[float] = Field(None, ge=0, le=5)
    would_take_again: Optional[bool] = None
    text: Optional[str] = None
    date: Optional[datetime] = None
    course_name: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ProfessorSchema(BaseModel):
    """Schema for professor response."""
    id: int
    name: str
    department: Optional[str] = None
    university: Optional[str] = None
    rmp_id: Optional[str] = None
    average_rating: Optional[float] = Field(None, ge=0, le=5)
    total_ratings: int
    created_at: datetime
    reviews: List[ReviewSchema] = []
    
    model_config = {"from_attributes": True}


class ProfessorCreateSchema(BaseModel):
    """Schema for professor creation."""
    name: str
    department: Optional[str] = None
    university: Optional[str] = None
    rmp_id: Optional[str] = None
    average_rating: Optional[float] = Field(None, ge=0, le=5)
    total_ratings: int = 0


class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    items: List[dict]
    total: int
    page: int
    page_size: int
    pages: int

