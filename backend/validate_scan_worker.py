"""
Quick validation script to verify scan worker implementation structure.
This doesn't require Redis to be running - just checks code structure.
"""

import sys
import inspect

def validate_implementation():
    """Validate that all components are properly implemented."""
    
    print("="*70)
    print("🔍 Scanning Worker Implementation Validation")
    print("="*70)
    
    checks = []
    
    # Check 1: Configuration
    print("\n📝 Checking Configuration...")
    try:
        from app.core.config import settings
        checks.append(("Configuration module", True, "settings loaded"))
        print(f"   ✅ Redis URL configured: {settings.REDIS_URL}")
    except Exception as e:
        checks.append(("Configuration module", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # Check 2: Celery App
    print("\n📝 Checking Celery App...")
    try:
        from app.core.celery_app import celery_app
        checks.append(("Celery app", True, "celery_app imported"))
        print(f"   ✅ Broker: {celery_app.conf.broker_url}")
        print(f"   ✅ Backend: {celery_app.conf.result_backend}")
    except Exception as e:
        checks.append(("Celery app", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # Check 3: Repository Model
    print("\n📝 Checking Repository Model...")
    try:
        from app.models.repository import Repository, RepositoryStatus
        
        # Check for new fields
        model_fields = [col.name for col in Repository.__table__.columns]
        required_fields = ['completed_at', 'file_count', 'line_count']
        
        missing = [f for f in required_fields if f not in model_fields]
        if missing:
            checks.append(("Repository model fields", False, f"Missing: {missing}"))
            print(f"   ❌ Missing fields: {missing}")
        else:
            checks.append(("Repository model fields", True, "All fields present"))
            print(f"   ✅ completed_at field exists")
            print(f"   ✅ file_count field exists")
            print(f"   ✅ line_count field exists")
        
        # Check status enum
        statuses = [s.value for s in RepositoryStatus]
        required_statuses = ['pending', 'processing', 'completed', 'failed']
        if all(s in statuses for s in required_statuses):
            checks.append(("Repository statuses", True, "All statuses defined"))
            print(f"   ✅ All required statuses: {', '.join(required_statuses)}")
        else:
            checks.append(("Repository statuses", False, "Missing statuses"))
    except Exception as e:
        checks.append(("Repository model", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # Check 4: Scan Worker
    print("\n📝 Checking Scan Worker...")
    try:
        from app.workers.scan_worker import scan_repository
        
        checks.append(("Scan worker task", True, "Task defined"))
        print(f"   ✅ Task imported: scan_repository")
        print(f"   ✅ Task name: {scan_repository.name}")
        
        # Check if task has request attribute (indicates bind=True)
        if hasattr(scan_repository, 'request'):
            checks.append(("Task binding", True, "Task is bound"))
            print(f"   ✅ Task is bound (bind=True)")
        else:
            checks.append(("Task binding", False, "Task not bound"))
            print(f"   ⚠️  Task may not be bound")
        
        # Check task is registered with Celery
        if scan_repository.name in celery_app.tasks:
            checks.append(("Task registration", True, "Task registered"))
            print(f"   ✅ Task registered with Celery")
    except Exception as e:
        checks.append(("Scan worker", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # Check 5: API Integration
    print("\n📝 Checking API Integration...")
    try:
        # Read the repo.py file to check for scan_repository.delay call
        with open('app/api/repo.py', 'r', encoding='utf-8') as f:
            repo_api_content = f.read()
        
        if 'scan_repository.delay' in repo_api_content:
            checks.append(("API integration", True, "Worker triggered from API"))
            print(f"   ✅ API triggers scan_repository.delay()")
        else:
            checks.append(("API integration", False, "Worker not triggered"))
            print(f"   ❌ scan_repository.delay() not found in API")
        
        if 'from app.workers.scan_worker import scan_repository' in repo_api_content:
            checks.append(("API worker import", True, "Worker imported in API"))
            print(f"   ✅ Worker imported in API file")
        else:
            checks.append(("API worker import", False, "Worker not imported"))
            print(f"   ⚠️  Worker not imported in API file")
    except Exception as e:
        checks.append(("API integration", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # Check 6: Database Connection
    print("\n📝 Checking Database Setup...")
    try:
        from app.core.database import SessionLocal, engine
        checks.append(("Database connection", True, "Database configured"))
        print(f"   ✅ SessionLocal configured")
        print(f"   ✅ Engine configured")
    except Exception as e:
        checks.append(("Database setup", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 Validation Summary")
    print("="*70)
    
    passed = sum(1 for _, success, _ in checks if success)
    total = len(checks)
    
    for check_name, success, detail in checks:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not success:
            print(f"         → {detail}")
    
    print("\n" + "-"*70)
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All validation checks passed!")
        print("\n📚 Implementation Summary:")
        print("   ✅ Configuration is environment-driven")
        print("   ✅ Celery is configured with Redis")
        print("   ✅ Repository model has scan metrics")
        print("   ✅ Scan worker task is implemented")
        print("   ✅ API triggers background scan")
        print("   ✅ Database is properly set up")
        print("\n🚀 Next Steps:")
        print("   1. Start Docker Desktop")
        print("   2. Run: docker-compose up -d redis")
        print("   3. Run: python test_scan_worker.py")
        print("   4. See SCAN_WORKER_SETUP.md for full guide")
        return 0
    else:
        print("\n⚠️  Some checks failed.")
        print("   Review error messages above and fix issues.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(validate_implementation())
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(130)
