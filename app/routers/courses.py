"""API endpoints for courses."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Course
from app.schemas import CourseSchema, PaginatedResponse

router = APIRouter()


@router.get("/courses", response_model=PaginatedResponse)
def get_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    department: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> PaginatedResponse:
    """Get paginated list of courses with optional filters.
    
    Args:
        page: Page number (starting from 1).
        page_size: Number of items per page.
        department: Filter by department.
        level: Filter by level (e.g., "Undergraduate", "Graduate").
        db: Database session.
        
    Returns:
        PaginatedResponse: Paginated list of courses.
    """
    query = db.query(Course)
    
    # Apply filters
    if department:
        query = query.filter(Course.department.ilike(f"%{department}%"))
    if level:
        query = query.filter(Course.level.ilike(f"%{level}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    courses = query.order_by(Course.code).offset(offset).limit(page_size).all()
    
    # Calculate total pages
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[CourseSchema.model_validate(course).model_dump() for course in courses],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/courses/{course_id}", response_model=CourseSchema)
def get_course(course_id: int, db: Session = Depends(get_db)) -> CourseSchema:
    """Get a specific course by ID.
    
    Args:
        course_id: The course ID.
        db: Database session.
        
    Returns:
        CourseSchema: Course details.
        
    Raises:
        HTTPException: If course not found.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseSchema.model_validate(course)

