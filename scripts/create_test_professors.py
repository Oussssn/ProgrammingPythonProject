"""Script to create test professor and review data."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal, init_db
from app.models import Professor, Review
from datetime import datetime, timedelta
import random

def create_test_data():
    """Create test professors and reviews."""
    init_db()
    db = SessionLocal()
    
    try:
        # Sample MIT professors
        professors_data = [
            {
                "name": "Dr. Christopher Cassa",
                "department": "Engineering",
                "university": "MIT",
                "rmp_id": "rmp_001",
                "average_rating": 4.5,
                "total_ratings": 25
            },
            {
                "name": "Prof. Marta C. Gonzalez",
                "department": "Computer Science",
                "university": "MIT",
                "rmp_id": "rmp_002",
                "average_rating": 4.2,
                "total_ratings": 18
            },
            {
                "name": "Dr. George Kocur",
                "department": "Systems Engineering",
                "university": "MIT",
                "rmp_id": "rmp_003",
                "average_rating": 4.0,
                "total_ratings": 15
            },
            {
                "name": "Prof. John Guttag",
                "department": "Computer Science",
                "university": "MIT",
                "rmp_id": "rmp_004",
                "average_rating": 4.7,
                "total_ratings": 42
            },
            {
                "name": "Dr. Gilbert Strang",
                "department": "Mathematics",
                "university": "MIT",
                "rmp_id": "rmp_005",
                "average_rating": 4.8,
                "total_ratings": 156
            }
        ]
        
        created_professors = []
        
        for prof_data in professors_data:
            # Check if professor already exists
            existing = db.query(Professor).filter(
                Professor.rmp_id == prof_data["rmp_id"]
            ).first()
            
            if existing:
                print(f"Professor {prof_data['name']} already exists, skipping...")
                created_professors.append(existing)
                continue
            
            professor = Professor(**prof_data)
            db.add(professor)
            db.flush()  # Get the ID
            created_professors.append(professor)
            print(f"Created professor: {professor.name}")
        
        db.commit()
        
        # Create reviews for each professor
        review_texts = [
            "Great professor! Very clear explanations and helpful office hours.",
            "The course was challenging but fair. Professor was always available for questions.",
            "Excellent lecturer, makes complex topics easy to understand.",
            "Good professor, but the course material is quite difficult.",
            "One of the best professors I've had. Highly recommend!",
            "The professor is knowledgeable but the pace is very fast.",
            "Fair grading and clear expectations. Would take again.",
            "The course is well-structured and the professor is engaging.",
            "Difficult course but the professor provides good support.",
            "Clear explanations and helpful feedback on assignments."
        ]
        
        course_names = [
            "Introduction to Computer Science",
            "Linear Algebra",
            "Calculus",
            "Data Structures",
            "Algorithms",
            "Machine Learning",
            "Database Systems",
            "Software Engineering",
            "Computer Systems",
            "Artificial Intelligence"
        ]
        
        for professor in created_professors:
            # Create 3-5 reviews per professor
            num_reviews = random.randint(3, 5)
            
            for i in range(num_reviews):
                # Check if review already exists
                existing_review = db.query(Review).filter(
                    Review.professor_id == professor.id,
                    Review.text == review_texts[i % len(review_texts)]
                ).first()
                
                if existing_review:
                    continue
                
                review = Review(
                    professor_id=professor.id,
                    rating=round(random.uniform(3.5, 5.0), 1),
                    difficulty=round(random.uniform(2.0, 4.5), 1),
                    would_take_again=random.choice([True, False, None]),
                    text=review_texts[i % len(review_texts)],
                    date=datetime.now() - timedelta(days=random.randint(1, 365)),
                    course_name=course_names[i % len(course_names)]
                )
                db.add(review)
                print(f"  Created review for {professor.name}: {review.rating}/5.0")
        
        db.commit()
        print(f"\nSuccessfully created {len(created_professors)} professors with reviews!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating test data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()

