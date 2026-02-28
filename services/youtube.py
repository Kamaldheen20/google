"""
YouTube Service
Provides integration with YouTube API for video management
"""

from typing import Optional, List, Dict, Any

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class YouTubeService:
    """YouTube API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('youtube', 'v3', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with YouTube")
    
    def search_videos(self, query: str,
                      max_results: int = 10,
                      type_: str = 'video') -> Dict[str, Any]:
        """Search for videos"""
        self._ensure_service()
        
        try:
            result = self.service.search().list(
                q=query,
                type=type_,
                part='id,snippet',
                maxResults=max_results
            ).execute()
            
            videos = []
            for item in result.get('items', []):
                videos.append({
                    "video_id": item['id']['videoId'],
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description'],
                    "channel": item['snippet']['channelTitle'],
                    "thumbnail": item['snippet']['thumbnails']['default']['url'],
                    "published_at": item['snippet']['publishedAt']
                })
            
            return {
                "success": True,
                "videos": videos,
                "total": len(videos)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """Get video details"""
        self._ensure_service()
        
        try:
            result = self.service.videos().list(
                part='snippet,statistics',
                id=video_id
            ).execute()
            
            if result['items']:
                item = result['items'][0]
                return {
                    "success": True,
                    "video_id": video_id,
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description'],
                    "view_count": item['statistics'].get('viewCount'),
                    "like_count": item['statistics'].get('likeCount'),
                    "comment_count": item['statistics'].get('commentCount')
                }
            else:
                return {
                    "success": False,
                    "error": "Video not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_my_channel(self) -> Dict[str, Any]:
        """Get authenticated user's channel"""
        self._ensure_service()
        
        try:
            result = self.service.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if result['items']:
                channel = result['items'][0]
                return {
                    "success": True,
                    "channel_id": channel['id'],
                    "title": channel['snippet']['title'],
                    "description": channel['snippet']['description'],
                    "subscriber_count": channel['statistics'].get('subscriberCount'),
                    "video_count": channel['statistics'].get('videoCount'),
                    "view_count": channel['statistics'].get('viewCount')
                }
            else:
                return {
                    "success": False,
                    "error": "No channel found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_playlists(self, max_results: int = 50) -> Dict[str, Any]:
        """List user's playlists"""
        self._ensure_service()
        
        try:
            result = self.service.playlists().list(
                part='snippet,contentDetails',
                mine=True,
                maxResults=max_results
            ).execute()
            
            playlists = []
            for item in result.get('items', []):
                playlists.append({
                    "playlist_id": item['id'],
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description'],
                    "video_count": item['contentDetails']['itemCount']
                })
            
            return {
                "success": True,
                "playlists": playlists,
                "total": len(playlists)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_playlist(self, title: str,
                       description: str = None,
                       privacy_status: str = 'private') -> Dict[str, Any]:
        """Create a new playlist"""
        self._ensure_service()
        
        try:
            body = {
                'snippet': {
                    'title': title,
                    'description': description or ''
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }
            
            result = self.service.playlists().insert(
                part='snippet,status',
                body=body
            ).execute()
            
            return {
                "success": True,
                "playlist_id": result['id'],
                "title": result['snippet']['title']
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_video_to_playlist(self, playlist_id: str,
                             video_id: str) -> Dict[str, Any]:
        """Add a video to playlist"""
        self._ensure_service()
        
        try:
            body = {
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
            
            result = self.service.playlistItems().insert(
                part='snippet',
                body=body
            ).execute()
            
            return {
                "success": True,
                "playlist_item_id": result['id']
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_subscriptions(self, max_results: int = 50) -> Dict[str, Any]:
        """Get user's subscriptions"""
        self._ensure_service()
        
        try:
            result = self.service.subscriptions().list(
                part='snippet',
                mine=True,
                maxResults=max_results
            ).execute()
            
            subscriptions = []
            for item in result.get('items', []):
                subscriptions.append({
                    "channel_id": item['snippet']['resourceId']['channelId'],
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description']
                })
            
            return {
                "success": True,
                "subscriptions": subscriptions,
                "total": len(subscriptions)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def search_videos(user_id: str, query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for videos"""
    service = YouTubeService(user_id)
    return service.search_videos(query, max_results)


def get_my_channel(user_id: str) -> Dict[str, Any]:
    """Get authenticated user's channel"""
    service = YouTubeService(user_id)
    return service.get_my_channel()
