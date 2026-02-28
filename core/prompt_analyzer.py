"""
Enhanced AI Prompt Analyzer
Analyzes natural language prompts to identify Google Workspace intents
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class IntentType(Enum):
    """Types of intents that can be detected"""
    # Gmail
    SEND_EMAIL = "send_email"
    READ_EMAILS = "read_emails"
    SEARCH_EMAILS = "search_emails"
    
    # Calendar
    CREATE_EVENT = "create_event"
    CREATE_MEETING = "create_meeting"
    SCHEDULE_MEETING = "schedule_meeting"
    GET_EVENTS = "get_events"
    
    # Drive
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"
    SEARCH_FILES = "search_files"
    CREATE_FOLDER = "create_folder"
    LIST_FILES = "list_files"
    
    # Docs
    CREATE_DOCUMENT = "create_document"
    READ_DOCUMENT = "read_document"
    UPDATE_DOCUMENT = "update_document"
    
    # Sheets
    CREATE_SPREADSHEET = "create_spreadsheet"
    READ_SPREADSHEET = "read_spreadsheet"
    WRITE_SPREADSHEET = "write_spreadsheet"
    
    # Slides
    CREATE_PRESENTATION = "create_presentation"
    
    # Meet
    CREATE_MEETING_SPACE = "create_meeting_space"
    
    # Chat
    SEND_MESSAGE = "send_message"
    LIST_SPACES = "list_spaces"
    
    # Translate
    TRANSLATE_TEXT = "translate_text"
    TRANSLATE_BATCH = "translate_batch"
    
    # Maps
    GEOCODE = "geocode"
    SEARCH_NEARBY = "search_nearby"
    GET_DIRECTIONS = "get_directions"
    
    # YouTube
    SEARCH_VIDEOS = "search_videos"
    GET_CHANNEL = "get_channel"
    
    # Keep
    CREATE_NOTE = "create_note"
    LIST_NOTES = "list_notes"
    SEARCH_NOTES = "search_notes"
    
    # Forms
    CREATE_FORM = "create_form"
    LIST_RESPONSES = "list_responses"
    
    # Contacts
    LIST_CONTACTS = "list_contacts"
    SEARCH_CONTACTS = "search_contacts"
    CREATE_CONTACT = "create_contact"
    
    # Photos
    LIST_ALBUMS = "list_albums"
    LIST_PHOTOS = "list_photos"
    SEARCH_PHOTOS = "search_photos"
    
    # General
    HELP = "help"
    UNKNOWN = "unknown"


# Keyword mappings for intent detection
INTENT_KEYWORDS = {
    IntentType.SEND_EMAIL: ['send', 'email', 'mail', 'write to', 'compose', 'message'],
    IntentType.READ_EMAILS: ['read', 'check', 'view', 'show', 'get emails', 'inbox'],
    IntentType.SEARCH_EMAILS: ['search', 'find', 'look for', 'filter'],
    
    IntentType.CREATE_EVENT: ['event', 'add event', 'create event', 'schedule event'],
    IntentType.CREATE_MEETING: ['meeting', 'schedule meeting', 'set up meeting', 'arrange meeting'],
    IntentType.GET_EVENTS: ['events', 'calendar', 'my schedule', 'upcoming', 'today'],
    
    IntentType.UPLOAD_FILE: ['upload', 'upload file', 'save file', 'add file'],
    IntentType.DOWNLOAD_FILE: ['download', 'get file', 'retrieve file'],
    IntentType.SEARCH_FILES: ['search files', 'find file', 'look for file', 'locate file'],
    IntentType.CREATE_FOLDER: ['folder', 'new folder', 'create folder', 'make folder'],
    IntentType.LIST_FILES: ['list files', 'my files', 'show files', 'browse'],
    
    IntentType.CREATE_DOCUMENT: ['document', 'doc', 'new doc', 'create doc', 'write document'],
    IntentType.READ_DOCUMENT: ['read doc', 'view doc', 'open doc', 'show doc content'],
    IntentType.UPDATE_DOCUMENT: ['update doc', 'edit doc', 'modify doc', 'add to doc'],
    
    IntentType.CREATE_SPREADSHEET: ['spreadsheet', 'sheet', 'excel', 'new sheet', 'create sheet'],
    IntentType.READ_SPREADSHEET: ['read sheet', 'view sheet', 'show sheet data'],
    IntentType.WRITE_SPREADSHEET: ['write sheet', 'update sheet', 'add to sheet', 'fill sheet'],
    
    IntentType.CREATE_PRESENTATION: ['presentation', 'slides', 'new presentation', 'create slides'],
    
    IntentType.CREATE_MEETING_SPACE: ['meet', 'video call', 'conference', 'new meeting'],
    
    IntentType.SEND_MESSAGE: ['message', 'send message', 'chat', 'dm'],
    IntentType.LIST_SPACES: ['spaces', 'chat spaces', 'rooms'],
    
    IntentType.TRANSLATE_TEXT: ['translate', 'translation', 'spanish', 'french', 'german', 'chinese', 'japanese'],
    IntentType.TRANSLATE_BATCH: ['translate multiple', 'batch translate'],
    
    IntentType.GEOCODE: ['address to coordinates', 'geocode', 'location from address'],
    IntentType.SEARCH_NEARBY: ['nearby', 'restaurants near', 'shops near', 'places near'],
    IntentType.GET_DIRECTIONS: ['directions', 'navigate', 'route', 'how to get'],
    
    IntentType.SEARCH_VIDEOS: ['videos', 'youtube', 'search videos', 'find videos'],
    IntentType.GET_CHANNEL: ['my channel', 'youtube channel', 'channel info'],
    
    IntentType.CREATE_NOTE: ['note', 'new note', 'create note', 'quick note'],
    IntentType.LIST_NOTES: ['notes', 'my notes', 'all notes'],
    IntentType.SEARCH_NOTES: ['search notes', 'find notes', 'look for notes'],
    
    IntentType.CREATE_FORM: ['form', 'survey', 'new form', 'create form'],
    IntentType.LIST_RESPONSES: ['responses', 'form responses', 'survey results'],
    
    IntentType.LIST_CONTACTS: ['contacts', 'my contacts', 'all contacts', 'address book'],
    IntentType.SEARCH_CONTACTS: ['search contacts', 'find contact', 'look for contact'],
    IntentType.CREATE_CONTACT: ['add contact', 'new contact', 'save contact', 'create contact'],
    
    IntentType.LIST_ALBUMS: ['albums', 'photo albums', 'my albums'],
    IntentType.LIST_PHOTOS: ['photos', 'pictures', 'my photos', 'all photos'],
    IntentType.SEARCH_PHOTOS: ['search photos', 'find photos', 'photos of'],
    
    IntentType.HELP: ['help', 'what can you do', 'capabilities', 'commands']
}


@dataclass
class Entity:
    """Extracted entity from prompt"""
    type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class DetectedIntent:
    """Detected intent with confidence"""
    intent_type: IntentType
    confidence: float
    service: str
    action: str
    entities: List[Entity] = field(default_factory=list)
    raw_prompt: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


class PromptAnalyzer:
    """Advanced NLP-based prompt analyzer for Google Workspace"""
    
    def __init__(self):
        self.email_pattern = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
        self.date_patterns = [
            r"(\d{1,2}/\d{1,2}/\d{2,4})",
            r"(\d{4}-\d{2}-\d{2})",
            r"(today|tomorrow|next week|next month)",
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"(\d{1,2}\s+(?:am|pm))",
        ]
        self.time_pattern = re.compile(r"(\d{1,2}):(\d{2})\s*(am|pm)?", re.IGNORECASE)
        self.amount_pattern = re.compile(r"\$[\d,]+(?:\.\d{2})?")
        
    def analyze(self, prompt: str) -> Dict[str, Any]:
        """
        Main entry point for prompt analysis
        Returns structured intent data
        """
        prompt_lower = prompt.lower().strip()
        
        # Extract entities
        entities = self._extract_entities(prompt)
        
        # Detect primary intent
        detected_intent = self._detect_intent(prompt_lower, entities)
        
        # Extract parameters
        parameters = self._extract_parameters(prompt, detected_intent, entities)
        
        # Generate structured response
        return {
            "success": True,
            "raw_prompt": prompt,
            "detected_intent": {
                "type": detected_intent.intent_type.value,
                "confidence": detected_intent.confidence,
                "service": detected_intent.service,
                "action": detected_intent.action
            },
            "entities": [
                {"type": e.type, "value": e.value, "confidence": e.confidence}
                for e in entities
            ],
            "parameters": parameters,
            "suggested_actions": self._suggest_actions(detected_intent)
        }
    
    def _extract_entities(self, prompt: str) -> List[Entity]:
        """Extract named entities from the prompt"""
        entities = []
        
        # Email addresses
        for match in self.email_pattern.finditer(prompt):
            entities.append(Entity(
                type="email",
                value=match.group(),
                start=match.start(),
                end=match.end()
            ))
        
        # Dates
        for pattern in self.date_patterns:
            for match in re.finditer(pattern, prompt, re.IGNORECASE):
                entities.append(Entity(
                    type="date",
                    value=match.group(),
                    start=match.start(),
                    end=match.end()
                ))
        
        # Times
        for match in self.time_pattern.finditer(prompt, re.IGNORECASE):
            entities.append(Entity(
                type="time",
                value=match.group(),
                start=match.start(),
                end=match.end()
            ))
        
        # Amounts
        for match in self.amount_pattern.finditer(prompt):
            entities.append(Entity(
                type="amount",
                value=match.group(),
                start=match.start(),
                end=match.end()
            ))
        
        # Phone numbers
        phone_pattern = re.compile(r"[\d\s\-\(\)\+]{10,}")
        for match in phone_pattern.finditer(prompt):
            if len(re.sub(r"[\s\-\(\)]", "", match.group())) >= 10:
                entities.append(Entity(
                    type="phone",
                    value=match.group(),
                    start=match.start(),
                    end=match.end()
                ))
        
        return entities
    
    def _detect_intent(self, prompt: str, entities: List[Entity]) -> DetectedIntent:
        """Detect the primary intent from the prompt"""
        
        # Check for help intent first
        for keyword in INTENT_KEYWORDS[IntentType.HELP]:
            if keyword in prompt:
                return DetectedIntent(
                    intent_type=IntentType.HELP,
                    confidence=1.0,
                    service="general",
                    action="help"
                )
        
        # Score each intent
        intent_scores = {}
        
        for intent_type, keywords in INTENT_KEYWORDS.items():
            if intent_type == IntentType.HELP:
                continue
            
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in prompt:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                # Calculate confidence based on match density
                confidence = min(0.5 + (score * 0.2), 0.95)
                intent_scores[intent_type] = {
                    "score": score,
                    "confidence": confidence,
                    "matched_keywords": matched_keywords
                }
        
        if intent_scores:
            # Get highest scoring intent
            best_intent = max(intent_scores.items(), key=lambda x: x[1]["score"])
            intent_type = best_intent[0]
            score_data = best_intent[1]
            
            # Map intent to service and action
            service, action = self._get_service_action(intent_type)
            
            return DetectedIntent(
                intent_type=intent_type,
                confidence=score_data["confidence"],
                service=service,
                action=action,
                entities=entities,
                raw_prompt=prompt
            )
        
        # No intent detected
        return DetectedIntent(
            intent_type=IntentType.UNKNOWN,
            confidence=0.0,
            service="unknown",
            action="unknown",
            entities=entities,
            raw_prompt=prompt
        )
    
    def _get_service_action(self, intent_type: IntentType) -> tuple:
        """Map intent type to service and action names"""
        mapping = {
            IntentType.SEND_EMAIL: ("gmail", "send_email"),
            IntentType.READ_EMAILS: ("gmail", "read_emails"),
            IntentType.SEARCH_EMAILS: ("gmail", "search_emails"),
            IntentType.CREATE_EVENT: ("calendar", "create_event"),
            IntentType.CREATE_MEETING: ("calendar", "create_meeting"),
            IntentType.SCHEDULE_MEETING: ("calendar", "create_event"), # Map schedule meeting to create event
            IntentType.GET_EVENTS: ("calendar", "get_events"),
            IntentType.UPLOAD_FILE: ("drive", "upload_file"),
            IntentType.DOWNLOAD_FILE: ("drive", "download_file"),
            IntentType.SEARCH_FILES: ("drive", "search_files"),
            IntentType.CREATE_FOLDER: ("drive", "create_folder"),
            IntentType.LIST_FILES: ("drive", "list_files"),
            IntentType.CREATE_DOCUMENT: ("docs", "create_document"),
            IntentType.READ_DOCUMENT: ("docs", "read_document"),
            IntentType.UPDATE_DOCUMENT: ("docs", "update_document"),
            IntentType.CREATE_SPREADSHEET: ("sheets", "create_spreadsheet"),
            IntentType.READ_SPREADSHEET: ("sheets", "read_spreadsheet"),
            IntentType.WRITE_SPREADSHEET: ("sheets", "write_spreadsheet"),
            IntentType.CREATE_PRESENTATION: ("slides", "create_presentation"),
            IntentType.CREATE_MEETING_SPACE: ("meet", "create_meeting_space"),
            IntentType.SEND_MESSAGE: ("chat", "send_message"),
            IntentType.LIST_SPACES: ("chat", "list_spaces"),
            IntentType.TRANSLATE_TEXT: ("translate", "translate"),
            IntentType.TRANSLATE_BATCH: ("translate", "translate_batch"),
            IntentType.GEOCODE: ("maps", "geocode"),
            IntentType.SEARCH_NEARBY: ("maps", "search_nearby"),
            IntentType.GET_DIRECTIONS: ("maps", "get_directions"),
            IntentType.SEARCH_VIDEOS: ("youtube", "search_videos"),
            IntentType.GET_CHANNEL: ("youtube", "get_channel"),
            IntentType.CREATE_NOTE: ("keep", "create_note"),
            IntentType.LIST_NOTES: ("keep", "list_notes"),
            IntentType.SEARCH_NOTES: ("keep", "search_notes"),
            IntentType.CREATE_FORM: ("forms", "create_form"),
            IntentType.LIST_RESPONSES: ("forms", "list_responses"),
            IntentType.LIST_CONTACTS: ("contacts", "list_contacts"),
            IntentType.SEARCH_CONTACTS: ("contacts", "search_contacts"),
            IntentType.CREATE_CONTACT: ("contacts", "create_contact"),
            IntentType.LIST_ALBUMS: ("photos", "list_albums"),
            IntentType.LIST_PHOTOS: ("photos", "list_photos"),
            IntentType.SEARCH_PHOTOS: ("photos", "search_photos"),
            IntentType.HELP: ("general", "help"),
            IntentType.UNKNOWN: ("unknown", "unknown")
        }
        
        return mapping.get(intent_type, ("unknown", "unknown"))
    
    def _extract_parameters(self, prompt: str, intent: DetectedIntent, 
                           entities: List[Entity]) -> Dict[str, Any]:
        """Extract parameters for the detected intent"""
        parameters = {}
        
        # Get email entities
        emails = [e for e in entities if e.type == "email"]
        if emails:
            parameters["recipients"] = [e.value for e in emails]
        
        # Get date entities
        dates = [e for e in entities if e.type == "date"]
        if dates:
            parameters["dates"] = [e.value for e in dates]
        
        # Get time entities
        times = [e for e in entities if e.type == "time"]
        if times:
            parameters["times"] = [e.value for e in times]
        
        # Get amount entities
        amounts = [e for e in entities if e.type == "amount"]
        if amounts:
            parameters["amounts"] = [e.value for e in amounts]
        
        # Get phone entities
        phones = [e for e in entities if e.type == "phone"]
        if phones:
            parameters["phones"] = [e.value for e in phones]
        
        # Intent-specific parameter extraction
        if intent.intent_type == IntentType.TRANSLATE_TEXT:
            # Extract target language
            languages = ['spanish', 'french', 'german', 'chinese', 'japanese', 
                        'korean', 'portuguese', 'italian', 'russian', 'arabic',
                        'hindi', 'english', 'dutch', 'polish', 'turkish']
            for lang in languages:
                if lang in prompt.lower():
                    parameters["target_language"] = lang
                    break
        
        if intent.intent_type == IntentType.SEARCH_NEARBY:
            # Extract query and location
            for entity in entities:
                if entity.type == "location":
                    parameters["location"] = entity.value
        
        if intent.intent_type == IntentType.GET_DIRECTIONS:
            # Extract origin and destination
            words = prompt.lower().split()
            if "from" in words and "to" in words:
                from_idx = words.index("from")
                to_idx = words.index("to")
                if from_idx < to_idx:
                    parameters["origin"] = " ".join(words[from_idx+1:to_idx])
                    parameters["destination"] = " ".join(words[to_idx+1:])
        
        # Extract quoted text for content
        quoted = re.findall(r'"([^"]+)"', prompt) or re.findall(r"'([^']+)'", prompt)
        if quoted:
            parameters["quoted_text"] = quoted
        
        # Extract numbers
        numbers = re.findall(r'\d+', prompt)
        if numbers:
            parameters["numbers"] = numbers
        
        return parameters
    
    def _suggest_actions(self, intent: DetectedIntent) -> List[str]:
        """Suggest follow-up actions based on detected intent"""
        suggestions = {
            IntentType.SEND_EMAIL: [
                "Would you like me to add a subject line?",
                "Should I include any attachments?"
            ],
            IntentType.CREATE_MEETING: [
                "What duration should the meeting be?",
                "Do you want to send calendar invites?"
            ],
            IntentType.CREATE_DOCUMENT: [
                "Would you like to add content to the document?",
                "Should I share this document with anyone?"
            ],
            IntentType.TRANSLATE_TEXT: [
                "Would you like me to translate to another language?"
            ],
            IntentType.UNKNOWN: [
                "Try asking: 'Send an email to John'",
                "Try: 'Schedule a meeting tomorrow at 3pm'",
                "Try: 'Create a new document'"
            ]
        }
        
        return suggestions.get(intent.intent_type, [])
    
    def batch_analyze(self, prompts: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple prompts"""
        return [self.analyze(prompt) for prompt in prompts]


# Singleton instance
analyzer = PromptAnalyzer()


def analyze_prompt(prompt: str) -> Dict[str, Any]:
    """Analyze a single prompt"""
    return analyzer.analyze(prompt)


def batch_analyze_prompts(prompts: List[str]) -> List[Dict[str, Any]]:
    """Analyze multiple prompts"""
    return analyzer.batch_analyze(prompts)
