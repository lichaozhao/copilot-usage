#!/usr/bin/env python3
"""
Test script for AAD integration in Copilot usage collection system.

This script tests the basic functionality of the AAD authentication module.
"""

import sys
import os
import tempfile
import configparser
from unittest.mock import patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from aad_auth import AADAuthenticator
    print("✓ Successfully imported AADAuthenticator")
except ImportError as e:
    print(f"✗ Failed to import AADAuthenticator: {e}")
    sys.exit(1)

def create_test_config():
    """Create a test configuration file."""
    config = configparser.ConfigParser()
    
    config['es'] = {
        'es_username': 'test_user',
        'es_password': 'test_pass',
        'es_host': 'localhost:9200'
    }
    
    config['aad'] = {
        'tenant_id': 'test-tenant-id',
        'client_id': 'test-client-id', 
        'client_secret': 'test-client-secret',
        'enable_aad_auth': 'false',  # Start with disabled for testing
        'fallback_to_userlist': 'true',
        'allowed_groups': 'group1,group2'
    }
    
    # Create temporary config file
    temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
    config.write(temp_config)
    temp_config.close()
    
    return temp_config.name

def test_aad_authenticator_init():
    """Test AADAuthenticator initialization."""
    print("\n🧪 Testing AADAuthenticator initialization...")
    
    config_file = create_test_config()
    
    try:
        auth = AADAuthenticator(config_file)
        
        # Test configuration loading
        assert auth.tenant_id == 'test-tenant-id', "Tenant ID not loaded correctly"
        assert auth.client_id == 'test-client-id', "Client ID not loaded correctly"
        assert auth.enable_aad_auth == False, "AAD auth should be disabled in test"
        assert auth.fallback_to_userlist == True, "Fallback should be enabled"
        assert len(auth.allowed_groups) == 2, "Should have 2 allowed groups"
        
        print("✓ Configuration loaded correctly")
        print("✓ AAD authenticator initialized successfully")
        
    except Exception as e:
        print(f"✗ Error initializing AADAuthenticator: {e}")
        return False
    finally:
        os.unlink(config_file)
    
    return True

def test_basic_auth_fallback():
    """Test basic authentication fallback functionality."""
    print("\n🧪 Testing basic auth fallback...")
    
    config_file = create_test_config()
    
    try:
        auth = AADAuthenticator(config_file)
        
        # Test basic auth header parsing
        import base64
        test_username = "testuser"
        basic_auth_value = base64.b64encode(f"{test_username}:".encode()).decode()
        auth_header = f"Basic {basic_auth_value}"
        
        username = auth.authenticate_user(auth_header)
        assert username == test_username, f"Expected {test_username}, got {username}"
        
        print("✓ Basic auth fallback works correctly")
        
    except Exception as e:
        print(f"✗ Error testing basic auth: {e}")
        return False
    finally:
        os.unlink(config_file)
    
    return True

def test_bearer_token_disabled():
    """Test that Bearer token authentication is properly disabled when AAD is off."""
    print("\n🧪 Testing Bearer token handling when AAD is disabled...")
    
    config_file = create_test_config()
    
    try:
        auth = AADAuthenticator(config_file)
        
        # Test that AAD is properly disabled
        assert not auth.is_aad_enabled(), "AAD should be disabled"
        
        # Test bearer token returns None when AAD is disabled
        fake_token = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.fake.token"
        username = auth.authenticate_user(fake_token)
        assert username is None, "Bearer token should return None when AAD is disabled"
        
        print("✓ Bearer token properly rejected when AAD is disabled")
        
    except Exception as e:
        print(f"✗ Error testing Bearer token: {e}")
        return False
    finally:
        os.unlink(config_file)
    
    return True

def test_user_info():
    """Test user info retrieval functionality."""
    print("\n🧪 Testing user info functionality...")
    
    config_file = create_test_config()
    
    try:
        auth = AADAuthenticator(config_file)
        
        # Test user info for non-cached user
        user_info = auth.get_user_info("testuser")
        assert user_info['username'] == "testuser", "Username should match"
        assert user_info['source'] == "basic_auth", "Source should be basic_auth"
        
        print("✓ User info retrieval works correctly")
        
    except Exception as e:
        print(f"✗ Error testing user info: {e}")
        return False
    finally:
        os.unlink(config_file)
    
    return True

def main():
    """Run all tests."""
    print("🚀 Starting AAD Integration Tests...\n")
    
    tests = [
        test_aad_authenticator_init,
        test_basic_auth_fallback,
        test_bearer_token_disabled,
        test_user_info
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
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! AAD integration is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())