"""
Google Slides Service
Provides integration with Google Slides API for presentation management
"""

from typing import Optional, List, Dict, Any

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class SlidesService:
    """Google Slides API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('slides', 'v1', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Slides")
    
    def create_presentation(self, title: str) -> Dict[str, Any]:
        """Create a new presentation"""
        self._ensure_service()
        
        try:
            body = {'title': title}
            
            result = self.service.presentations().create(body=body).execute()
            
            return {
                "success": True,
                "presentation_id": result['presentationId'],
                "title": result.get('title'),
                "url": f"https://docs.google.com/presentation/d/{result['presentationId']}/edit"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_presentation(self, presentation_id: str) -> Dict[str, Any]:
        """Get presentation metadata and content"""
        self._ensure_service()
        
        try:
            result = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            return {
                "success": True,
                "presentation_id": result['presentationId'],
                "title": result.get('title'),
                "slides_count": len(result.get('slides', [])),
                "revision_id": result.get('revisionId')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def batch_update(self, presentation_id: str,
                    requests: List[Dict]) -> Dict[str, Any]:
        """Batch update presentation"""
        self._ensure_service()
        
        try:
            body = {'requests': requests}
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body=body
            ).execute()
            
            return {
                "success": True,
                "presentation_id": presentation_id,
                "replies": result.get('replies', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_slide(self, presentation_id: str,
                    index: int = 0,
                    layout: str = 'BLANK') -> Dict[str, Any]:
        """Create a new slide"""
        self._ensure_service()
        
        request = {
            'createSlide': {
                'insertionIndex': index,
                'slideLayoutReference': {
                    'predefinedLayout': layout
                }
            }
        }
        
        return self.batch_update(presentation_id, [request])
    
    def add_text_box(self, presentation_id: str,
                    page_id: str,
                    text: str,
                    position: Dict[str, float],
                    size: Dict[str, float]) -> Dict[str, Any]:
        """Add a text box to a slide"""
        self._ensure_service()
        
        request = {
            'createShape': {
                'pageId': page_id,
                'shape': {
                    'shapeType': 'TEXT_BOX',
                    'text': {'textElements': [{'textRun': {'content': text}}]},
                    'transform': {
                        'scaleX': size.get('width', 1),
                        'scaleY': size.get('height', 1),
                        'translateX': position.get('x', 0),
                        'translateY': position.get('y', 0),
                        'unit': 'PT'
                    }
                }
            }
        }
        
        return self.batch_update(presentation_id, [request])
    
    def add_image(self, presentation_id: str,
                page_id: str,
                image_url: str,
                position: Dict[str, float],
                size: Dict[str, float]) -> Dict[str, Any]:
        """Add an image to a slide"""
        self._ensure_service()
        
        request = {
            'createImage': {
                'pageId': page_id,
                'imageProperties': {
                    'sourceUrl': image_url
                },
                'transform': {
                    'scaleX': size.get('width', 1),
                    'scaleY': size.get('height', 1),
                    'translateX': position.get('x', 0),
                    'translateY': position.get('y', 0),
                    'unit': 'PT'
                }
            }
        }
        
        return self.batch_update(presentation_id, [request])
    
    def replace_text(self, presentation_id: str,
                    find_text: str,
                    replace_text: str) -> Dict[str, Any]:
        """Replace all occurrences of text"""
        self._ensure_service()
        
        request = {
            'replaceAllText': {
                'containsText': {'text': find_text},
                'replaceText': replace_text
            }
        }
        
        return self.batch_update(presentation_id, [request])
    
    def delete_text(self, presentation_id: str,
                   page_id: str,
                   text_range: Dict[str, int]) -> Dict[str, Any]:
        """Delete text from a shape"""
        self._ensure_service()
        
        request = {
            'deleteObject': {
                'objectId': page_id
            }
        }
        
        return self.batch_update(presentation_id, [request])
    
    def get_slides(self, presentation_id: str) -> Dict[str, Any]:
        """Get all slides in a presentation"""
        self._ensure_service()
        
        try:
            result = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            slides = []
            for i, slide in enumerate(result.get('slides', [])):
                slide_info = {
                    "index": i,
                    "slide_id": slide.get('objectId'),
                    "page_elements_count": len(slide.get('pageElements', []))
                }
                slides.append(slide_info)
            
            return {
                "success": True,
                "presentation_id": presentation_id,
                "slides": slides,
                "total": len(slides)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def copy_presentation(self, presentation_id: str,
                         title: str) -> Dict[str, Any]:
        """Copy a presentation (using Drive API)"""
        self._ensure_service()
        
        try:
            from services.drive import DriveService
            drive_service = DriveService(self.user_id)
            
            result = drive_service.service.files().copy(
                fileId=presentation_id,
                body={'name': title}
            ).execute()
            
            return {
                "success": True,
                "new_presentation_id": result['id'],
                "title": result['name']
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def create_presentation(user_id: str, title: str) -> Dict[str, Any]:
    """Create a new presentation"""
    service = SlidesService(user_id)
    return service.create_presentation(title)


def get_presentation(user_id: str, presentation_id: str) -> Dict[str, Any]:
    """Get presentation metadata"""
    service = SlidesService(user_id)
    return service.get_presentation(presentation_id)
