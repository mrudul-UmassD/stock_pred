"""
Verify project setup and check all components.
"""

import sys
from pathlib import Path
import subprocess

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 9:
        print("✓ Python version OK")
        return True
    else:
        print("✗ Python 3.9+ required")
        return False

def check_file_exists(path: str):
    """Check if file exists."""
    p = Path(path)
    if p.exists():
        print(f"✓ {path}")
        return True
    else:
        print(f"✗ {path} NOT FOUND")
        return False

def check_directory_exists(path: str):
    """Check if directory exists."""
    p = Path(path)
    if p.exists() and p.is_dir():
        print(f"✓ {path}/")
        return True
    else:
        print(f"✗ {path}/ NOT FOUND")
        return False

def main():
    print("="*60)
    print("Stock Prediction Dashboard - Setup Verification")
    print("="*60)
    
    all_ok = True
    
    # Check Python
    print("\n1. Python Version")
    all_ok &= check_python_version()
    
    # Check directories
    print("\n2. Directory Structure")
    dirs = [
        "backend",
        "backend/app",
        "backend/app/services",
        "backend/scripts",
        "frontend",
        "frontend/app",
        "frontend/components",
        "notebooks",
        "artifacts",
        "db",
        ".github"
    ]
    for d in dirs:
        all_ok &= check_directory_exists(d)
    
    # Check backend files
    print("\n3. Backend Files")
    backend_files = [
        "backend/requirements.txt",
        "backend/app/__init__.py",
        "backend/app/main.py",
        "backend/app/db.py",
        "backend/app/routes.py",
        "backend/app/stream.py",
        "backend/app/services/__init__.py",
        "backend/app/services/data_sources.py",
        "backend/app/services/features.py",
        "backend/app/services/inference.py",
        "backend/scripts/predict.py"
    ]
    for f in backend_files:
        all_ok &= check_file_exists(f)
    
    # Check frontend files
    print("\n4. Frontend Files")
    frontend_files = [
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/tailwind.config.js",
        "frontend/next.config.js",
        "frontend/app/layout.tsx",
        "frontend/app/page.tsx",
        "frontend/app/globals.css",
        "frontend/app/health/page.tsx",
        "frontend/app/ticker/[symbol]/page.tsx",
        "frontend/components/PredictionTable.tsx",
        "frontend/components/LiveIndicator.tsx"
    ]
    for f in frontend_files:
        all_ok &= check_file_exists(f)
    
    # Check artifact files
    print("\n5. Artifact Files")
    artifact_files = [
        "artifacts/feature_schema.json",
        "artifacts/model_meta.json"
    ]
    for f in artifact_files:
        all_ok &= check_file_exists(f)
    
    # Check documentation
    print("\n6. Documentation")
    doc_files = [
        "README.md",
        "CONTRIBUTING.md",
        "QUICKSTART.md",
        ".gitignore",
        ".github/pull_request_template.md"
    ]
    for f in doc_files:
        all_ok &= check_file_exists(f)
    
    # Check notebooks
    print("\n7. Notebooks")
    notebook_files = [
        "notebooks/train.ipynb",
        "notebooks/requirements.txt"
    ]
    for f in notebook_files:
        all_ok &= check_file_exists(f)
    
    # Summary
    print("\n" + "="*60)
    if all_ok:
        print("✅ All checks passed! Project setup is complete.")
        print("\nNext steps:")
        print("1. cd backend && python -m venv venv && .\\venv\\Scripts\\activate")
        print("2. pip install -r requirements.txt")
        print("3. uvicorn app.main:app --reload")
        print("4. In new terminal: python scripts/predict.py --dummy")
        print("5. cd frontend && npm install && npm run dev")
        print("6. Open http://localhost:3000")
    else:
        print("❌ Some checks failed. Please review the output above.")
        sys.exit(1)
    print("="*60)

if __name__ == "__main__":
    main()
