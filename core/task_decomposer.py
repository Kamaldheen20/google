"""
Task Decomposer
Breaks down complex prompts into actionable tasks
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):
    """Status of a task"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """A single executable task"""
    task_id: str
    service: str
    action: str
    parameters: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    depends_on: List[str] = None
    result: Dict[str, Any] = None
    error: str = None
    created_at: str = None
    completed_at: str = None


class TaskDecomposer:
    """Decomposes complex prompts into executable tasks"""
    
    def __init__(self):
        self.task_counter = 0
    
    def decompose(self, intent_data: Dict[str, Any]) -> List[Task]:
        """
        Decompose an intent into executable tasks
        """
        tasks = []
        intent_type = intent_data.get('detected_intent', {}).get('type', 'unknown')
        parameters = intent_data.get('parameters', {})
        
        # Route to appropriate decomposer
        if intent_type.startswith('send_email'):
            tasks = self._decompose_send_email(parameters)
        elif intent_type in ['create_event', 'create_meeting', 'schedule_meeting']:
            tasks = self._decompose_create_event(parameters)
        elif intent_type in ['create_document', 'read_document', 'update_document']:
            tasks = self._decompose_document_operation(intent_type, parameters)
        elif intent_type in ['create_spreadsheet', 'read_spreadsheet', 'write_spreadsheet']:
            tasks = self._decompose_spreadsheet_operation(intent_type, parameters)
        elif intent_type.startswith('translate'):
            tasks = self._decompose_translate(parameters)
        elif intent_type in ['search_files', 'upload_file', 'download_file', 'list_files']:
            tasks = self._decompose_drive_operation(intent_type, parameters)
        elif intent_type.startswith('create_meeting_space'):
            tasks = self._decompose_meeting_space(parameters)
        elif intent_type.startswith('send_message'):
            tasks = self._decompose_send_message(parameters)
        elif intent_type in ['search_videos', 'get_channel']:
            tasks = self._decompose_youtube_operation(intent_type, parameters)
        elif intent_type.startswith('create_note'):
            tasks = self._decompose_create_note(parameters)
        elif intent_type.startswith('create_form'):
            tasks = self._decompose_create_form(parameters)
        elif intent_type in ['create_contact', 'search_contacts', 'list_contacts']:
            tasks = self._decompose_contact_operation(intent_type, parameters)
        elif intent_type.startswith('list_albums'):
            tasks = self._decompose_list_albums(parameters)
        elif intent_type.startswith('list_photos'):
            tasks = self._decompose_list_photos(parameters)
        else:
            # Single task for simple operations
            tasks = [self._create_single_task(intent_data)]
        
        return tasks
    
    def _create_task_id(self) -> str:
        """Generate unique task ID"""
        self.task_counter += 1
        return f"task_{self.task_counter}"
    
    def _create_single_task(self, intent_data: Dict[str, Any]) -> Task:
        """Create a single task from intent data"""
        intent = intent_data.get('detected_intent', {})
        return Task(
            task_id=self._create_task_id(),
            service=intent.get('service', 'unknown'),
            action=intent.get('action', 'unknown'),
            parameters=intent_data.get('parameters', {}),
            priority=TaskPriority.MEDIUM
        )
    
    def _decompose_send_email(self, params: Dict[str, Any]) -> List[Task]:
        """Decompose email sending into tasks"""
        tasks = []
        
        # Task 1: Validate email addresses
        tasks.append(Task(
            task_id=self._create_task_id(),
            service="gmail",
            action="validate_email",
            parameters={"emails": params.get('recipients', [])},
            priority=TaskPriority.HIGH
        ))
        
        # Task 2: Send email
        tasks.append(Task(
            task_id=self._create_task_id(),
            service="gmail",
            action="send_email",
            parameters={
                "to": params.get('recipients', []),
                "subject": params.get('subject', ''),
                "body": params.get('body', params.get('quoted_text', [''])[0])
            },
            priority=TaskPriority.HIGH,
            depends_on=[tasks[0].task_id]
        ))
        
        return tasks
    
    def _decompose_create_event(self, params: Dict[str, Any]) -> List[Task]:
        """Decompose event creation into tasks"""
        tasks = []
        
        # Task 1: Check calendar availability
        tasks.append(Task(
            task_id=self._create_task_id(),
            service="calendar",
            action="check_availability",
            parameters={
                "start_time": params.get('start_time'),
                "end_time": params.get('end_time')
            },
            priority=TaskPriority.HIGH
        ))
        
        # Task 2: Create event
        tasks.append(Task(
            task_id=self._create_task_id(),
            service="calendar",
            action="create_event",
            parameters={
                "summary": params.get('summary', params.get('title', 'Meeting')),
                "description": params.get('description', ''),
                "start_time": params.get('start_time'),
                "end_time": params.get('end_time'),
                "attendees": params.get('recipients', [])
            },
            priority=TaskPriority.HIGH,
            depends_on=[tasks[0].task_id]
        ))
        
        return tasks
    
    def _decompose_document_operation(self, intent_type: str, params: Dict[str, Any]) -> List[Task]:
        """Decompose document operations into tasks"""
        tasks = []
        
        if intent_type == 'create_document':
            tasks.append(Task(
                task_id=self._create_task_id(),
                service="docs",
                action="create_document",
                parameters={"title": params.get('title', 'Untitled Document')},
                priority=TaskPriority.MEDIUM
            ))
            
            # Add content if provided
            if params.get('content'):
                tasks.append(Task(
                    task_id=self._create_task_id(),
                    service="docs",
                    action="append_text",
                    parameters={
                        "document_id": "{{" + tasks[0].task_id + "}}",
                        "text": params.get('content')
                    },
                    priority=TaskPriority.LOW,
                    depends_on=[tasks[0].task_id]
                ))
        
        elif intent_type == 'read_document':
            tasks.append(Task(
                task_id=self._create_task_id(),
                service="docs",
                action="read_document",
                parameters={"document_id": params.get('document_id')},
                priority=TaskPriority.MEDIUM
            ))
        
        return tasks
    
    def _decompose_spreadsheet_operation(self, intent_type: str, params: Dict[str, Any]) -> List[Task]:
        """Decompose spreadsheet operations into tasks"""
        tasks = []
        
        if intent_type == 'create_spreadsheet':
            tasks.append(Task(
                task_id=self._create_task_id(),
                service="sheets",
                action="create_spreadsheet",
                parameters={"title": params.get('title', 'Untitled Spreadsheet')},
                priority=TaskPriority.MEDIUM
            ))
        
        return tasks
    
    def _decompose_translate(self, params: Dict[str, Any]) -> List[Task]:
        """Decompose translation into tasks"""
        tasks = []
        
        texts = params.get('quoted_text', [params.get('text', '')])
        target_lang = params.get('target_language', 'en')
        
        for i, text in enumerate(texts):
            tasks.append(Task(
                task_id=self._create_task_id(),
                service="translate",
                action="translate",
                parameters={
                    "text": text,
                    "target_language": target_lang,
                    "source_language": params.get('source_language')
                },
                priority=TaskPriority.MEDIUM
            ))
        
        return tasks
    
    def _decompose_drive_operation(self, intent_type: str, params: Dict[str, Any]) -> List[Task]:
        """Decompose drive operations into tasks"""
        tasks = []
        
        if intent_type == 'search_files':
            tasks.append(Task(
                task_id=self._create_task_id(),
                service="drive",
                action="search_files",
                parameters={"query": params.get('query', params.get('text', ''))},
                priority=TaskPriority.MEDIUM
            ))
        
        elif intent_type == 'upload_file':
            tasks.append(Task(
                task_id=self._create_task_id(),
                service="drive",
                action="upload_file",
                parameters={
                    "file_path": params.get('file_path'),
                    "name": params.get('name'),
                    "folder_id": params.get('folder_id')
                },
                priority=TaskPriority.HIGH
            ))
        
        return tasks
    
    def _decompose_meeting_space(self, params: Dict[str, Any]) -> List[Task]:
        """Decompose meeting space creation into tasks"""
        return [
            Task(
                task_id=self._create_task_id(),
                service="meet",
                action="create_meeting_space",
                parameters={
                    "name": params.get('name', 'Quick Meeting'),
                    "expiration_minutes": params.get('expiration_minutes', 60)
                },
                priority=TaskPriority.HIGH
            )
        ]
    
    def _decompose_send_message(self, params: Dict[str, Any]) -> List[Task]:
        """Decompose message sending into tasks"""
        return [
            Task(
                task_id=self._create_task_id(),
                service="chat",
                action="send_message",
                parameters={
                    "space_id": params.get('space_id'),
                    "text": params.get('message', params.get('quoted_text', [''])[0])
                },
                priority=TaskPriority.HIGH
            )
        ]
    
    def _decompose_youtube_operation(self, intent_type: str, params: Dict[str, Any]) -> List[Task]:
        """Decompose YouTube operations into tasks"""
        tasks = []
        
        if intent_type == 'search_videos':
            tasks.append(Task(
                task_id=self._create_task_id(),
                service="youtube",
                action="search_videos",
                parameters={
                    "query": params.get('query', params.get('text', '')),
                    "max_results": params.get('max_results', 10)
                },
                priority=TaskPriority.LOW
            ))
        
        return tasks
    
    def _decompose_create_note(self, params: Dict[str, Any]) -> List[Task]:
        """Decompose note creation into tasks"""
        return [
            Task(
                task_id=self._create_task_id(),
                service="keep",
                action="create_note",
                parameters={
                    "title": params.get('title', 'Quick Note'),
                    "text": params.get('text', params.get('quoted_text', [''])[0]),
                    "labels": params.get('labels', [])
                },
                priority=TaskPriority.LOW
            )
        ]
    
    def _decompose_create_form(self, params: Dict[str, Any]) -> List[Task]:
        """Decompose form creation into tasks"""
        tasks = []
        
        tasks.append(Task(
            task_id=self._create_task_id(),
            service="forms",
            action="create_form",
            parameters={
                "title": params.get('title', 'Untitled Form'),
                "description": params.get('description', '')
            },
            priority=TaskPriority.MEDIUM
        ))
        
        return tasks
    
    def _decompose_contact_operation(self, intent_type: str, params: Dict[str, Any]) -> List[Task]:
        """Decompose contact operations into tasks"""
        tasks = []
        
        if intent_type == 'create_contact':
            tasks.append(Task(
                task_id=self._create_task_id(),
                service="contacts",
                action="create_contact",
                parameters={
                    "name": params.get('name'),
                    "email": params.get('email'),
                    "phone": params.get('phone')
                },
                priority=TaskPriority.MEDIUM
            ))
        
        elif intent_type == 'search_contacts':
            tasks.append(Task(
                task_id=self._create_task_id(),
                service="contacts",
                action="search_contacts",
                parameters={"query": params.get('query', params.get('text', ''))},
                priority=TaskPriority.LOW
            ))
        
        return tasks
    
    def _decompose_list_albums(self, params: Dict[str, Any]) -> List[Task]:
        """Decompose list albums into tasks"""
        return [
            Task(
                task_id=self._create_task_id(),
                service="photos",
                action="list_albums",
                parameters={},
                priority=TaskPriority.LOW
            )
        ]
    
    def _decompose_list_photos(self, params: Dict[str, Any]) -> List[Task]:
        """Decompose list photos into tasks"""
        return [
            Task(
                task_id=self._create_task_id(),
                service="photos",
                action="list_photos",
                parameters={"album_id": params.get('album_id')},
                priority=TaskPriority.LOW
            )
        ]


# Singleton instance
decomposer = TaskDecomposer()


def decompose_tasks(intent_data: Dict[str, Any]) -> List[Dict]:
    """Decompose intent data into tasks"""
    tasks = decomposer.decompose(intent_data)
    return [task.__dict__ for task in tasks]
