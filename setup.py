"""
Setup script for WhatsApp Automation project.
This script installs all dependencies and sets up Playwright browser.
"""

import subprocess
import sys

def install_requirements():
    """Install Python packages from requirements.txt"""
    print("Installing Python packages from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All Python packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def install_playwright_browser():
    """Install Chromium browser for Playwright"""
    print("\nInstalling Chromium browser for Playwright...")
    print("(This may take a few minutes and download ~150 MB)")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Chromium browser installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Chromium: {e}")
        return False

def main():
    print("=" * 60)
    print("WhatsApp Automation - Setup Script")
    print("=" * 60)
    
    # Step 1: Install Python packages
    if not install_requirements():
        print("\n❌ Setup failed at package installation step.")
        sys.exit(1)
    
    # Step 2: Install Playwright browser
    if not install_playwright_browser():
        print("\n⚠️  Setup completed but Chromium installation failed.")
        print("   You can install it manually later with: python -m playwright install chromium")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Create a .env file with your API keys (see ENV_FILE_SETUP.md)")
    print("2. Run: python extract_messages.py")

if __name__ == "__main__":
    main()

