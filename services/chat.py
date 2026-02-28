"""
Google Chat Service
Provides integration with Google Chat API for messaging
"""

from typing import Optional, List, Dict, Any

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class ChatService:
    """Google Chat API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('chat', 'v1', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Chat")
    
    def list_spaces(self, max_results: int = 100) -> Dict[str, Any]:
        """List chat spaces"""
        self._ensure_service()
        
        try:
            result = self.service.spaces().list(
                pageSize=max_results
            ).execute()
            
            spaces = result.get('spaces', [])
            
            return {
                "success": True,
                "spaces": spaces,
                "total": len(spaces)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_space(self, space_id: str) -> Dict[str, Any]:
        """Get space details"""
        self._ensure_service()
        
        try:
            result = self.service.spaces().get(name=space_id).execute()
            
            return {
                "success": True,
                "space": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_space(self, name: str, 
                    space_type: str = 'SPACE') -> Dict[str, Any]:
        """Create a new space"""
        self._ensure_service()
        
        try:
            body = {
                'spaceType': space_type,
                'displayName': name
            }
            
            result = self.service.spaces().create(body=body).execute()
            
            return {
                "success": True,
                "space_id": result.get('name'),
                "display_name": result.get('displayName')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_messages(self, space_id: str,
                     max_results: int = 100) -> Dict[str, Any]:
        """List messages in a space"""
        self._ensure_service()
        
        try:
            result = self.service.spaces().messages().list(
                parent=space_id,
                pageSize=max_results
            ).execute()
            
            messages = result.get('messages', [])
            
            parsed_messages = []
            for msg in messages:
                parsed_messages.append({
                    "message_id": msg.get('name'),
                    "text": msg.get('text'),
                    "sender": msg.get('sender', {}).get('name'),
                    "create_time": msg.get('createTime')
                })
            
            return {
                "success": True,
                "messages": parsed_messages,
                "total": len(parsed_messages)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_message(self, space_id: str,
                    text: str,
                    thread_key: str = None) -> Dict[str, Any]:
        """Send a message to a space"""
        self._ensure_service()
        
        try:
            body = {'text': text}
            
            if thread_key:
                body['thread'] = {'threadKey': thread_key}
            
            result = self.service.spaces().messages().create(
                parent=space_id,
                body=body
            ).execute()
            
            return {
                "success": True,
                "message_id": result.get('name'),
                "text": result.get('text')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_direct_message(self, user_id: str,
                             text: str) -> Dict[str, Any]:
        """Create a direct message"""
        self._ensure_service()
        
        try:
            # Create or get DM space
            space_result = self.service.spaces().createDirectMessage(
                body={
                    'user': f'users/{user_id}'
                }
            ).execute()
            
            space_id = space_result.get('name')
            
            # Send message
            return self.send_message(space_id, text)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_message(self, space_id: str,
                       message_id: str) -> Dict[str, Any]:
        """Delete a message"""
        self._ensure_service()
        
        try:
            self.service.spaces().messages().delete(
                name=f"{space_id}/messages/{message_id}"
            ).execute()
            
            return {
                "success": True,
                "message_id": message_id,
                "deleted": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_members(self, space_id: str) -> Dict[str, Any]:
        """Get space members"""
        self._ensure_service()
        
        try:
            result = self.service.spaces().members().list(
                parent=space_id
            ).execute()
            
            members = result.get('members', [])
            
            return {
                "success": True,
                "members": members,
                "total": len(members)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def list_spaces(user_id: str, max_results: int = 100) -> Dict[str, Any]:
    """List chat spaces"""
    service = ChatService(user_id)
    return service.list_spaces(max_results)


def send_message(user_id: str, space_id: str, text: str) -> Dict[str, Any]:
    """Send a message"""
    service = ChatService(user_id)
    return service.send_message(space_id, text)
