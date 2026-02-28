"""
Google Keep Service
Provides integration with Google Keep API for note management
"""

from typing import Optional, List, Dict, Any
import re

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class KeepService:
    """Google Keep API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('keep', 'v1', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Keep")
    
    def list_notes(self, max_results: int = 50) -> Dict[str, Any]:
        """List all notes"""
        self._ensure_service()
        
        try:
            result = self.service.notes().list(
                pageSize=max_results
            ).execute()
            
            notes = result.get('notes', [])
            
            parsed_notes = []
            for note in notes:
                parsed_notes.append({
                    "note_id": note.get('name'),
                    "title": note.get('title'),
                    "text": note.get('text'),
                    "created_time": note.get('createdTime'),
                    "updated_time": note.get('updatedTime'),
                    "is_trashed": note.get('trashed', False)
                })
            
            return {
                "success": True,
                "notes": parsed_notes,
                "total": len(parsed_notes)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_note(self, note_id: str) -> Dict[str, Any]:
        """Get a specific note"""
        self._ensure_service()
        
        try:
            result = self.service.notes().get(name=note_id).execute()
            
            return {
                "success": True,
                "note_id": result.get('name'),
                "title": result.get('title'),
                "text": result.get('text'),
                "labels": result.get('labels', []),
                "created_time": result.get('createdTime'),
                "updated_time": result.get('updatedTime')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_note(self, title: str,
                   text: str,
                   labels: List[str] = None) -> Dict[str, Any]:
        """Create a new note"""
        self._ensure_service()
        
        try:
            body = {
                'title': title,
                'text': text
            }
            
            if labels:
                body['labels'] = [{'name': label} for label in labels]
            
            result = self.service.notes().create(
                body=body,
                parent='notes'
            ).execute()
            
            return {
                "success": True,
                "note_id": result.get('name'),
                "title": result.get('title'),
                "created_time": result.get('createdTime')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_note(self, note_id: str,
                   title: str = None,
                   text: str = None) -> Dict[str, Any]:
        """Update a note"""
        self._ensure_service()
        
        try:
            # Get current note
            current = self.service.notes().get(name=note_id).execute()
            
            body = {
                'name': note_id,
                'title': title or current.get('title'),
                'text': text or current.get('text')
            }
            
            result = self.service.notes().update(
                name=note_id,
                body=body
            ).execute()
            
            return {
                "success": True,
                "note_id": result.get('name'),
                "updated": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_note(self, note_id: str) -> Dict[str, Any]:
        """Delete a note (move to trash)"""
        self._ensure_service()
        
        try:
            self.service.notes().delete(name=note_id).execute()
            
            return {
                "success": True,
                "note_id": note_id,
                "deleted": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_labels(self) -> Dict[str, Any]:
        """List all labels"""
        self._ensure_service()
        
        try:
            result = self.service.labels().list().execute()
            
            labels = result.get('labels', [])
            
            return {
                "success": True,
                "labels": labels,
                "total": len(labels)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_notes(self, query: str) -> Dict[str, Any]:
        """Search notes by content"""
        self._ensure_service()
        
        try:
            result = self.service.notes().list(
                pageSize=100
            ).execute()
            
            matching_notes = []
            for note in result.get('notes', []):
                text = (note.get('title', '') + ' ' + note.get('text', '')).lower()
                if query.lower() in text:
                    matching_notes.append({
                        "note_id": note.get('name'),
                        "title": note.get('title'),
                        "text": note.get('text')
                    })
            
            return {
                "success": True,
                "notes": matching_notes,
                "total": len(matching_notes)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def list_notes(user_id: str, max_results: int = 50) -> Dict[str, Any]:
    """List all notes"""
    service = KeepService(user_id)
    return service.list_notes(max_results)


def create_note(user_id: str, title: str, text: str,
                labels: List[str] = None) -> Dict[str, Any]:
    """Create a new note"""
    service = KeepService(user_id)
    return service.create_note(title, text, labels)


def search_notes(user_id: str, query: str) -> Dict[str, Any]:
    """Search notes"""
    service = KeepService(user_id)
    return service.search_notes(query)
