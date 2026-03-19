#!/usr/bin/env python3
"""
Startup validation script for Code Radar backend.
Tests all critical imports and module structure.
"""

def test_imports():
    """Test that all API modules can be imported."""
    print("🔍 Testing API module imports...")
    
    try:
        from app.api import auth
        assert hasattr(auth, 'router'), "auth.py missing router"
        print("  ✅ auth.py - router found")
    except Exception as e:
        print(f"  ❌ auth.py - {str(e)}")
        return False
    
    try:
        from app.api import dashboard
        assert hasattr(dashboard, 'router'), "dashboard.py missing router"
        print("  ✅ dashboard.py - router found")
    except Exception as e:
        print(f"  ❌ dashboard.py - {str(e)}")
        return False
    
    try:
        from app.api import repo
        assert hasattr(repo, 'router'), "repo.py missing router"
        print("  ✅ repo.py - router found")
    except Exception as e:
        print(f"  ❌ repo.py - {str(e)}")
        return False
    
    return True


def test_main_app():
    """Test that FastAPI app can be instantiated."""
    print("\n🔍 Testing FastAPI app instantiation...")
    
    try:
        from app.main import app
        print("  ✅ FastAPI app created successfully")
        
        # Check routes are registered
        routes = [route.path for route in app.routes]
        
        expected_prefixes = ["/auth", "/dashboard", "/repo"]
        for prefix in expected_prefixes:
            found = any(prefix in route for route in routes)
            if found:
                print(f"  ✅ {prefix} routes registered")
            else:
                print(f"  ⚠️  {prefix} routes not found")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed to create app: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*70)
    print("🚀 Code Radar Backend - Startup Validation")
    print("="*70)
    print()
    
    # Test imports
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n❌ Import tests failed. Fix errors above.")
        return 1
    
    # Test app instantiation
    app_ok = test_main_app()
    
    if not app_ok:
        print("\n❌ App instantiation failed. Fix errors above.")
        return 1
    
    print("\n" + "="*70)
    print("✅ All validation tests passed!")
    print("="*70)
    print("\n📝 Summary:")
    print("  • All API modules have valid routers")
    print("  • FastAPI app instantiates correctly")
    print("  • No import-time execution errors")
    print("\n🎉 Backend is ready to start with: uvicorn app.main:app --reload")
    print()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
