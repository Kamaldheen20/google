"""
Google Forms Service
Provides integration with Google Forms API for form management
"""

from typing import Optional, List, Dict, Any

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class FormsService:
    """Google Forms API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('forms', 'v1', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Forms")
    
    def create_form(self, title: str,
                   description: str = None) -> Dict[str, Any]:
        """Create a new form"""
        self._ensure_service()
        
        try:
            body = {
                'info': {
                    'title': title,
                    'documentTitle': title
                }
            }
            
            if description:
                body['info']['description'] = description
            
            result = self.service.forms().create(body=body).execute()
            
            return {
                "success": True,
                "form_id": result.get('formId'),
                "title": result['info']['title'],
                "url": f"https://docs.google.com/forms/d/{result['formId']}/edit"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_form(self, form_id: str) -> Dict[str, Any]:
        """Get form details"""
        self._ensure_service()
        
        try:
            result = self.service.forms().get(formId=form_id).execute()
            
            return {
                "success": True,
                "form_id": result.get('formId'),
                "title": result.get('info', {}).get('title'),
                "description": result.get('info', {}).get('description'),
                "items": result.get('items', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_question(self, form_id: str,
                    question: str,
                    question_type: str = 'TEXT',
                    choices: List[str] = None) -> Dict[str, Any]:
        """Add a question to the form"""
        self._ensure_service()
        
        try:
            item = {
                'title': question,
                'questionItem': {
                    'question': {
                        'required': True,
                        'textQuestion': {}
                    }
                }
            }
            
            if question_type == 'SHORT_ANSWER':
                item['questionItem']['question']['textQuestion'] = {}
            elif question_type == 'PARAGRAPH':
                item['questionItem']['question']['textQuestion'] = {'paragraph': True}
            elif question_type == 'MULTIPLE_CHOICE' and choices:
                item['questionItem']['question'] = {
                    'required': True,
                    'choiceQuestion': {
                        'type': 'RADIO',
                        'options': [{'value': choice} for choice in choices]
                    }
                }
            
            result = self.service.forms().batchUpdate(
                formId=form_id,
                body={
                    'requests': [{
                        'createItem': {
                            'item': item,
                            'location': {'index': 0}
                        }
                    }]
                }
            ).execute()
            
            return {
                "success": True,
                "form_id": form_id,
                "item_id": result.get('replies', [{}])[-1].get('createItem', {}).get('itemId')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_responses(self, form_id: str) -> Dict[str, Any]:
        """List form responses"""
        self._ensure_service()
        
        try:
            result = self.service.forms().responses().list(
                formId=form_id
            ).execute()
            
            responses = result.get('responses', [])
            
            return {
                "success": True,
                "responses": responses,
                "total": len(responses)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_response(self, form_id: str,
                     response_id: str) -> Dict[str, Any]:
        """Get a specific response"""
        self._ensure_service()
        
        try:
            result = self.service.forms().responses().get(
                formId=form_id,
                responseId=response_id
            ).execute()
            
            return {
                "success": True,
                "response_id": result.get('responseId'),
                "answers": result.get('answers', {}),
                "timestamp": result.get('createTime')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_form(self, form_id: str) -> Dict[str, Any]:
        """Delete a form"""
        self._ensure_service()
        
        try:
            self.service.forms().delete(formId=form_id).execute()
            
            return {
                "success": True,
                "form_id": form_id,
                "deleted": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def create_form(user_id: str, title: str, description: str = None) -> Dict[str, Any]:
    """Create a new form"""
    service = FormsService(user_id)
    return service.create_form(title, description)


def list_responses(user_id: str, form_id: str) -> Dict[str, Any]:
    """List form responses"""
    service = FormsService(user_id)
    return service.list_responses(form_id)
