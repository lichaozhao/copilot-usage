#!/usr/bin/env python3
"""
Example usage of AAD-enhanced Copilot usage collection system.

This script demonstrates how to configure and use the AAD integration
features in the Copilot usage collection system.
"""

import os
import shutil
import configparser

def setup_aad_config():
    """Create a sample configuration for AAD integration."""
    
    print("📝 Setting up AAD configuration...")
    
    # Check if config-sample.ini exists
    sample_config = "config-sample.ini"
    target_config = "config.ini"
    
    if not os.path.exists(sample_config):
        print(f"❌ Sample config file not found: {sample_config}")
        return False
    
    if os.path.exists(target_config):
        print(f"⚠️  Config file already exists: {target_config}")
        return True
    
    # Copy sample to actual config
    try:
        shutil.copy(sample_config, target_config)
        print(f"✅ Created {target_config} from {sample_config}")
        
        print("""
🔧 Next steps to configure AAD:
1. Edit config.ini and fill in your Azure AD details:
   - tenant_id: Your Azure AD tenant ID
   - client_id: Your app registration client ID  
   - client_secret: Your app registration client secret
   
2. Set enable_aad_auth=true to enable AAD authentication

3. Optionally configure allowed_groups for additional security

Example configuration:
[aad]
tenant_id=12345678-1234-1234-1234-123456789012
client_id=87654321-4321-4321-4321-210987654321
client_secret=your-client-secret-here
enable_aad_auth=true
fallback_to_userlist=true
""")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating config file: {e}")
        return False

def setup_user_list():
    """Create a sample allowed users list."""
    
    print("\n📝 Setting up user list...")
    
    users_file = "allowed_users.txt"
    
    if os.path.exists(users_file):
        print(f"⚠️  User list file already exists: {users_file}")
        return True
    
    try:
        with open(users_file, 'w') as f:
            f.write("""# Allowed users for proxy authentication
# Add one username per line
# These users can authenticate via basic auth when AAD fallback is enabled

user1
user2
admin
""")
        
        print(f"✅ Created sample {users_file}")
        print("""
🔧 Edit allowed_users.txt to add your authorized users.
This file is used for fallback authentication when AAD is disabled
or when fallback_to_userlist=true in config.ini
""")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating user list: {e}")
        return False

def show_usage_examples():
    """Show examples of how to use the AAD-enhanced system."""
    
    print("""
🚀 Usage Examples:

1. Start mitmproxy with AAD support:
   mitmdump --listen-host 0.0.0.0 --set block_global=false -s sample.py -p 8080

2. Client authentication options:

   a) Using Azure AD Bearer token (recommended):
      curl -H "Authorization: Bearer <your-jwt-token>" \\
           --proxy http://proxy-server:8080 \\
           https://api.example.com

   b) Using legacy basic auth (fallback):
      curl --proxy http://username@proxy-server:8080 \\
           https://api.example.com

3. Configure your IDE/editor proxy settings:
   
   VS Code:
   - Proxy: http://proxy-server:8080
   - Use AAD token in Authorization header
   
   JetBrains:
   - Proxy: http://proxy-server:8080
   - Authentication: Use AAD token or username

4. Monitor usage data:
   python3 copilot-usage.py  # Generate usage reports
   
🔐 Security Notes:
- AAD tokens are validated against Microsoft's public keys
- User information is extracted from verified JWT tokens
- Group membership can be enforced via allowed_groups config
- All authentication attempts are logged for audit purposes
""")

def main():
    """Main setup function."""
    
    print("🎯 AAD Integration Setup for Copilot Usage Collection\n")
    
    # Setup configuration
    if not setup_aad_config():
        return 1
    
    # Setup user list
    if not setup_user_list():
        return 1
    
    # Show usage examples
    show_usage_examples()
    
    print("\n✅ Setup complete! Configure your Azure AD details in config.ini and start the proxy.")
    
    return 0

if __name__ == "__main__":
    exit(main())