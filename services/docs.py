"""
Google Docs Service
Provides integration with Google Docs API for document creation and editing
"""

from typing import Optional, List, Dict, Any

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class DocsService:
    """Google Docs API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('docs', 'v1', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Docs")
    
    def create_document(self, title: str) -> Dict[str, Any]:
        """Create a new Google Doc"""
        self._ensure_service()
        
        try:
            body = {'title': title}
            
            result = self.service.documents().create(body=body).execute()
            
            return {
                "success": True,
                "document_id": result['documentId'],
                "title": result.get('title'),
                "url": f"https://docs.google.com/document/d/{result['documentId']}/edit"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document content"""
        self._ensure_service()
        
        try:
            result = self.service.documents().get(documentId=document_id).execute()
            
            return {
                "success": True,
                "document_id": result['documentId'],
                "title": result.get('title'),
                "content": result.get('body', {}).get('content'),
                "revision_id": result.get('revisionId')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_document(self, document_id: str, 
                       requests: List[Dict]) -> Dict[str, Any]:
        """Update document with batch operations"""
        self._ensure_service()
        
        try:
            result = self.service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            return {
                "success": True,
                "document_id": document_id,
                "replies": result.get('replies', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def insert_text(self, document_id: str, 
                    text: str,
                    index: int = 1) -> Dict[str, Any]:
        """Insert text at a specific location"""
        self._ensure_service()
        
        request = {
            'insertText': {
                'location': {'index': index},
                'text': text
            }
        }
        
        return self.update_document(document_id, [request])
    
    def append_text(self, document_id: str, text: str) -> Dict[str, Any]:
        """Append text to the end of the document"""
        self._ensure_service()
        
        # Get document to find end index
        doc = self.get_document(document_id)
        if not doc['success']:
            return doc
        
        # Find the end of the body content
        end_index = 1
        for element in doc.get('content', []):
            if 'endIndex' in element:
                end_index = element['endIndex']
        
        return self.insert_text(document_id, text, end_index - 1)
    
    def replace_text(self, document_id: str,
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
        
        return self.update_document(document_id, [request])
    
    def format_text(self, document_id: str,
                    start_index: int,
                    end_index: int,
                    bold: bool = None,
                    italic: bool = None,
                    underline: bool = None,
                    font_size: int = None,
                    font_family: str = None) -> Dict[str, Any]:
        """Format text with styles"""
        self._ensure_service()
        
        updates = {}
        
        if bold is not None:
            updates['bold'] = bold
        if italic is not None:
            updates['italic'] = italic
        if underline is not None:
            updates['underline'] = underline
        if font_size is not None:
            updates['fontSize'] = {'magnitude': font_size, 'unit': 'PT'}
        if font_family is not None:
            updates['weightedFontFamily'] = {'fontFamily': font_family}
        
        request = {
            'updateTextStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': end_index
                },
                'textStyle': updates,
                'fields': ','.join(updates.keys())
            }
        }
        
        return self.update_document(document_id, [request])
    
    def create_heading(self, document_id: str,
                       text: str,
                       heading_type: str = 'HEADING_1') -> Dict[str, Any]:
        """Create a heading"""
        self._ensure_service()
        
        request = {
            'insertText': {
                'location': {'index': 1},
                'text': text + '\n'
            }
        }
        
        update_request = {
            'updateTextStyle': {
                'range': {
                    'startIndex': 1,
                    'endIndex': len(text) + 1
                },
                'textStyle': {
                    'headingId': heading_type.lower(),
                    'headingType': heading_type
                },
                'fields': 'headingId,headingType'
            }
        }
        
        return self.update_document(document_id, [request, update_request])
    
    def insert_paragraph(self, document_id: str,
                         text: str,
                         index: int = 1,
                         style: str = 'NORMAL_TEXT') -> Dict[str, Any]:
        """Insert a paragraph"""
        self._ensure_service()
        
        request = {
            'insertText': {
                'location': {'index': index},
                'text': text + '\n'
            }
        }
        
        return self.update_document(document_id, [request])
    
    def create_list(self, document_id: str,
                   items: List[str],
                   list_type: str = 'NUMBERED') -> Dict[str, Any]:
        """Create a bulleted or numbered list"""
        self._ensure_service()
        
        results = []
        index = 1
        
        for i, item in enumerate(items):
            # Insert text
            request = {
                'insertText': {
                    'location': {'index': index},
                    'text': item + '\n'
                }
            }
            result = self.update_document(document_id, [request])
            results.append(result)
            
            index += len(item) + 1
        
        return {
            "success": True,
            "document_id": document_id,
            "items_added": len(items)
        }
    
    def create_table(self, document_id: str,
                    rows: int,
                    cols: int,
                    index: int = 1) -> Dict[str, Any]:
        """Create a table"""
        self._ensure_service()
        
        request = {
            'insertTable': {
                'location': {'index': index},
                'rows': rows,
                'columns': cols
            }
        }
        
        return self.update_document(document_id, [request])
    
    def read_document(self, document_id: str) -> Dict[str, Any]:
        """Read document content as plain text"""
        self._ensure_service()
        
        try:
            result = self.service.documents().get(documentId=document_id).execute()
            
            content_text = []
            
            # Parse body content
            body = result.get('body', {}).get('content', [])
            for element in body:
                if 'paragraph' in element:
                    para = element['paragraph']
                    para_text = ''
                    for elem in para.get('elements', []):
                        if 'textRun' in elem:
                            para_text += elem['textRun'].get('content', '')
                    if para_text.strip():
                        content_text.append(para_text.strip())
                elif 'table' in element:
                    content_text.append('[Table]')
            
            return {
                "success": True,
                "document_id": document_id,
                "title": result.get('title'),
                "content": '\n\n'.join(content_text)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_document(self, document_id: str,
                       mime_type: str = 'text/plain') -> Dict[str, Any]:
        """Export document in different formats"""
        self._ensure_service()
        
        try:
            # Note: Docs API doesn't support direct export
            # You would need to use Drive API for export
            return {
                "success": False,
                "error": "Use Drive API for document export",
                "hint": "Use drive.download_file with mime_type"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def create_document(user_id: str, title: str) -> Dict[str, Any]:
    """Create a new document"""
    service = DocsService(user_id)
    return service.create_document(title)


def get_document(user_id: str, document_id: str) -> Dict[str, Any]:
    """Get document content"""
    service = DocsService(user_id)
    return service.get_document(document_id)


def read_document(user_id: str, document_id: str) -> Dict[str, Any]:
    """Read document as plain text"""
    service = DocsService(user_id)
    return service.read_document(document_id)
