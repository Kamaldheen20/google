"""
Google Photos Service
Provides integration with Google Photos API for photo management
"""

from typing import Optional, List, Dict, Any

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class PhotosService:
    """Google Photos API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('photoslibrary', 'v1', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Photos")
    
    def list_albums(self, page_size: int = 50) -> Dict[str, Any]:
        """List all albums"""
        self._ensure_service()
        
        try:
            result = self.service.albums().list(
                pageSize=page_size
            ).execute()
            
            albums = result.get('albums', [])
            
            parsed_albums = []
            for album in albums:
                parsed_albums.append({
                    "album_id": album.get('id'),
                    "title": album.get('title'),
                    "photo_count": album.get('mediaItemsCount'),
                    "cover_url": album.get('coverPhotoBaseUrl'),
                    "created": album.get('productUrl')
                })
            
            return {
                "success": True,
                "albums": parsed_albums,
                "total": len(parsed_albums)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_photos(self, page_size: int = 100,
                    album_id: str = None) -> Dict[str, Any]:
        """List photos"""
        self._ensure_service()
        
        try:
            if album_id:
                result = self.service.mediaItems().search(
                    body={
                        'albumId': album_id,
                        'pageSize': page_size
                    }
                ).execute()
            else:
                result = self.service.mediaItems().list(
                    pageSize=page_size
                ).execute()
            
            photos = result.get('mediaItems', [])
            
            parsed_photos = []
            for photo in photos:
                parsed_photos.append({
                    "photo_id": photo.get('id'),
                    "filename": photo.get('filename'),
                    "base_url": photo.get('baseUrl'),
                    "mime_type": photo.get('mimeType'),
                    "created_at": photo.get('creationTime'),
                    "width": photo.get('mediaMetadata', {}).get('width'),
                    "height": photo.get('mediaMetadata', {}).get('height')
                })
            
            return {
                "success": True,
                "photos": parsed_photos,
                "total": len(parsed_photos)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_photos(self, query: str,
                      page_size: int = 50) -> Dict[str, Any]:
        """Search photos by content (labels)"""
        self._ensure_service()
        
        try:
            result = self.service.mediaItems().search(
                body={
                    'pageSize': page_size,
                    'filters': {
                        'contentFilter': {
                            'filterType': 'LABELS',
                            'values': [query]
                        }
                    }
                }
            ).execute()
            
            photos = result.get('mediaItems', [])
            
            return {
                "success": True,
                "photos": photos,
                "total": len(photos)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_photo(self, photo_id: str) -> Dict[str, Any]:
        """Get a specific photo"""
        self._ensure_service()
        
        try:
            result = self.service.mediaItems().get(
                mediaItemId=photo_id
            ).execute()
            
            return {
                "success": True,
                "photo": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_album(self, title: str) -> Dict[str, Any]:
        """Create a new album"""
        self._ensure_service()
        
        try:
            result = self.service.albums().create(
                body={'album': {'title': title}}
            ).execute()
            
            return {
                "success": True,
                "album_id": result.get('id'),
                "title": result.get('title'),
                "url": result.get('productUrl')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def share_album(self, album_id: str) -> Dict[str, Any]:
        """Share an album (creates shared album)"""
        self._ensure_service()
        
        try:
            result = self.service.sharedAlbums().share(
                albumId=album_id,
                body={
                    'sharedAlbumOptions': {
                        'isCollaborative': True,
                        'isCommentable': True
                    }
                }
            ).execute()
            
            return {
                "success": True,
                "share_token": result.get('shareToken'),
                "shareable_url": result.get('shareableUrl')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def list_albums(user_id: str, page_size: int = 50) -> Dict[str, Any]:
    """List all albums"""
    service = PhotosService(user_id)
    return service.list_albums(page_size)


def list_photos(user_id: str, page_size: int = 100,
                album_id: str = None) -> Dict[str, Any]:
    """List photos"""
    service = PhotosService(user_id)
    return service.list_photos(page_size, album_id)


def search_photos(user_id: str, query: str,
                  page_size: int = 50) -> Dict[str, Any]:
    """Search photos"""
    service = PhotosService(user_id)
    return service.search_photos(query, page_size)
