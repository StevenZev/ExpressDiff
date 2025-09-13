#!/usr/bin/env python3
"""
Simple test script to verify FastAPI backend compatibility with Python 3.6.8
"""

def test_imports():
    """Test if all required imports work."""
    try:
        print("Testing imports...")
        
        # Test basic imports
        import sys
        print(f"Python version: {sys.version}")
        
        # Test FastAPI imports
        try:
            import fastapi
            print(f"✓ FastAPI version: {fastapi.__version__}")
        except ImportError as e:
            print(f"✗ FastAPI import failed: {e}")
            return False
            
        try:
            import uvicorn
            print(f"✓ Uvicorn available")
        except ImportError as e:
            print(f"✗ Uvicorn import failed: {e}")
            return False
            
        try:
            import pydantic
            print(f"✓ Pydantic version: {pydantic.VERSION}")
        except ImportError as e:
            print(f"✗ Pydantic import failed: {e}")
            return False
            
        # Test our backend modules
        try:
            from backend.models import RunCreate, HealthCheck
            print("✓ Backend models imported successfully")
        except ImportError as e:
            print(f"✗ Backend models import failed: {e}")
            return False
            
        try:
            from backend.core.config import Config
            print("✓ Backend config imported successfully")
        except ImportError as e:
            print(f"✗ Backend config import failed: {e}")
            return False
            
        print("\n✓ All imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_basic_api():
    """Test if basic FastAPI app can be created."""
    try:
        print("\nTesting FastAPI app creation...")
        
        from fastapi import FastAPI
        app = FastAPI(title="Test App")
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "Hello World"}
            
        print("✓ FastAPI app created successfully")
        return True
        
    except Exception as e:
        print(f"✗ FastAPI app creation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("ExpressDiff Backend Compatibility Test")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_basic_api()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! Backend is compatible with your Python version.")
        print("\nTo start the development server:")
        print("python3 -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("✗ Some tests failed. You may need to install missing dependencies.")
        print("\nTo install dependencies:")
        print("python3 -m pip install --user -r requirements.txt")
    
    return success

if __name__ == "__main__":
    main()