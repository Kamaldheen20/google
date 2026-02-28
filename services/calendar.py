"""
Google Calendar Service
Provides integration with Google Calendar API for event management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pytz

from googleapiclient.discovery import build
from auth.google_auth import auth_handler


class CalendarService:
    """Google Calendar API Service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials = auth_handler.load_credentials(user_id)
        
        if self.credentials:
            self.service = build('calendar', 'v3', credentials=self.credentials)
        else:
            self.service = None
    
    def _ensure_service(self):
        """Ensure service is initialized"""
        if not self.service:
            raise ValueError("User not authenticated with Google Calendar")
    
    def _parse_datetime(self, dt):
        """Parse datetime to ISO format"""
        if isinstance(dt, str):
            return dt
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            return dt.isoformat()
        return None
    
    def create_event(self, summary: str, 
                     start_time: datetime,
                     end_time: datetime,
                     description: str = None,
                     location: str = None,
                     attendees: List[str] = None,
                     timezone: str = 'UTC',
                     reminders: bool = True) -> Dict[str, Any]:
        """Create a calendar event"""
        self._ensure_service()
        
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': self._parse_datetime(start_time),
                    'timeZone': timezone
                },
                'end': {
                    'dateTime': self._parse_datetime(end_time),
                    'timeZone': timezone
                }
            }
            
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            if reminders:
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30}
                    ]
                }
            
            result = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all' if attendees else 'none'
            ).execute()
            
            return {
                "success": True,
                "event_id": result['id'],
                "summary": result['summary'],
                "html_link": result.get('htmlLink'),
                "start": result['start'].get('dateTime'),
                "end": result['end'].get('dateTime')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_quick_event(self, text: str) -> Dict[str, Any]:
        """Create an event from natural language text"""
        self._ensure_service()
        
        try:
            result = self.service.events().quickAdd(
                calendarId='primary',
                text=text
            ).execute()
            
            return {
                "success": True,
                "event_id": result['id'],
                "summary": result['summary'],
                "html_link": result.get('htmlLink')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_events(self, 
                   time_min: datetime = None,
                   time_max: datetime = None,
                   max_results: int = 100,
                   query: str = None) -> Dict[str, Any]:
        """Get calendar events"""
        self._ensure_service()
        
        try:
            now = datetime.utcnow()
            
            if time_min is None:
                time_min = now
            if time_max is None:
                time_max = now + timedelta(days=30)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=self._parse_datetime(time_min),
                timeMax=self._parse_datetime(time_max),
                maxResults=max_results,
                q=query,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            parsed_events = []
            for event in events:
                parsed_events.append({
                    "id": event['id'],
                    "summary": event.get('summary'),
                    "description": event.get('description'),
                    "start": event['start'].get('dateTime') or event['start'].get('date'),
                    "end": event['end'].get('dateTime') or event['end'].get('date'),
                    "location": event.get('location'),
                    "html_link": event.get('htmlLink'),
                    "status": event.get('status'),
                    "attendees": [a.get('email') for a in event.get('attendees', [])]
                })
            
            return {
                "success": True,
                "events": parsed_events,
                "total": len(parsed_events)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_todays_events(self) -> Dict[str, Any]:
        """Get today's events"""
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return self.get_events(time_min=start_of_day, time_max=end_of_day)
    
    def get_upcoming_events(self, max_results: int = 10) -> Dict[str, Any]:
        """Get upcoming events"""
        now = datetime.utcnow()
        return self.get_events(time_min=now, max_results=max_results)
    
    def update_event(self, event_id: str, 
                     **kwargs) -> Dict[str, Any]:
        """Update a calendar event"""
        self._ensure_service()
        
        try:
            # Get current event
            current_event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update fields
            for key, value in kwargs.items():
                if key == 'start_time':
                    current_event['start'] = {
                        'dateTime': self._parse_datetime(value),
                        'timeZone': current_event['start'].get('timeZone', 'UTC')
                    }
                elif key == 'end_time':
                    current_event['end'] = {
                        'dateTime': self._parse_datetime(value),
                        'timeZone': current_event['end'].get('timeZone', 'UTC')
                    }
                elif key in ['summary', 'description', 'location']:
                    current_event[key] = value
                elif key == 'attendees':
                    current_event['attendees'] = [{'email': email} for email in value]
            
            result = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=current_event,
                sendUpdates='all'
            ).execute()
            
            return {
                "success": True,
                "event_id": result['id'],
                "updated": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a calendar event"""
        self._ensure_service()
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            return {
                "success": True,
                "event_id": event_id,
                "deleted": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def find_free_busy(self,
                       time_min: datetime,
                       time_max: datetime,
                       calendars: List[str] = None) -> Dict[str, Any]:
        """Find free/busy information"""
        self._ensure_service()
        
        try:
            body = {
                'timeMin': self._parse_datetime(time_min),
                'timeMax': self._parse_datetime(time_max),
                'items': [{'id': cal} for cal in (calendars or ['primary'])]
            }
            
            result = self.service.freebusy().query(body=body).execute()
            
            return {
                "success": True,
                "calendars": result.get('calendars', {})
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_slots(self,
                            time_min: datetime,
                            time_max: datetime,
                            duration_minutes: int = 30,
                            calendars: List[str] = None) -> Dict[str, Any]:
        """Find available time slots"""
        self._ensure_service()
        
        try:
            # Get free/busy info
            busy_result = self.find_free_busy(time_min, time_max, calendars)
            
            if not busy_result['success']:
                return busy_result
            
            # Get existing events
            events_result = self.get_events(time_min, time_max)
            
            if not events_result['success']:
                return events_result
            
            # Calculate busy periods
            busy_periods = []
            for cal_id, cal_data in busy_result['calendars'].items():
                for period in cal_data.get('busy', []):
                    busy_periods.append({
                        'start': period.get('start'),
                        'end': period.get('end')
                    })
            
            # Add existing events to busy periods
            for event in events_result['events']:
                busy_periods.append({
                    'start': event['start'],
                    'end': event['end']
                })
            
            # Sort busy periods
            busy_periods.sort(key=lambda x: x['start'])
            
            # Find available slots
            available_slots = []
            current_time = time_min
            
            while current_time < time_max:
                is_available = True
                for busy in busy_periods:
                    if busy['start'] <= current_time.isoformat() < busy['end']:
                        is_available = False
                        current_time = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                        break
                
                if is_available:
                    slot_end = current_time + timedelta(minutes=duration_minutes)
                    if slot_end <= time_max:
                        available_slots.append({
                            'start': current_time.isoformat(),
                            'end': slot_end.isoformat()
                        })
                    current_time = slot_end
                else:
                    current_time = current_time + timedelta(minutes=15)  # Check next 15 min
            
            return {
                "success": True,
                "available_slots": available_slots,
                "total": len(available_slots)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_meeting(self, summary: str,
                       attendees: List[str],
                       duration_minutes: int = 60,
                       description: str = None,
                       start_time: datetime = None) -> Dict[str, Any]:
        """Create a meeting with attendees"""
        if start_time is None:
            start_time = datetime.utcnow() + timedelta(hours=1)
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        return self.create_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            attendees=attendees
        )


# Convenience functions
def create_event(user_id: str, summary: str, start_time: datetime, 
                 end_time: datetime, **kwargs) -> Dict[str, Any]:
    """Create a calendar event"""
    service = CalendarService(user_id)
    return service.create_event(summary, start_time, end_time, **kwargs)


def get_events(user_id: str, time_min: datetime = None, 
               time_max: datetime = None, max_results: int = 100) -> Dict[str, Any]:
    """Get calendar events"""
    service = CalendarService(user_id)
    return service.get_events(time_min, time_max, max_results)


def create_meeting(user_id: str, summary: str, attendees: List[str],
                    duration_minutes: int = 60, description: str = None) -> Dict[str, Any]:
    """Create a meeting"""
    service = CalendarService(user_id)
    return service.create_meeting(summary, attendees, duration_minutes, description)
