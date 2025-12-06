"""Script to delete test professor and review data."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal, init_db
from app.models import Professor, Review

def delete_test_data():
    """Delete test professors and their reviews."""
    init_db()
    db = SessionLocal()
    
    try:
        # Test professor names (from create_test_professors.py)
        test_professor_names = [
            "Dr. Christopher Cassa",
            "Prof. Marta C. Gonzalez",
            "Dr. George Kocur",
            "Prof. John Guttag",
            "Dr. Gilbert Strang"
        ]
        
        # Find and delete test professors
        deleted_count = 0
        for name in test_professor_names:
            professor = db.query(Professor).filter(Professor.name == name).first()
            if professor:
                # Delete associated reviews first (cascade should handle this, but being explicit)
                review_count = db.query(Review).filter(Review.professor_id == professor.id).count()
                db.query(Review).filter(Review.professor_id == professor.id).delete()
                
                # Delete professor
                db.delete(professor)
                deleted_count += 1
                print(f"Deleted professor: {name} (and {review_count} reviews)")
        
        db.commit()
        print(f"\nSuccessfully deleted {deleted_count} test professors and their reviews!")
        
        # Show remaining professors
        remaining = db.query(Professor).count()
        print(f"Remaining professors in database: {remaining}")
        
    except Exception as e:
        db.rollback()
        print(f"Error deleting test data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    delete_test_data()

