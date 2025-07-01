#!/usr/bin/env python3
"""
Setup script for FBX to MDL Converter
Handles installation and dependency checking
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    min_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        print(f"Error: Python {min_version[0]}.{min_version[1]}+ required, found {current_version[0]}.{current_version[1]}")
        return False
    
    print(f"✓ Python {current_version[0]}.{current_version[1]} detected")
    return True


def install_requirements():
    """Install Python requirements"""
    print("Installing Python dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install Python dependencies")
        return False


def check_fbx_sdk():
    """Check if FBX SDK is available"""
    print("Checking FBX SDK availability...")
    
    try:
        import fbx
        print("✓ FBX SDK is available")
        return True
    except ImportError:
        print("⚠ FBX SDK not found")
        print("\nTo install FBX SDK:")
        print("1. Download from: https://www.autodesk.com/developer-network/platform-technologies/fbx-sdk-2020-3")
        print("2. Install the SDK for your platform")
        print("3. Add Python bindings to your Python path")
        return False


def setup_directories():
    """Create necessary directories"""
    print("Setting up directories...")
    
    directories = [
        "output",
        "temp", 
        "logs",
        "tests/sample_models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created {len(directories)} directories")


def create_config_file():
    """Create a user-specific config file if it doesn't exist"""
    user_config_path = "user_config.py"
    
    if os.path.exists(user_config_path):
        print("✓ User config file already exists")
        return
    
    print("Creating user config file...")
    
    # Detect FBX SDK path
    fbx_sdk_path = detect_fbx_sdk_path()
    
    config_content = f'''"""
User-specific configuration for FBX to MDL Converter
This file overrides settings in config.py
"""

# FBX SDK path (customize based on your installation)
FBX_SDK_PATH = r"{fbx_sdk_path}"

# Override any settings from config.py here
# Example:
# OPTIMIZE_GEOMETRY = False
# LOG_LEVEL = "DEBUG"
'''
    
    with open(user_config_path, 'w') as f:
        f.write(config_content)
    
    print(f"✓ Created user config file: {user_config_path}")


def detect_fbx_sdk_path():
    """Try to detect FBX SDK installation path"""
    system = platform.system()
    
    # Common installation paths
    if system == "Windows":
        paths = [
            r"C:\Program Files\Autodesk\FBX\FBX SDK\2020.3",
            r"C:\Program Files (x86)\Autodesk\FBX\FBX SDK\2020.3",
            r"C:\Autodesk\FBX SDK\2020.3"
        ]
    elif system == "Darwin":  # macOS
        paths = [
            "/Applications/Autodesk/FBX SDK/2020.3",
            "/usr/local/fbx",
            "/opt/fbx"
        ]
    else:  # Linux
        paths = [
            "/usr/local/fbx",
            "/opt/fbx",
            "/usr/fbx"
        ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return "CHANGE_THIS_PATH"


def validate_installation():
    """Validate the installation"""
    print("\nValidating installation...")
    
    try:
        # Test config import
        import config
        print("✓ Configuration loaded successfully")
        
        # Test core modules
        sys.path.insert(0, 'src')
        
        from utils.logger import get_logger
        print("✓ Logger module working")
        
        from formats.mdl_format import MDLHeader
        print("✓ MDL format module working")
        
        print("✓ Installation validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Installation validation failed: {e}")
        return False


def print_usage_info():
    """Print usage information"""
    print("\n" + "="*60)
    print("FBX to MDL Converter - Setup Complete!")
    print("="*60)
    
    print("\nUsage Examples:")
    print("  Single file conversion:")
    print("    python convert.py model.fbx model.mdl")
    
    print("\n  Batch conversion:")
    print("    python batch_convert.py input_folder/ output_folder/")
    
    print("\n  With optimization:")
    print("    python convert.py model.fbx model.mdl --optimize-bones --compress-animations")
    
    print("\nNext Steps:")
    if not check_fbx_sdk():
        print("  1. Install Autodesk FBX SDK 2020.3")
        print("  2. Update FBX_SDK_PATH in user_config.py")
    else:
        print("  1. Place your FBX files in the input directory")
        print("  2. Run the converter with your desired options")
    
    print("\nDocumentation:")
    print("  - README.md for detailed usage instructions")
    print("  - config.py for configuration options")
    print("  - Run with --help for command-line options")
    
    print("\n" + "="*60)


def main():
    """Main setup function"""
    print("FBX to MDL Converter Setup")
    print("="*40)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    # Setup directories
    setup_directories()
    
    # Install dependencies
    if not install_requirements():
        print("Warning: Some dependencies failed to install")
    
    # Check FBX SDK
    fbx_available = check_fbx_sdk()
    
    # Create user config
    create_config_file()
    
    # Validate installation
    validation_passed = validate_installation()
    
    # Print final information
    print_usage_info()
    
    if not validation_passed:
        print("\n⚠ Setup completed with warnings. Check error messages above.")
        sys.exit(1)
    elif not fbx_available:
        print("\n⚠ Setup completed but FBX SDK is not available.")
        print("The converter will not work until FBX SDK is installed.")
        sys.exit(1)
    else:
        print("\n✓ Setup completed successfully!")


if __name__ == "__main__":
    main()