"""
Quick test to verify users table exists and can accept data.
"""

from app.core.database import SessionLocal
from app.models import User


def test_user_creation():
    """Test creating a user in the database."""
    db = SessionLocal()
    
    try:
        # Check if table exists by querying
        print("🔍 Testing if users table exists...")
        count = db.query(User).count()
        print(f"✅ Users table exists! Found {count} existing users.\n")
        
        # Try to create a test user
        print("🔧 Creating test user...")
        test_user = User(
            email="test_table@example.com",
            name="Table Test",
            hashed_password="$2b$12$dummyhashfortest",  # Dummy hash to avoid bcrypt issue
            is_verified=False,
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ User created successfully!")
        print(f"   ID: {test_user.id}")
        print(f"   Email: {test_user.email}")
        print(f"   Name: {test_user.name}")
        
        # Clean up
        print("\n🧹 Cleaning up test user...")
        db.delete(test_user)
        db.commit()
        print("✅ Test user deleted.\n")
        
        print("=" * 60)
        print("✅ SUCCESS: Users table is working correctly!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    test_user_creation()
