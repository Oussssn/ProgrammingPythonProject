"""SQLAlchemy ORM models for database entities."""
from datetime import datetime
from typing import List
from sqlalchemy import Integer, String, Float, Boolean, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Course(Base):
    """ORM model for Course entity."""
    __tablename__ = "courses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    credits: Mapped[float | None] = mapped_column(Float, nullable=True)
    level: Mapped[str] = mapped_column(String(50), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    instructors: Mapped[List["CourseInstructor"]] = relationship(
        "CourseInstructor", back_populates="course", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_course_code_dept", "code", "department"),
    )


class Professor(Base):
    """ORM model for Professor entity."""
    __tablename__ = "professors"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    university: Mapped[str] = mapped_column(String(200), nullable=True, index=True)
    rmp_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True, nullable=True)
    average_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_ratings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="professor", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_professor_name_dept", "name", "department"),
    )


class Review(Base):
    """ORM model for Review entity."""
    __tablename__ = "reviews"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    professor_id: Mapped[int] = mapped_column(Integer, ForeignKey("professors.id"), nullable=False, index=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    would_take_again: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=True)
    date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    course_name: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    professor: Mapped["Professor"] = relationship("Professor", back_populates="reviews")
    
    __table_args__ = (
        Index("idx_review_professor_rating", "professor_id", "rating"),
    )


class CourseInstructor(Base):
    """ORM model for Course-Instructor relationship."""
    __tablename__ = "course_instructors"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    instructor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="instructors")
    
    __table_args__ = (
        Index("idx_course_instructor", "course_id", "instructor_name"),
    )

