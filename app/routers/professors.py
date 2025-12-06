"""API endpoints for professors."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Professor
from app.schemas import ProfessorSchema, PaginatedResponse

router = APIRouter()


@router.get("/professors", response_model=PaginatedResponse)
def get_professors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    department: Optional[str] = Query(None),
    university: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> PaginatedResponse:
    """Get paginated list of professors with optional filters.
    
    Args:
        page: Page number (starting from 1).
        page_size: Number of items per page.
        department: Filter by department.
        university: Filter by university.
        db: Database session.
        
    Returns:
        PaginatedResponse: Paginated list of professors.
    """
    query = db.query(Professor)
    
    # Apply filters
    if department:
        query = query.filter(Professor.department.ilike(f"%{department}%"))
    if university:
        query = query.filter(Professor.university.ilike(f"%{university}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    professors = query.order_by(Professor.name).offset(offset).limit(page_size).all()
    
    # Calculate total pages
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[ProfessorSchema.model_validate(prof).model_dump() for prof in professors],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/professors/{professor_id}", response_model=ProfessorSchema)
def get_professor(professor_id: int, db: Session = Depends(get_db)) -> ProfessorSchema:
    """Get a specific professor by ID.
    
    Args:
        professor_id: The professor ID.
        db: Database session.
        
    Returns:
        ProfessorSchema: Professor details with reviews.
        
    Raises:
        HTTPException: If professor not found.
    """
    professor = db.query(Professor).filter(Professor.id == professor_id).first()
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    return ProfessorSchema.model_validate(professor)

