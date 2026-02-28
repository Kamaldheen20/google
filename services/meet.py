"""
Google Meet Service
Provides integration with Google Meet API for video conferencing
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class MeetService:
    """Google Meet API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('meet', 'v2', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Meet")
    
    def create_meeting_space(self, 
                            name: str = None,
                            expiration_minutes: int = 60) -> Dict[str, Any]:
        """Create a new meeting space"""
        self._ensure_service()
        
        try:
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            
            body = {
                'config': {
                    'expireTime': expiration.isoformat() + 'Z'
                }
            }
            
            if name:
                body['displayName'] = name
            
            result = self.service.spaces().create(body=body).execute()
            
            return {
                "success": True,
                "space_id": result.get('name'),
                "meeting_code": result.get('meetingCode'),
                "meeting_uri": result.get('meetingUri'),
                "display_name": result.get('config', {}).get('expireTime')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_meeting_space(self, space_id: str) -> Dict[str, Any]:
        """Get meeting space details"""
        self._ensure_service()
        
        try:
            result = self.service.spaces().get(name=space_id).execute()
            
            return {
                "success": True,
                "space_id": result.get('name'),
                "meeting_code": result.get('meetingCode'),
                "meeting_uri": result.get('meetingUri'),
                "config": result.get('config', {})
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_meeting_spaces(self, max_results: int = 10) -> Dict[str, Any]:
        """List meeting spaces"""
        self._ensure_service()
        
        try:
            result = self.service.spaces().list(
                pageSize=max_results
            ).execute()
            
            spaces = result.get('spaces', [])
            
            parsed_spaces = []
            for space in spaces:
                parsed_spaces.append({
                    "space_id": space.get('name'),
                    "meeting_code": space.get('meetingCode'),
                    "meeting_uri": space.get('meetingUri'),
                    "display_name": space.get('displayName')
                })
            
            return {
                "success": True,
                "spaces": parsed_spaces,
                "total": len(parsed_spaces)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_meeting_space(self, space_id: str) -> Dict[str, Any]:
        """Delete a meeting space"""
        self._ensure_service()
        
        try:
            self.service.spaces().delete(name=space_id).execute()
            
            return {
                "success": True,
                "space_id": space_id,
                "deleted": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_meeting_participants(self, space_id: str) -> Dict[str, Any]:
        """Get meeting participants"""
        self._ensure_service()
        
        try:
            result = self.service.spaces().participants().list(
                parent=space_id
            ).execute()
            
            participants = result.get('participants', [])
            
            return {
                "success": True,
                "participants": participants,
                "total": len(participants)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_quick_meeting(self, name: str = None) -> Dict[str, Any]:
        """Create a quick meeting"""
        return self.create_meeting_space(name=name, expiration_minutes=60)


# Convenience functions
def create_meeting_space(user_id: str, name: str = None) -> Dict[str, Any]:
    """Create a new meeting space"""
    service = MeetService(user_id)
    return service.create_meeting_space(name)


def get_meeting_space(user_id: str, space_id: str) -> Dict[str, Any]:
    """Get meeting space details"""
    service = MeetService(user_id)
    return service.get_meeting_space(space_id)
