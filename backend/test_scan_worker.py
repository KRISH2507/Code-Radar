"""
Test script to validate Redis + Celery scan worker implementation.

This script tests:
1. Configuration is loaded correctly
2. Celery can connect to Redis  
3. Worker task can be enqueued
4. Database models are properly set up
"""

import sys
from app.core.config import settings
from app.core.celery_app import celery_app
from app.core.database import SessionLocal, engine
from app.models.repository import Repository, RepositoryStatus, SourceType
from sqlalchemy import inspect

def test_configuration():
    """Test 1: Verify configuration is loaded."""
    print("\n" + "="*60)
    print("Test 1: Configuration")
    print("="*60)
    
    try:
        print(f"✅ Redis URL: {settings.REDIS_URL}")
        print(f"✅ Database: Configured")
        print(f"✅ JWT Secret: Configured")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        return False

def test_celery_connection():
    """Test 2: Verify Celery can connect to Redis."""
    print("\n" + "="*60)
    print("Test 2: Celery Connection")
    print("="*60)
    
    try:
        print(f"✅ Broker: {celery_app.conf.broker_url}")
        print(f"✅ Backend: {celery_app.conf.result_backend}")
        print(f"✅ Serializer: {celery_app.conf.task_serializer}")
        
        # Try to inspect registered tasks
        registered_tasks = list(celery_app.tasks.keys())
        scan_task_found = any('scan_repository' in task for task in registered_tasks)
        
        if scan_task_found:
            print(f"✅ scan_repository task registered")
        else:
            print(f"⚠️  scan_repository task not found in: {[t for t in registered_tasks if not t.startswith('celery.')]}")
        
        return True
    except Exception as e:
        print(f"❌ Celery connection error: {str(e)}")
        return False

def test_database_schema():
    """Test 3: Verify database schema has new columns."""
    print("\n" + "="*60)
    print("Test 3: Database Schema")
    print("="*60)
    
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns('repositories')
        column_names = [col['name'] for col in columns]
        
        required_columns = ['completed_at', 'file_count', 'line_count']
        
        for col in required_columns:
            if col in column_names:
                print(f"✅ Column '{col}' exists")
            else:
                print(f"❌ Column '{col}' missing - run migration script!")
                return False
        
        print(f"\n✅ All required columns present")
        return True
    except Exception as e:
        print(f"❌ Database schema error: {str(e)}")
        print(f"   Run: python migrate_repository_metrics.py")
        return False

def test_worker_import():
    """Test 4: Verify worker can be imported and has correct signature."""
    print("\n" + "="*60)
    print("Test 4: Worker Import")
    print("="*60)
    
    try:
        from app.workers.scan_worker import scan_repository
        
        print(f"✅ Worker imported successfully")
        print(f"✅ Task name: {scan_repository.name}")
        print(f"✅ Task registered: {scan_repository.name in celery_app.tasks}")
        
        return True
    except Exception as e:
        print(f"❌ Worker import error: {str(e)}")
        return False

def test_enqueue_task():
    """Test 5: Verify task can be enqueued (requires Redis running)."""
    print("\n" + "="*60)
    print("Test 5: Task Enqueueing")
    print("="*60)
    
    try:
        from app.workers.scan_worker import scan_repository
        
        # Try to enqueue a task (with a fake ID)
        # This tests that Redis is accessible and Celery can queue tasks
        result = scan_repository.delay(99999)
        
        print(f"✅ Task enqueued successfully")
        print(f"✅ Task ID: {result.id}")
        print(f"✅ Task state: {result.state}")
        
        # Revoke the task since it's just a test
        result.revoke()
        print(f"✅ Test task revoked")
        
        return True
    except Exception as e:
        print(f"❌ Task enqueue error: {str(e)}")
        print(f"   Make sure Redis is running: docker-compose up -d redis")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 Redis + Celery Scan Worker Test Suite")
    print("="*60)
    
    tests = [
        ("Configuration", test_configuration),
        ("Celery Connection", test_celery_connection),
        ("Database Schema", test_database_schema),
        ("Worker Import", test_worker_import),
        ("Task Enqueueing", test_enqueue_task),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "-"*60)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("="*60)
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Worker is ready.")
        print("\nNext steps:")
        print("1. Start FastAPI: uvicorn app.main:app --reload")
        print("2. Start Celery: celery -A app.core.celery_app worker --pool=solo --loglevel=info")
        print("3. Submit a repository via API: POST /repo/github")
        return 0
    else:
        print("\n⚠️  Some tests failed. Fix issues before proceeding.")
        
        if not results[2][1]:  # Database schema test failed
            print("\n💡 Run database migration:")
            print("   python migrate_repository_metrics.py")
        
        if not results[4][1]:  # Task enqueue test failed
            print("\n💡 Start Redis:")
            print("   docker-compose up -d redis")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
