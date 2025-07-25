"""
Azure Active Directory (AAD) Authentication Helper for Copilot Usage Collection

This module provides AAD authentication functionality for the mitmproxy-based
Copilot usage collection system.
"""

import jwt
import logging
import configparser
import requests
from msal import ConfidentialClientApplication
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json

# Setup logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class AADAuthenticator:
    """Handles Azure Active Directory authentication for proxy users."""
    
    def __init__(self, config_file_path: str = 'config.ini'):
        """Initialize AAD authenticator with configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_file_path)
        
        # AAD Configuration
        self.tenant_id = self.config.get('aad', 'tenant_id', fallback='')
        self.client_id = self.config.get('aad', 'client_id', fallback='')
        self.client_secret = self.config.get('aad', 'client_secret', fallback='')
        self.authority = self.config.get('aad', 'authority', fallback=f'https://login.microsoftonline.com/{self.tenant_id}')
        self.enable_aad_auth = self.config.getboolean('aad', 'enable_aad_auth', fallback=False)
        self.fallback_to_userlist = self.config.getboolean('aad', 'fallback_to_userlist', fallback=True)
        
        # Parse allowed groups if specified
        allowed_groups_str = self.config.get('aad', 'allowed_groups', fallback='')
        self.allowed_groups = [group.strip() for group in allowed_groups_str.split(',') if group.strip()]
        
        # Initialize MSAL client if AAD is enabled
        self.msal_app = None
        if self.enable_aad_auth and self.tenant_id and self.client_id:
            try:
                self.msal_app = ConfidentialClientApplication(
                    client_id=self.client_id,
                    client_credential=self.client_secret,
                    authority=self.authority
                )
                log.info("AAD authentication initialized successfully")
            except Exception as e:
                log.error(f"Failed to initialize AAD authentication: {e}")
                self.enable_aad_auth = False
        
        # Cache for token validation to avoid repeated calls
        self.token_cache = {}
        self.cache_ttl = timedelta(minutes=5)
    
    def is_aad_enabled(self) -> bool:
        """Check if AAD authentication is enabled and properly configured."""
        return self.enable_aad_auth and self.msal_app is not None
    
    def validate_bearer_token(self, token: str) -> Optional[Dict]:
        """
        Validate a Bearer token against Azure AD.
        
        Args:
            token: JWT Bearer token
            
        Returns:
            Dict with user info if valid, None if invalid
        """
        if not self.is_aad_enabled():
            return None
            
        # Check cache first
        cache_key = token[:20]  # Use first 20 chars as cache key
        if cache_key in self.token_cache:
            cached_result, cached_time = self.token_cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_result
        
        try:
            # Decode JWT without verification first to get key ID
            unverified_header = jwt.get_unverified_header(token)
            
            # Get Microsoft's public keys for verification
            jwks_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
            jwks_response = requests.get(jwks_url, timeout=10)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
            
            # Find the correct key
            key = None
            for jwk in jwks['keys']:
                if jwk['kid'] == unverified_header['kid']:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
                    break
            
            if not key:
                log.warning("No matching key found for token")
                return None
            
            # Verify and decode the token
            decoded_token = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
            )
            
            # Extract user information
            user_info = {
                'username': decoded_token.get('preferred_username', ''),
                'name': decoded_token.get('name', ''),
                'email': decoded_token.get('email', ''),
                'oid': decoded_token.get('oid', ''),  # Object ID
                'groups': decoded_token.get('groups', []),
                'roles': decoded_token.get('roles', [])
            }
            
            # Check group membership if allowed_groups is configured
            if self.allowed_groups:
                user_groups = set(decoded_token.get('groups', []))
                allowed_groups_set = set(self.allowed_groups)
                if not user_groups.intersection(allowed_groups_set):
                    log.warning(f"User {user_info['username']} not in allowed groups")
                    return None
            
            # Cache the result
            self.token_cache[cache_key] = (user_info, datetime.now())
            
            log.info(f"Successfully validated AAD token for user: {user_info['username']}")
            return user_info
            
        except jwt.ExpiredSignatureError:
            log.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            log.warning(f"Invalid token: {e}")
            return None
        except requests.RequestException as e:
            log.error(f"Failed to fetch JWKS: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error validating token: {e}")
            return None
    
    def authenticate_user(self, auth_header: str) -> Optional[str]:
        """
        Authenticate user from authorization header.
        
        Supports both Bearer tokens (AAD) and Basic auth (legacy).
        
        Args:
            auth_header: Authorization header value
            
        Returns:
            Username if authenticated, None if not
        """
        if not auth_header:
            return None
        
        auth_parts = auth_header.split(' ', 1)
        if len(auth_parts) != 2:
            return None
        
        auth_type, auth_value = auth_parts
        
        # Try AAD Bearer token first if enabled
        if auth_type.lower() == 'bearer' and self.is_aad_enabled():
            user_info = self.validate_bearer_token(auth_value)
            if user_info:
                return user_info['username'] or user_info['email']
        
        # Fall back to basic auth if configured or AAD fails
        elif auth_type.lower() == 'basic' and self.fallback_to_userlist:
            try:
                import base64
                username = base64.b64decode(auth_value).decode("utf-8").replace(":", "")
                return username
            except Exception as e:
                log.warning(f"Failed to decode basic auth: {e}")
                return None
        
        return None
    
    def get_user_info(self, username: str) -> Dict:
        """
        Get cached user information for a username.
        
        Args:
            username: Username to lookup
            
        Returns:
            Dict with user information
        """
        # Search cache for user info by username
        for (cached_result, cached_time) in self.token_cache.values():
            if cached_result and (cached_result.get('username') == username or cached_result.get('email') == username):
                if datetime.now() - cached_time < self.cache_ttl:
                    return cached_result
        
        # Return basic info if not found in cache
        return {'username': username, 'source': 'basic_auth'}