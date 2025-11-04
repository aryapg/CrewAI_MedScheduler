"""
Setup script for initializing the backend environment.
Run this script to verify all dependencies and configuration.
"""

import sys
import os

def check_python_version():
    """Check if Python version is 3.8+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "firebase_admin",
        "jose",
        "passlib",
        "pydantic",
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            missing_packages.append(package)
    
    return missing_packages


def check_env_file():
    """Check if .env file exists."""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        print("✅ .env file exists")
        return True
    else:
        print("⚠️  .env file not found. Using default configuration.")
        return False


def main():
    """Main setup check."""
    print("=" * 50)
    print("Medical Scheduler Backend - Setup Check")
    print("=" * 50)
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    print()
    
    # Check dependencies
    print("Checking dependencies...")
    missing = check_dependencies()
    print()
    
    if missing:
        print("⚠️  Missing packages. Install with:")
        print(f"   pip install {' '.join(missing)}")
        print()
    
    # Check .env file
    print("Checking configuration...")
    check_env_file()
    print()
    
    print("=" * 50)
    print("Setup check complete!")
    print("=" * 50)
    
    if missing:
        print("\n⚠️  Please install missing packages before running the server.")
    else:
        print("\n✅ All checks passed! You can now run the server with:")
        print("   python main.py")
        print("   or")
        print("   uvicorn main:app --reload")


if __name__ == "__main__":
    main()

