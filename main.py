"""
Google Workspace AI Assistant
Unified interface to all Google apps controlled by AI prompts

Features:
- Natural language prompt processing
- Multi-user support with sessions
- Works without Google credentials (demo mode)
- Full Google OAuth integration when configured
"""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uvicorn
import logging

try:
    from core.prompt_analyzer import analyze_prompt
    from core.task_decomposer import decompose_tasks
    from core.orchestrator import Orchestrator
    from auth.google_auth import auth_handler
    from auth.session_manager import session_manager, create_user_session
    from config import load_config
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Load configuration
try:
    config = load_config()
except Exception as e:
    print(f"Configuration error: {e}")
    config = {
        'app': {
            'host': 'localhost',
            'port': 8000,
            'debug': True,
            'title': 'Google Workspace AI Assistant',
            'version': '1.0.0'
        },
        'google': {
            'client_id': None,
            'client_secret': None
        }
    }

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get('logging', {}).get('level', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=config['app']['title'],
    version=config['app']['version']
)

# Check if Google OAuth is configured
GOOGLE_CONFIGURED = bool(config.get('google', {}).get('client_id'))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
static_dir = os.path.join(os.path.dirname(__file__), 'static')
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Session cookie name
SESSION_COOKIE = "session_id"


# Request/Response Models
class PromptRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None


# Demo mode responses for testing without Google credentials
DEMO_RESPONSES = {
    'gmail.send_email': {
        "success": True,
        "message": "Demo mode: Email would be sent",
        "note": "Connect Google account to send real emails"
    },
    'gmail.read_emails': {
        "success": True,
        "message": "Demo mode: Would show emails",
        "emails": [],
        "note": "Connect Google account to read real emails"
    },
    'calendar.create_event': {
        "success": True,
        "message": "Demo mode: Event would be created",
        "note": "Connect Google account to create real calendar events"
    },
    'calendar.get_events': {
        "success": True,
        "message": "Demo mode: Would show calendar events",
        "events": [],
        "note": "Connect Google account to view real calendar"
    },
    'drive.list_files': {
        "success": True,
        "message": "Demo mode: Would show files",
        "files": [],
        "note": "Connect Google account to access real Drive files"
    },
    'drive.search_files': {
        "success": True,
        "message": "Demo mode: Would search files",
        "files": [],
        "note": "Connect Google account to search real Drive files"
    },
    'docs.create_document': {
        "success": True,
        "message": "Demo mode: Document would be created",
        "note": "Connect Google account to create real Google Docs"
    },
    'docs.read_document': {
        "success": True,
        "message": "Demo mode: Would read document",
        "note": "Connect Google account to read real documents"
    },
    'sheets.create_spreadsheet': {
        "success": True,
        "message": "Demo mode: Spreadsheet would be created",
        "note": "Connect Google account to create real spreadsheets"
    },
    'translate.translate': {
        "success": True,
        "translated_text": "Demo: Translation would appear here",
        "note": "Connect Google account for real translations"
    },
    'meet.create_meeting_space': {
        "success": True,
        "message": "Demo mode: Meeting space would be created",
        "meeting_uri": "https://meet.google.com/demo-meeting",
        "note": "Connect Google account to create real Google Meet links"
    },
    'youtube.search_videos': {
        "success": True,
        "message": "Demo mode: Would search YouTube videos",
        "videos": [],
        "note": "Connect Google account for real YouTube search"
    },
    'keep.create_note': {
        "success": True,
        "message": "Demo mode: Note would be created",
        "note": "Connect Google account to create real Keep notes"
    },
    'forms.create_form': {
        "success": True,
        "message": "Demo mode: Form would be created",
        "note": "Connect Google account to create real forms"
    },
    'contacts.create_contact': {
        "success": True,
        "message": "Demo mode: Contact would be created",
        "note": "Connect Google account to add real contacts"
    },
    'photos.list_albums': {
        "success": True,
        "message": "Demo mode: Would show photo albums",
        "albums": [],
        "note": "Connect Google account to view real photos"
    },
}


def execute_demo_task(service: str, action: str, parameters: Dict) -> Dict[str, Any]:
    """Execute a demo task without Google credentials"""
    key = f"{service}.{action}"
    
    if key in DEMO_RESPONSES:
        response = DEMO_RESPONSES[key].copy()
        response['parameters'] = parameters
        return response
    
    return {
        "success": True,
        "message": f"Demo mode: {service}.{action} would execute",
        "service": service,
        "action": action,
        "parameters": parameters,
        "note": "Connect Google account for full functionality"
    }


# API Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session_id: Optional[str] = Cookie(None)):
    """Serve the web interface"""
    is_authenticated = False
    user_id = None
    
    if session_id:
        is_authenticated = session_manager.validate_session(session_id)
        user_id = session_manager.get_user_id(session_id)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "is_authenticated": is_authenticated,
        "user_id": user_id,
        "google_configured": GOOGLE_CONFIGURED
    })


@app.get("/login")
async def login(request: Request):
    """Create a new session and redirect to Google auth"""
    if not GOOGLE_CONFIGURED:
        # Demo mode - no Google credentials
        session_id = create_user_session()
        response = RedirectResponse(url="/?demo=true", status_code=302)
        response.set_cookie(
            key=SESSION_COOKIE,
            value=session_id,
            httponly=True,
            max_age=86400,
            samesite="lax"
        )
        return response
    
    # Real Google OAuth
    session_id = create_user_session()
    auth_url = auth_handler.get_auth_url(session_id)
    
    response = RedirectResponse(url=auth_url, status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    return response


@app.get("/demo-login")
async def demo_login():
    """Create a demo session without Google"""
    session_id = create_user_session()
    response = RedirectResponse(url="/?demo=true&auth=demo", status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    return response


@app.get("/auth/callback")
async def handle_callback(
    request: Request,
    code: str = None,
    error: str = None,
    session_id: Optional[str] = Cookie(None)
):
    """Handle OAuth2 callback from Google"""
    if error:
        logger.error(f"OAuth error: {error}")
        return RedirectResponse(url="/?auth=error&message=" + error, status_code=302)
    
    if not code:
        return RedirectResponse(url="/?auth=error&message=no_code", status_code=302)
        
    # The 'state' parameter should contain the session_id used to initiate the auth flow
    # This is crucial for matching the callback to the correct session/flow
    state_session_id = request.query_params.get('state')
    
    if not state_session_id:
        logger.error("OAuth callback error: 'state' parameter missing from request.")
        return RedirectResponse(url="/?auth=error&message=missing_state", status_code=302)

    # Validate that the state from the callback matches the session cookie to prevent CSRF.
    if not session_id or state_session_id != session_id:
        logger.error(f"OAuth state mismatch. State: {state_session_id}, Cookie: {session_id}. Possible CSRF attack.")
        return RedirectResponse(url="/?auth=error&message=state_mismatch", status_code=302)

    user_id_for_auth = state_session_id
    
    try: # Pass the session_id from state to handle_callback
        credentials = auth_handler.handle_callback(user_id_for_auth, code)
        
        if credentials:
            # Mark session as authenticated
            session_manager.authenticate_session(user_id_for_auth)
            response = RedirectResponse(url="/?auth=success", status_code=302)
            response.set_cookie(
                key=SESSION_COOKIE,
                value=user_id_for_auth, # Set cookie with the session_id that was authenticated
                httponly=True,
                max_age=86400,
                samesite="lax"
            )
            return response
        else:
            return RedirectResponse(url="/?auth=error&message=auth_failed", status_code=302)
            
    except Exception as e:
        logger.error(f"Auth callback error: {e}")
        return RedirectResponse(url="/?auth=error&message=" + str(e), status_code=302)

@app.get("/logout")
async def logout(session_id: Optional[str] = Cookie(None)):
    """End user session"""
    if session_id:
        session_manager.end_session(session_id)
    
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return response


@app.get("/api/status")
async def api_status(session_id: Optional[str] = Cookie(None)):
    """API status check"""
    is_authenticated = False
    user_id = None
    
    if session_id:
        is_authenticated = session_manager.validate_session(session_id)
        user_id = session_manager.get_user_id(session_id)
    
    return {
        "status": "running",
        "version": config['app']['version'],
        "title": config['app']['title'],
        "authenticated": is_authenticated,
        "google_configured": GOOGLE_CONFIGURED,
        "mode": "demo" if not (GOOGLE_CONFIGURED and is_authenticated) else "full",
        "user_id": user_id
    }


@app.get("/api/auth/url")
async def get_auth_url(request: Request, session_id: Optional[str] = Cookie(None)):
    """Get Google OAuth2 authorization URL"""
    if not GOOGLE_CONFIGURED:
        # Return demo URL
        return {
            "success": True,
            "demo_mode": True,
            "auth_url": "/demo-login",
            "message": "Demo mode - click to continue without Google"
        }
    
    if not session_id or not session_manager.get_session(session_id):
        session_id = create_user_session()
    
    try:
        redirect_uri = str(request.url_for('handle_callback'))
        auth_url = auth_handler.get_auth_url(session_id, redirect_uri=redirect_uri)
        return {
            "success": True,
            "auth_url": auth_url,
            "session_id": session_id
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/auth/status")
async def check_auth_status(session_id: Optional[str] = Cookie(None)):
    """Check if user is authenticated"""
    if not session_id:
        return {"authenticated": False, "google_configured": GOOGLE_CONFIGURED}
    
    is_authenticated = session_manager.validate_session(session_id)
    user_id = session_manager.get_user_id(session_id) if is_authenticated else None
    
    return {
        "authenticated": is_authenticated,
        "google_configured": GOOGLE_CONFIGURED,
        "user_id": user_id,
        "mode": "demo" if not (GOOGLE_CONFIGURED and is_authenticated) else "full"
    }


@app.post("/api/prompt")
async def handle_prompt(data: PromptRequest, session_id: Optional[str] = Cookie(None)):
    """
    Main endpoint for processing AI prompts
    Works in both demo mode and full Google integration mode
    """
    current_session = data.session_id or session_id
    
    try:
        # Step 1: Analyze the prompt (always works - AI powered)
        intent = analyze_prompt(data.prompt)
        
        if not intent.get('success'):
            return JSONResponse(
                status_code=400,
                content={"error": "Failed to analyze prompt"}
            )
        
        # Step 2: Decompose into tasks
        tasks = decompose_tasks(intent)
        
        # Step 3: Execute tasks
        user_id = session_manager.get_user_id(current_session) if current_session else "default"
        
        # Check if we have real credentials
        is_authenticated = session_manager.validate_session(current_session) if current_session else False
        
        if GOOGLE_CONFIGURED and is_authenticated:
            # Real execution with Google APIs
            orchestrator = Orchestrator(user_id)
            execution_results = orchestrator.run_tasks(tasks)
            results_list = execution_results.get('results', [])
        else:
            # Demo mode - simulate response for each task
            results_list = []
            for task_dict in tasks:
                service = task_dict.get('service', 'unknown')
                action = task_dict.get('action', 'unknown')
                params = task_dict.get('parameters', {})
                result = execute_demo_task(service, action, params)
                results_list.append({"task_id": task_dict.get('task_id'), "service": service, "action": action, "result": result})
        
        return {
            "success": True,
            "mode": "demo" if not (GOOGLE_CONFIGURED and is_authenticated) else "full",
            "prompt": data.prompt,
            "intent": intent.get('detected_intent'),
            "entities": intent.get('entities', []),
            "tasks": tasks,
            "execution_summary": { # Renamed to avoid confusion with 'results' list
                "executed": len(results_list),
                "total": len(tasks),
                "results": results_list
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/services")
async def list_services(session_id: Optional[str] = Cookie(None)):
    """List all available services"""
    is_authenticated = False
    user_id = None
    
    if session_id:
        is_authenticated = session_manager.validate_session(session_id)
        user_id = session_manager.get_user_id(session_id)
    
    services = [
        {"name": "gmail", "description": "Email management", "icon": "📧", "status": "ready"},
        {"name": "drive", "description": "File storage", "icon": "📁", "status": "ready"},
        {"name": "calendar", "description": "Event scheduling", "icon": "📅", "status": "ready"},
        {"name": "docs", "description": "Document editing", "icon": "📄", "status": "ready"},
        {"name": "sheets", "description": "Spreadsheet management", "icon": "📊", "status": "ready"},
        {"name": "slides", "description": "Presentation creation", "icon": "🎨", "status": "ready"},
        {"name": "meet", "description": "Video conferencing", "icon": "🎥", "status": "ready"},
        {"name": "chat", "description": "Team messaging", "icon": "💬", "status": "ready"},
        {"name": "translate", "description": "Language translation", "icon": "🌐", "status": "ready"},
        {"name": "maps", "description": "Location services", "icon": "🗺️", "status": "ready"},
        {"name": "youtube", "description": "Video search", "icon": "📺", "status": "ready"},
        {"name": "keep", "description": "Note taking", "icon": "📝", "status": "ready"},
        {"name": "forms", "description": "Form creation", "icon": "📋", "status": "ready"},
        {"name": "contacts", "description": "Contact management", "icon": "👥", "status": "ready"},
        {"name": "photos", "description": "Photo management", "icon": "📸", "status": "ready"}
    ]
    return {
        "services": services,
        "total": len(services),
        "google_configured": GOOGLE_CONFIGURED,
        "authenticated": is_authenticated,
        "user_id": user_id,
        "mode": "demo" if not (GOOGLE_CONFIGURED and is_authenticated) else "full"
    }


@app.get("/api/help")
async def get_help():
    """Get help information"""
    return {
        "title": "Google Workspace AI Assistant",
        "description": "Control all your Google apps with natural language",
        "mode": "demo" if not GOOGLE_CONFIGURED else "full",
        "setup_required": not GOOGLE_CONFIGURED,
        "setup_instructions": {
            "step_1": "Go to Google Cloud Console",
            "step_2": "Create a new project",
            "step_3": "Enable required APIs",
            "step_4": "Create OAuth 2.0 credentials",
            "step_5": "Add credentials to config.local.yaml"
        } if not GOOGLE_CONFIGURED else None,
        "examples": [
            "Send an email to john@example.com about the meeting",
            "Schedule a meeting tomorrow at 3pm with team",
            "Create a new document called Project Notes",
            "Find my files about the budget",
            "Translate 'Hello, how are you?' to Spanish",
            "List all my calendar events for today"
        ]
    }


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config['app']['host'],
        port=config['app']['port'],
        reload=config['app'].get('debug', False)
    )
