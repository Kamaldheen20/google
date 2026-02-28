"""
Google OAuth2 Authentication Module
Handles authentication flow for Google Workspace APIs
"""

import os
import json
import pickle
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from pydantic import BaseModel

from config import load_config


class TokenData(BaseModel):
    """Token storage model"""
    user_id: str
    credentials: Dict[str, Any]
    expires_at: datetime
    created_at: datetime = datetime.utcnow()


class GoogleAuth:
    """Google OAuth2 Authentication Handler"""
    
    def __init__(self):
        self.config = load_config()
        self.token_storage = {}
        self._credentials_cache = {}
        self.scopes = self.config['google']['scopes'] # Load scopes from config
    
    def get_auth_url(self, user_id: str) -> str:
        """Generate OAuth2 authorization URL"""
        client_config = {
            "web": {
                "client_id": self.config['google']['client_id'],
                "project_id": "inductive-dream-465220-h7",
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": self.config['google']['client_secret'],
                "redirect_uris": [self.config['google']['redirect_uri']]
            }
        }
        
        flow = InstalledAppFlow.from_client_config(
            client_config, # Use the client_config dictionary directly
            scopes=self.scopes # Use scopes loaded from config
        )
        
        # For 'web' client type, redirect_uri is set in client_config
        # For 'installed' type, we need to set it explicitly
        if 'web' in client_config:
            auth_url, state = flow.authorization_url(
                access_type='offline'
            )
        else:
            redirect_uri = self.config['google']['redirect_uri']
            auth_url, state = flow.authorization_url(
                access_type='offline',
                redirect_uri=redirect_uri
            )
        
        # Store flow in memory for callback
        self.token_storage[f"flow_{user_id}"] = {
            "flow": flow,
            "created_at": datetime.utcnow(),
            "state": state
        }
        
        return auth_url
    
    def handle_callback(self, user_id: str, authorization_code: str) -> Optional[Credentials]:
        """Handle OAuth2 callback and exchange code for tokens"""
        flow_key = f"flow_{user_id}"
        
        if flow_key not in self.token_storage:
            # Try to create a new flow if state expired
            return None
        
        flow_data = self.token_storage[flow_key]
        flow = flow_data["flow"]
        
        try:
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Store credentials
            self._store_credentials(user_id, credentials)
            
            # Clean up
            del self.token_storage[flow_key]
            
            return credentials
            
        except Exception as e:
            print(f"Error fetching tokens: {e}")
            # Clean up on error
            if flow_key in self.token_storage:
                del self.token_storage[flow_key]
            return None
    
    def _store_credentials(self, user_id: str, credentials: Credentials) -> None:
        """Store credentials for a user"""
        token_data = TokenData(
            user_id=user_id,
            credentials={
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'id_token': credentials.id_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': list(credentials.scopes) if credentials.scopes else self.scopes
            },
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self._credentials_cache[user_id] = token_data
        
        # Save to file
        token_dir = self.config['token']['file_path']
        os.makedirs(token_dir, exist_ok=True)
        
        token_file = os.path.join(token_dir, f"{self.config['token']['prefix']}_{user_id}.pickle")
        with open(token_file, 'wb') as f:
            pickle.dump(token_data.dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
    
    def load_credentials(self, user_id: str) -> Optional[Credentials]:
        """Load stored credentials for a user"""
        
        # Check in-memory cache first
        if user_id in self._credentials_cache:
            token_data = self._credentials_cache[user_id]
            cred_dict = token_data.credentials
            creds = Credentials(
                token=cred_dict['token'],
                refresh_token=cred_dict.get('refresh_token'),
                id_token=cred_dict.get('id_token'),
                token_uri=cred_dict['token_uri'],
                client_id=cred_dict['client_id'],
                client_secret=cred_dict['client_secret'],
                scopes=cred_dict.get('scopes')
            )
            if creds.valid: # Check if credentials are valid (not expired)
                return creds
            elif creds.refresh_token: # If expired but refresh token exists, try to refresh
                return self.refresh_credentials(user_id, creds)
            else: # No refresh token, or refresh failed
                return None
        
        # Try loading from file
        token_dir = self.config['token']['file_path']
        token_file = os.path.join(token_dir, f"{self.config['token']['prefix']}_{user_id}.pickle")
        
        if os.path.exists(token_file):
            try:
                with open(token_file, 'rb') as f:
                    token_data_dict = pickle.load(f)
                    token_data = TokenData(**token_data_dict)
                    
                    # Cache it
                    self._credentials_cache[user_id] = token_data
                    
                    cred_dict = token_data.credentials
                    creds = Credentials(
                        token=cred_dict['token'],
                        refresh_token=cred_dict.get('refresh_token'),
                        id_token=cred_dict.get('id_token'),
                        token_uri=cred_dict['token_uri'],
                        client_id=cred_dict['client_id'],
                        client_secret=cred_dict['client_secret'],
                        scopes=cred_dict.get('scopes')
                    )
                    if creds.valid:
                        return creds
                    elif creds.refresh_token:
                        return self.refresh_credentials(user_id, creds)
            except Exception as e:
                print(f"Error loading credentials: {e}")
        
        return None
    
    def refresh_credentials(self, user_id: str, credentials: Credentials) -> Optional[Credentials]:
        """Refresh expired credentials"""
        try:
            credentials.refresh(google.auth.transport.requests.Request())
            self._store_credentials(user_id, credentials)
            return credentials
        except RefreshError:
            # Credentials can't be refreshed, need re-authentication
            self.revoke_credentials(user_id)
            return None
    
    def revoke_credentials(self, user_id: str) -> bool:
        """Revoke and remove stored credentials"""
        # Remove from cache
        if user_id in self._credentials_cache:
            del self._credentials_cache[user_id]
        
        # Remove from file
        token_file = os.path.join(
            self.config['token']['file_path'],
            f"{self.config['token']['prefix']}_{user_id}.pickle"
        )
        
        if os.path.exists(token_file):
            os.remove(token_file)
            return True
        
        return False
    
    def is_authenticated(self, user_id: str) -> bool:
        """Check if user has valid credentials"""
        credentials = self.load_credentials(user_id) # This now handles refreshing
        if credentials and credentials.valid:
            return True
        # If credentials are not valid or couldn't be refreshed, they are not authenticated
        return False


# Singleton instance
auth_handler = GoogleAuth()
