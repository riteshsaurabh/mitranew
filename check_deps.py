#!/usr/bin/env python3
"""
Check for missing dependencies required by the Money-Mitra app
"""

import sys
import importlib

REQUIRED_MODULES = [
    'streamlit',
    'pandas',
    'requests',
    'plotly',
    'numpy',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'altair',
    'toml',
    'blinker',
    'rich',
    'pydeck',
    'tenacity',
    'pyarrow'  # Checking if this is really needed
]

def check_dependency(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        return False, str(e)

if __name__ == "__main__":
    print("Checking dependencies...")
    missing = []
    
    for module in REQUIRED_MODULES:
        result = check_dependency(module)
        if result is True:
            print(f"✅ {module} is installed")
        else:
            _, error = result
            print(f"❌ {module} is NOT installed: {error}")
            missing.append(module)
    
    if missing:
        print("\nMissing modules:")
        for module in missing:
            print(f"  - {module}")
        print("\nInstall with:")
        print(f"pip install {' '.join(missing)}")
    else:
        print("\nAll dependencies are installed.") 