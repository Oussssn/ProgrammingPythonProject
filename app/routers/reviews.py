"""API endpoints for reviews."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Review
from app.schemas import ReviewSchema, PaginatedResponse

router = APIRouter()


@router.get("/reviews", response_model=PaginatedResponse)
def get_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    professor_id: Optional[int] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    db: Session = Depends(get_db)
) -> PaginatedResponse:
    """Get paginated list of reviews with optional filters.
    
    Args:
        page: Page number (starting from 1).
        page_size: Number of items per page.
        professor_id: Filter by professor ID.
        min_rating: Filter by minimum rating.
        db: Database session.
        
    Returns:
        PaginatedResponse: Paginated list of reviews.
    """
    query = db.query(Review)
    
    # Apply filters
    if professor_id:
        query = query.filter(Review.professor_id == professor_id)
    if min_rating is not None:
        query = query.filter(Review.rating >= min_rating)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    from sqlalchemy import desc, nulls_last
    reviews = query.order_by(nulls_last(desc(Review.date)), desc(Review.created_at)).offset(offset).limit(page_size).all()
    
    # Calculate total pages
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[ReviewSchema.model_validate(review).model_dump() for review in reviews],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/reviews/{review_id}", response_model=ReviewSchema)
def get_review(review_id: int, db: Session = Depends(get_db)) -> ReviewSchema:
    """Get a specific review by ID.
    
    Args:
        review_id: The review ID.
        db: Database session.
        
    Returns:
        ReviewSchema: Review details.
        
    Raises:
        HTTPException: If review not found.
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewSchema.model_validate(review)

