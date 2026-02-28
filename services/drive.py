"""
Google Drive Service
Provides integration with Google Drive API for file management
"""

from typing import Optional, List, Dict, Any
import io
import os
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload
from auth.google_auth import auth_handler


class DriveService:
    """Google Drive API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('drive', 'v3', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Drive")
    
    def list_files(self, folder_id: str = None, 
                   mime_type: str = None,
                   max_results: int = 100,
                   query: str = None) -> Dict[str, Any]:
        """List files in Drive"""
        self._ensure_service()
        
        try:
            query_parts = []
            
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            if mime_type:
                query_parts.append(f"mimeType = '{mime_type}'")
            if query:
                query_parts.append(query)
            
            full_query = " and ".join(query_parts) if query_parts else None
            
            results = self.service.files().list(
                q=full_query,
                pageSize=max_results,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink, thumbnailLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            return {
                "success": True,
                "files": results.get('files', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_files(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """Search files by name or content"""
        self._ensure_service()
        
        try:
            # Build search query
            search_query = f"name contains '{query}' or fullText contains '{query}'"
            
            results = self.service.files().list(
                q=search_query,
                pageSize=max_results,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, thumbnailLink)"
            ).execute()
            
            return {
                "success": True,
                "files": results.get('files', []),
                "query": query
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_file(self, file_path: str, 
                    folder_id: str = None,
                    name: str = None,
                    mime_type: str = None) -> Dict[str, Any]:
        """Upload a file to Drive"""
        self._ensure_service()
        
        try:
            file_name = name or os.path.basename(file_path)
            file_mime = mime_type or 'application/octet-stream'
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id] if folder_id else []
            }
            
            media = MediaFileUpload(
                file_path,
                mimetype=file_mime,
                resumable=True
            )
            
            result = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, thumbnailLink'
            ).execute()
            
            return {
                "success": True,
                "file_id": result['id'],
                "file_name": result['name'],
                "link": result.get('webViewLink')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_content(self, content: str, 
                       file_name: str,
                       mime_type: str = 'text/plain',
                       folder_id: str = None) -> Dict[str, Any]:
        """Upload content as a file"""
        self._ensure_service()
        
        try:
            file_metadata = {
                'name': file_name,
                'parents': [folder_id] if folder_id else []
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode()),
                mimetype=mime_type,
                resumable=True
            )
            
            result = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                "success": True,
                "file_id": result['id'],
                "file_name": result['name'],
                "link": result.get('webViewLink')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_file(self, file_id: str, 
                      destination_path: str = None) -> Dict[str, Any]:
        """Download a file from Drive"""
        self._ensure_service()
        
        try:
            # Get file metadata
            file_metadata = self.service.files().get(fileId=file_id).execute()
            
            if destination_path:
                request = self.service.files().get_media(fileId=file_id)
                
                with open(destination_path, 'wb') as f:
                    f.write(request.execute())
                
                return {
                    "success": True,
                    "file_id": file_id,
                    "file_name": file_metadata['name'],
                    "saved_to": destination_path
                }
            else:
                # Return content as bytes
                request = self.service.files().get_media(fileId=file_id)
                content = request.execute()
                
                return {
                    "success": True,
                    "file_id": file_id,
                    "file_name": file_metadata['name'],
                    "content": content
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_folder(self, name: str, 
                      parent_id: str = None) -> Dict[str, Any]:
        """Create a folder in Drive"""
        self._ensure_service()
        
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id] if parent_id else []
            }
            
            result = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                "success": True,
                "folder_id": result['id'],
                "folder_name": result['name'],
                "link": result.get('webViewLink')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete a file or folder"""
        self._ensure_service()
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            
            return {
                "success": True,
                "file_id": file_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def move_file(self, file_id: str, 
                  new_folder_id: str) -> Dict[str, Any]:
        """Move a file to a different folder"""
        self._ensure_service()
        
        try:
            # Get current parents
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            
            # Move to new folder
            result = self.service.files().update(
                fileId=file_id,
                addParents=new_folder_id,
                removeParents=previous_parents,
                fields='id, name, parents'
            ).execute()
            
            return {
                "success": True,
                "file_id": result['id'],
                "new_parents": result.get('parents', [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def share_file(self, file_id: str, 
                   email: str,
                   role: str = 'reader',
                   notify: bool = True) -> Dict[str, Any]:
        """Share a file with someone"""
        self._ensure_service()
        
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            result = self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=notify
            ).execute()
            
            return {
                "success": True,
                "file_id": file_id,
                "permission_id": result.get('id'),
                "shared_with": email
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_storage_quota(self) -> Dict[str, Any]:
        """Get storage quota information"""
        self._ensure_service()
        
        try:
            about = self.service.about().get(
                fields='storageQuota'
            ).execute()
            
            quota = about.get('storageQuota', [])
            
            return {
                "success": True,
                "storage_quota": quota
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_doc_from_text(self, title: str, 
                            content: str,
                            folder_id: str = None) -> Dict[str, Any]:
        """Create a Google Doc from text"""
        self._ensure_service()
        
        try:
            file_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.document',
                'parents': [folder_id] if folder_id else []
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode()),
                mimetype='text/plain',
                resumable=True
            )
            
            result = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                "success": True,
                "document_id": result['id'],
                "title": result['name'],
                "link": result.get('webViewLink')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def batch_delete(self, file_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple files"""
        self._ensure_service()
        
        try:
            for file_id in file_ids:
                self.service.files().delete(fileId=file_id).execute()
            
            return {
                "success": True,
                "deleted_count": len(file_ids)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def list_files(user_id: str, folder_id: str = None, max_results: int = 100) -> Dict[str, Any]:
    """List files in Drive"""
    service = DriveService(user_id)
    return service.list_files(folder_id, max_results=max_results)


def upload_file(user_id: str, file_path: str, folder_id: str = None) -> Dict[str, Any]:
    """Upload a file"""
    service = DriveService(user_id)
    return service.upload_file(file_path, folder_id)


def search_files(user_id: str, query: str, max_results: int = 20) -> Dict[str, Any]:
    """Search files"""
    service = DriveService(user_id)
    return service.search_files(query, max_results)
