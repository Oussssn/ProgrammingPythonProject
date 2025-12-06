"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import courses, professors, reviews

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="University Course Scraper API",
    description="REST API for accessing scraped university course and professor data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(courses.router, prefix="/api", tags=["courses"])
app.include_router(professors.router, prefix="/api", tags=["professors"])
app.include_router(reviews.router, prefix="/api", tags=["reviews"])


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "University Course Scraper API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

