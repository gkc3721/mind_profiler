from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routes import config, profiles, run
from app.core.profiles_manager import initialize_default_profiles
import time
import asyncio
import signal
import sys
from pathlib import Path

app = FastAPI(
    title="Zenin EEG Pipeline API",
    description="API for running EEG analysis pipeline with configurable constants and profile sets",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Idle shutdown configuration
IDLE_TIMEOUT_SECONDS = 600  # 10 minutes
last_request_time = time.time()
shutdown_task = None

# Middleware to track activity
@app.middleware("http")
async def track_activity(request: Request, call_next):
    global last_request_time
    
    # Update last request time for all requests except static files
    if not request.url.path.startswith("/assets"):
        last_request_time = time.time()
    
    response = await call_next(request)
    return response

# Background task to check for idle timeout
async def idle_shutdown_checker():
    """Check for idle timeout and shutdown if inactive for too long"""
    global last_request_time
    
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        
        idle_time = time.time() - last_request_time
        
        if idle_time > IDLE_TIMEOUT_SECONDS:
            print(f"\n⏰ Server idle for {int(idle_time/60)} minutes. Shutting down...")
            print("🛑 Auto-shutdown activated. Goodbye!\n")
            # Gracefully shutdown
            import os
            os.kill(os.getpid(), signal.SIGTERM)
            break

# Include routers
app.include_router(config.router, prefix="/config", tags=["config"])
app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
app.include_router(run.router, prefix="", tags=["run"])

# Mount static files for the built frontend
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the frontend SPA - return index.html for all non-API routes"""
        # If requesting a specific file that exists, serve it
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # Otherwise, serve index.html (for SPA routing)
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        return {"error": "Frontend not built. Run 'cd frontend && npm run build'"}


@app.on_event("startup")
async def startup_event():
    """Initialize default profile set on startup and start idle checker"""
    global shutdown_task
    
    try:
        initialize_default_profiles()
        print("✅ Startup: Default profiles initialized")
    except Exception as e:
        print(f"⚠️ Startup warning: {e}")
    
    # Check if frontend is built
    if not frontend_dist.exists():
        print("⚠️ Warning: Frontend not built. Run 'cd frontend && npm run build' to build the UI.")
    else:
        print("✅ Frontend found and will be served at http://127.0.0.1:8000")
    
    # Start idle shutdown checker
    shutdown_task = asyncio.create_task(idle_shutdown_checker())
    print(f"⏰ Idle shutdown: Server will stop after {IDLE_TIMEOUT_SECONDS//60} minutes of inactivity")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global shutdown_task
    if shutdown_task:
        shutdown_task.cancel()
    print("👋 Server shutdown complete")
