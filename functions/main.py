"""
Netlify Function handler for Google Workspace AI Assistant
Simplified version for Netlify deployment
"""
import os
import sys
from pathlib import Path

# Get the function directory
FUNCTION_DIR = Path(__file__).parent
PROJECT_ROOT = FUNCTION_DIR.parent

# Add project root to path
sys.path.insert(0, str(PROJECT_ROOT))

# Read the template
TEMPLATE_FILE = FUNCTION_DIR / "templates" / "index.html"

def get_template_content():
    """Read and return the HTML template content"""
    if TEMPLATE_FILE.exists():
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return None

# Import after path is set
try:
    from mangum import Mangum
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from datetime import datetime
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create FastAPI app
    app = FastAPI(
        title="Google Workspace AI Assistant",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    static_dir = PROJECT_ROOT / "public" / "static"
    if static_dir.exists():
        from fastapi.staticfiles import StaticFiles
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    @app.get("/")
    @app.get("/index")
    async def root(request: Request):
        """Serve the main application page"""
        template_content = get_template_content()
        
        if template_content:
            # Process template - replace basic variables
            from string import Template
            try:
                # Try to use Jinja2 if available
                from jinja2 import Template as JinjaTemplate
                template = JinjaTemplate(template_content)
                html = template.render(
                    request=request,
                    title="Google Workspace AI Assistant",
                    year=datetime.now().year
                )
            except Exception:
                # Fallback to basic string replacement
                html = template_content
                html = html.replace('{{ title }}', 'Google Workspace AI Assistant')
                html = html.replace('{{ year }}', str(datetime.now().year))
            
            return HTMLResponse(content=html)
        else:
            return HTMLResponse(
                content="<html><body><h1>Template not found</h1></body></html>",
                status_code=500
            )
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {"status": "healthy", "service": "Google Workspace AI Assistant"}
    
    @app.post("/api/analyze")
    async def analyze(request: Request):
        """Analyze prompt endpoint"""
        try:
            body = await request.json()
            prompt = body.get("prompt", "")
            
            # Import the core functionality
            try:
                from core.prompt_analyzer import analyze_prompt as core_analyze
                result = core_analyze(prompt)
                return JSONResponse(content=result)
            except ImportError as e:
                logger.warning(f"Could not import core modules: {e}")
                return JSONResponse(
                    content={"error": "Core modules not available", "details": str(e)},
                    status_code=503
                )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            return JSONResponse(
                content={"error": str(e)},
                status_code=500
            )
    
    @app.post("/api/execute")
    async def execute(request: Request):
        """Execute task endpoint"""
        try:
            body = await request.json()
            prompt = body.get("prompt", "")
            
            # Import the core functionality
            try:
                from core.prompt_analyzer import analyze_prompt
                from core.task_decomposer import decompose_tasks
                from core.orchestrator import Orchestrator
                
                # Analyze the prompt
                analysis = analyze_prompt(prompt)
                
                # Decompose into tasks
                tasks = decompose_tasks(analysis)
                
                # Execute tasks
                orchestrator = Orchestrator()
                results = orchestrator.execute_tasks(tasks)
                
                return JSONResponse(content={
                    "analysis": analysis,
                    "tasks": tasks,
                    "results": results
                })
            except ImportError as e:
                logger.warning(f"Could not import core modules: {e}")
                return JSONResponse(
                    content={"error": "Core modules not available", "details": str(e)},
                    status_code=503
                )
        except Exception as e:
            logger.error(f"Error in execute: {e}")
            return JSONResponse(
                content={"error": str(e)},
                status_code=500
            )
    
    # Create the handler for Netlify
    handler = Mangum(app, debug=False)
    
except Exception as e:
    # If there's an error, create a simple error handler
    logger.error(f"Error initializing app: {e}")
    
    def handler(event, context):
        from mangum import Mangum
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        app = FastAPI()
        
        @app.get("/")
        async def root():
            return JSONResponse(
                content={"error": "Application initialization failed", "details": str(e)},
                status_code=500
            )
        
        handler = Mangum(app)
        return handler(event, context)

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
