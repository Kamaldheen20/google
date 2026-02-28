"""
Google Workspace Services Package
Unified interface to all Google Workspace APIs
"""

from .gmail import GmailService, send_email, read_emails
from .drive import DriveService, list_files, upload_file, search_files
from .calendar import CalendarService, create_event, get_events, create_meeting
from .docs import DocsService, create_document, get_document, read_document
from .sheets import SheetsService, create_spreadsheet, read_range, write_range
from .slides import SlidesService, create_presentation, get_presentation
from .meet import MeetService, create_meeting_space, get_meeting_space
from .chat import ChatService, list_spaces, send_message
from .translate import TranslateService, translate, translate_batch
from .maps import MapsService, geocode, search_nearby, get_directions
from .youtube import YouTubeService, search_videos, get_my_channel
from .keep import KeepService, list_notes, create_note, search_notes
from .forms import FormsService, create_form, list_responses
from .contacts import ContactsService, list_contacts, search_contacts, create_contact 
from .photos import PhotosService, list_albums, list_photos, search_photos # Removed add_photo_to_album due to API limitations for non-shared albums


# Service mapping for unified access
SERVICE_MAP = {
    'gmail': GmailService,
    'drive': DriveService,
    'calendar': CalendarService,
    'docs': DocsService,
    'sheets': SheetsService,
    'slides': SlidesService,
    'meet': MeetService,
    'chat': ChatService,
    'translate': TranslateService,
    'maps': MapsService,
    'youtube': YouTubeService,
    'keep': KeepService,
    'forms': FormsService,
    'contacts': ContactsService,
    'photos': PhotosService
}


def get_service(service_name: str, user_id: str):
    """Get a service instance by name"""
    service_class = SERVICE_MAP.get(service_name.lower())
    if service_class:
        return service_class(user_id)
    return None


# Export all services and functions
__all__ = [
    # Gmail
    'GmailService', 'send_email', 'read_emails',
    # Drive
    'DriveService', 'list_files', 'upload_file', 'search_files',
    # Calendar
    'CalendarService', 'create_event', 'get_events', 'create_meeting',
    # Docs
    'DocsService', 'create_document', 'get_document', 'read_document',
    # Sheets
    'SheetsService', 'create_spreadsheet', 'read_range', 'write_range',
    # Slides
    'SlidesService', 'create_presentation', 'get_presentation',
    # Meet
    'MeetService', 'create_meeting_space', 'get_meeting_space',
    # Chat
    'ChatService', 'list_spaces', 'send_message',
    # Translate
    'TranslateService', 'translate', 'translate_batch',
    # Maps
    'MapsService', 'geocode', 'search_nearby', 'get_directions',
    # YouTube
    'YouTubeService', 'search_videos', 'get_my_channel',
    # Keep
    'KeepService', 'list_notes', 'create_note', 'search_notes',
    # Forms
    'FormsService', 'create_form', 'list_responses',
    # Contacts
    'ContactsService', 'list_contacts', 'search_contacts', 'create_contact',
    # Photos
    'PhotosService', 'list_albums', 'list_photos', 'search_photos',
    # Utility
    'get_service', 'SERVICE_MAP'
]
