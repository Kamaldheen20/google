"""
Session Manager
Handles user sessions and authentication state
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import secrets


@dataclass
class UserSession:
    """User session data"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    is_authenticated: bool = False
    credentials_stored: bool = False
    
    def is_valid(self) -> bool:
        """Check if session is valid"""
        return datetime.utcnow() < self.expires_at


class SessionManager:
    """Manages user sessions"""
    
    def __init__(self, session_secret: str = None):
        self.sessions: Dict[str, UserSession] = {}
        self.session_secret = session_secret or secrets.token_hex(32)
        self.session_duration = timedelta(hours=24)
    
    def create_session(self, user_id: str) -> str:
        """Create a new session for a user"""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            expires_at=now + self.session_duration
        )
        
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.is_valid():
                return session
            else:
                # Expired session, remove it
                del self.sessions[session_id]
        return None
    
    def validate_session(self, session_id: str) -> bool:
        """Validate a session"""
        session = self.get_session(session_id)
        return session is not None and session.is_authenticated
    
    def authenticate_session(self, session_id: str) -> bool:
        """Mark session as authenticated"""
        session = self.get_session(session_id)
        if session:
            session.is_authenticated = True
            session.credentials_stored = True
            return True
        return False
    
    def end_session(self, session_id: str) -> bool:
        """End a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def refresh_session(self, session_id: str) -> bool:
        """Refresh session expiration"""
        session = self.get_session(session_id)
        if session:
            session.expires_at = datetime.utcnow() + self.session_duration
            return True
        return False
    
    def get_user_id(self, session_id: str) -> Optional[str]:
        """Get user ID from session"""
        session = self.get_session(session_id)
        return session.user_id if session else None


# Singleton session manager
session_manager = SessionManager()


def create_user_session(user_id: str = None) -> str:
    """Create a new session"""
    if user_id is None:
        user_id = str(uuid.uuid4())
    return session_manager.create_session(user_id)


def validate_user_session(session_id: str) -> bool:
    """Validate user session"""
    return session_manager.validate_session(session_id)


def get_session_user(session_id: str) -> Optional[str]:
    """Get user ID from session"""
    return session_manager.get_user_id(session_id)
