"""
Google Maps Service
Provides integration with Google Maps API for location services
"""

from typing import Optional, List, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth.google_auth import auth_handler


class MapsService:
    """Google Maps API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('mapsplatform', 'v1', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Maps")
    
    def geocode(self, address: str) -> Dict[str, Any]:
        """Convert address to coordinates"""
        self._ensure_service()
        
        try:
            result = self.service.geocode().get(address=address).execute()
            
            if result:
                location = result[0]['geometry']['location']
                
                return {
                    "success": True,
                    "address": result[0]['formatted_address'],
                    "location": location,
                    "place_id": result[0].get('place_id')
                }
            else:
                return {
                    "success": False,
                    "error": "Address not found"
                }
        except HttpError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """Convert coordinates to address"""
        self._ensure_service()
        
        try:
            result = self.service.geocode().get(
                latlng={'lat': lat, 'lng': lng}
            ).execute()
            
            if result:
                return {
                    "success": True,
                    "address": result[0]['formatted_address'],
                    "location": {'lat': lat, 'lng': lng}
                }
            else:
                return {
                    "success": False,
                    "error": "Location not found"
                }
        except HttpError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_nearby(self, location: Dict[str, float],
                     keyword: str,
                     radius: int = 5000,
                     type_: str = None) -> Dict[str, Any]:
        """Search nearby places"""
        self._ensure_service()
        
        try:
            result = self.service.places().searchNearby(
                location=location,
                radius=radius,
                keyword=keyword,
                type=type_
            ).execute()
            
            return {
                "success": True,
                "places": result.get('places', []),
                "total": len(result.get('places', []))
            }
        except HttpError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def text_search(self, query: str,
                   location: Dict[str, float] = None) -> Dict[str, Any]:
        """Search places by text query"""
        self._ensure_service()
        
        try:
            result = self.service.places().searchText(
                textQuery=query,
                locationBias=location
            ).execute()
            
            return {
                "success": True,
                "places": result.get('places', []),
                "total": len(result.get('places', []))
            }
        except HttpError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_directions(self, origin: str,
                      destination: str,
                      mode: str = 'driving') -> Dict[str, Any]:
        """Get directions between two points"""
        self._ensure_service()
        
        try:
            result = self.service.directions().get(
                origin=origin,
                destination=destination,
                mode=mode
            ).execute()
            
            route = result['routes'][0]
            
            return {
                "success": True,
                "distance": route['legs'][0]['distance']['text'],
                "duration": route['legs'][0]['duration']['text'],
                "steps": [
                    step['html_instructions'] 
                    for step in route['legs'][0]['steps']
                ]
            }
        except HttpError as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions
def geocode(user_id: str, address: str) -> Dict[str, Any]:
    """Convert address to coordinates"""
    service = MapsService(user_id)
    return service.geocode(address)


def search_nearby(user_id: str, location: Dict[str, float],
                  keyword: str, radius: int = 5000) -> Dict[str, Any]:
    """Search nearby places"""
    service = MapsService(user_id)
    return service.search_nearby(location, keyword, radius)


def get_directions(user_id: str, origin: str,
                   destination: str, mode: str = 'driving') -> Dict[str, Any]:
    """Get directions"""
    service = MapsService(user_id)
    return service.get_directions(origin, destination, mode)
