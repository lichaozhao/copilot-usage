#!/usr/bin/env python3
"""
Simple validation script for AAD integration files.
Tests basic functionality without requiring external dependencies.
"""

import sys
import os
import tempfile
import configparser

def test_config_sample():
    """Test that the config sample file is properly formatted."""
    print("🧪 Testing config-sample.ini...")
    
    config_file = "/home/runner/work/copilot-usage/copilot-usage/config-sample.ini"
    
    if not os.path.exists(config_file):
        print(f"✗ Config sample file not found: {config_file}")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        
        # Check required sections
        required_sections = ['es', 'azure_storage', 'aad']
        for section in required_sections:
            if section not in config.sections():
                print(f"✗ Missing required section: {section}")
                return False
        
        # Check AAD section has required keys
        aad_keys = ['tenant_id', 'client_id', 'client_secret', 'enable_aad_auth']
        for key in aad_keys:
            if key not in config['aad']:
                print(f"✗ Missing AAD config key: {key}")
                return False
        
        print("✓ Config sample file is properly formatted")
        return True
        
    except Exception as e:
        print(f"✗ Error reading config file: {e}")
        return False

def test_aad_auth_file():
    """Test that aad_auth.py has proper structure."""
    print("\n🧪 Testing aad_auth.py structure...")
    
    aad_file = "/home/runner/work/copilot-usage/copilot-usage/aad_auth.py"
    
    if not os.path.exists(aad_file):
        print(f"✗ AAD auth file not found: {aad_file}")
        return False
    
    try:
        with open(aad_file, 'r') as f:
            content = f.read()
        
        # Check for required class and methods
        required_elements = [
            'class AADAuthenticator',
            'def __init__',
            'def is_aad_enabled',
            'def validate_bearer_token',
            'def authenticate_user',
            'def get_user_info'
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"✗ Missing required element: {element}")
                return False
        
        print("✓ AAD auth file has proper structure")
        return True
        
    except Exception as e:
        print(f"✗ Error reading AAD auth file: {e}")
        return False

def test_sample_py_integration():
    """Test that sample.py has been properly modified."""
    print("\n🧪 Testing sample.py AAD integration...")
    
    sample_file = "/home/runner/work/copilot-usage/copilot-usage/sample.py"
    
    if not os.path.exists(sample_file):
        print(f"✗ Sample file not found: {sample_file}")
        return False
    
    try:
        with open(sample_file, 'r') as f:
            content = f.read()
        
        # Check for AAD integration elements
        required_elements = [
            'from aad_auth import AADAuthenticator',
            'self.aad_auth = AADAuthenticator',
            'Authorization',
            'Bearer',
            'user_info'
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"✗ Missing AAD integration element: {element}")
                return False
        
        print("✓ Sample.py has proper AAD integration")
        return True
        
    except Exception as e:
        print(f"✗ Error reading sample.py: {e}")
        return False

def test_requirements_file():
    """Test that requirements.txt includes AAD dependencies."""
    print("\n🧪 Testing requirements.txt...")
    
    req_file = "/home/runner/work/copilot-usage/copilot-usage/requirements.txt"
    
    if not os.path.exists(req_file):
        print(f"✗ Requirements file not found: {req_file}")
        return False
    
    try:
        with open(req_file, 'r') as f:
            content = f.read()
        
        # Check for AAD-related dependencies
        required_deps = ['msal', 'PyJWT', 'cryptography']
        
        for dep in required_deps:
            if dep not in content:
                print(f"✗ Missing required dependency: {dep}")
                return False
        
        print("✓ Requirements.txt includes AAD dependencies")
        return True
        
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False

def test_readme_updates():
    """Test that README has been updated with AAD instructions."""
    print("\n🧪 Testing README.md updates...")
    
    readme_file = "/home/runner/work/copilot-usage/copilot-usage/readme.md"
    
    if not os.path.exists(readme_file):
        print(f"✗ README file not found: {readme_file}")
        return False
    
    try:
        with open(readme_file, 'r') as f:
            content = f.read()
        
        # Check for AAD documentation
        required_elements = [
            'Azure Active Directory',
            'AAD',
            'Bearer Token',
            'tenant_id',
            'enable_aad_auth'
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"✗ Missing AAD documentation element: {element}")
                return False
        
        print("✓ README.md has proper AAD documentation")
        return True
        
    except Exception as e:
        print(f"✗ Error reading README.md: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Starting AAD Integration Validation...\n")
    
    tests = [
        test_config_sample,
        test_aad_auth_file,
        test_sample_py_integration,
        test_requirements_file,
        test_readme_updates
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All validations passed! AAD integration files are properly structured.")
        return 0
    else:
        print("❌ Some validations failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())