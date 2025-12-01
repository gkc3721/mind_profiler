# Zenin EEG Application - Packaging Guide

## Overview

The Zenin EEG application is now packaged for easy double-click usage by non-technical users. No terminal commands needed!

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────┐
│ User double-clicks app icon             │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│ Automator .app launcher                 │
│ (runs: python run_zenin_app.py)        │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│ Python launcher starts FastAPI          │
│ - Activates venv                        │
│ - Starts server on 127.0.0.1:8000      │
│ - Opens browser automatically            │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│ FastAPI serves built frontend           │
│ - Serves /assets (JS, CSS)              │
│ - Serves index.html for all routes      │
│ - Handles API requests                   │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│ Browser opens at http://127.0.0.1:8000  │
│ User interacts with UI                   │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│ Auto-shutdown after 10min idle          │
│ OR user closes browser/presses Ctrl+C   │
└─────────────────────────────────────────┘
```

---

## Setup Steps

### Step 1: Build the Frontend

```bash
cd frontend
npm run build
```

This creates `frontend/dist/` with:
- `index.html` (entry point)
- `assets/` (JS, CSS, images)

### Step 2: Test the Launcher

```bash
cd backend
source venv/bin/activate  # Or: venv\Scripts\activate on Windows
python run_zenin_app.py
```

**Expected output:**
```
============================================================
🧠 Zenin EEG Pipeline - Starting...
============================================================

📍 Server will be available at: http://127.0.0.1:8000
🌐 Browser will open automatically in 2 seconds...

⏰ Auto-shutdown: Server will stop after 10 minutes of inactivity
🛑 To stop the server manually: Press Ctrl+C

✅ Startup: Default profiles initialized
✅ Frontend found and will be served at http://127.0.0.1:8000
⏰ Idle shutdown: Server will stop after 10 minutes of inactivity
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

🌊 Opening Zenin EEG in your browser...
```

Browser should open automatically showing the Zenin EEG UI.

### Step 3: Create macOS .app Launcher (Automator)

1. **Open Automator** (search in Spotlight)

2. **Choose:** "Application"

3. **Add action:** "Run Shell Script"

4. **Configure:**
   - Shell: `/bin/bash`
   - Pass input: `as arguments`

5. **Script content:**
   ```bash
   #!/bin/bash
   
   # Navigate to project directory
   cd "/Users/umutkaya/Documents/Zenin Mind Reader/zenin_mac2/backend"
   
   # Activate virtual environment
   source venv/bin/activate
   
   # Run the launcher
   python run_zenin_app.py
   ```

6. **Save as:** "Zenin EEG.app" (on Desktop or Applications folder)

7. **Optional - Add custom icon:**
   - Right-click .app → Get Info
   - Drag an icon image to the top-left icon area

### Step 4: Test the .app

1. Double-click "Zenin EEG.app"
2. Browser should open automatically
3. UI should load
4. Run a pipeline to test functionality

---

## Features

### 1. Auto-start Server

**File:** `backend/run_zenin_app.py`

- Starts FastAPI server using uvicorn
- No need for manual `uvicorn` command

### 2. Auto-open Browser

**Implementation:**
```python
def open_browser():
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000")

threading.Thread(target=open_browser, daemon=True).start()
```

- Opens default browser after 2-second delay
- Uses Python's `webbrowser` module
- Works on macOS, Windows, Linux

### 3. Frontend Served by FastAPI

**File:** `backend/app/main.py`

**Changes:**
- Mount `frontend/dist/assets` as static files
- Serve `index.html` for all non-API routes (SPA routing)
- Detect if frontend is built, show warning if not

**Routes:**
- `/` → `index.html`
- `/run-pipeline` → `index.html` (React Router handles routing)
- `/assets/*` → Static files (JS, CSS, images)
- `/config/*` → API endpoints
- `/profiles/*` → API endpoints
- `/runs/*` → API endpoints

### 4. Auto-shutdown After Idle

**Implementation:**

**Middleware tracks activity:**
```python
@app.middleware("http")
async def track_activity(request: Request, call_next):
    global last_request_time
    if not request.url.path.startswith("/assets"):
        last_request_time = time.time()
    response = await call_next(request)
    return response
```

**Background task checks for timeout:**
```python
async def idle_shutdown_checker():
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        idle_time = time.time() - last_request_time
        
        if idle_time > 600:  # 10 minutes
            print("⏰ Server idle for 10 minutes. Shutting down...")
            os.kill(os.getpid(), signal.SIGTERM)
            break
```

**Behavior:**
- Tracks time since last request
- Ignores static file requests (JS/CSS)
- Checks every 30 seconds
- Shuts down after 10 minutes of no activity
- Graceful shutdown using `SIGTERM`

### 5. Production vs Development URLs

**File:** `frontend/src/api/client.ts`

```typescript
const baseURL = import.meta.env.DEV 
  ? 'http://localhost:8000'  // Development (Vite dev server)
  : window.location.origin;   // Production (served from same origin)
```

**Behavior:**
- **Development:** API calls go to `http://localhost:8000`
- **Production:** API calls are relative (e.g., `/runs/123/summary`)

---

## Testing

### Test 1: Frontend Build

```bash
cd frontend
npm run build
```

**Check:**
- `frontend/dist/index.html` exists
- `frontend/dist/assets/` contains JS/CSS files

### Test 2: Launcher Script

```bash
cd backend
source venv/bin/activate
python run_zenin_app.py
```

**Expected:**
1. Server starts
2. Browser opens automatically
3. UI loads without errors

### Test 3: Frontend Integration

1. Open http://127.0.0.1:8000
2. Check DevTools console (no errors)
3. Navigate between pages (Run Pipeline, Profile Sets, History, Config)
4. Run a pipeline
5. View results, summary, plots

### Test 4: Idle Shutdown

1. Start server
2. Don't interact for 10 minutes
3. Server should auto-shutdown with message:
   ```
   ⏰ Server idle for 10 minutes. Shutting down...
   🛑 Auto-shutdown activated. Goodbye!
   ```

### Test 5: .app Launcher

1. Double-click "Zenin EEG.app"
2. Same behavior as manual launch
3. Browser opens automatically

---

## User Experience

### Starting the App

1. **User:** Double-clicks "Zenin EEG.app" icon
2. **System:** Terminal window opens (optional: can be hidden)
3. **System:** Browser opens with Zenin EEG UI
4. **User:** Interacts with UI normally

### Using the App

- All features work as before
- No need to know about ports, URLs, or terminal
- Just use the UI

### Stopping the App

**Option 1: Auto-shutdown**
- Close browser
- Wait 10 minutes (or less if configured)
- Server stops automatically

**Option 2: Manual stop**
- Press `Ctrl+C` in terminal window
- Server stops immediately

**Option 3: Close terminal**
- Click red X on terminal window
- Server stops

---

## Configuration

### Change Idle Timeout

**File:** `backend/app/main.py`

```python
IDLE_TIMEOUT_SECONDS = 600  # 10 minutes
```

**Change to:**
- `300` = 5 minutes
- `900` = 15 minutes
- `1800` = 30 minutes

### Change Server Port

**File:** `backend/run_zenin_app.py`

```python
uvicorn.run(
    "app.main:app",
    host="127.0.0.1",
    port=8000  # Change this
)
```

**Also update browser URL:**
```python
webbrowser.open("http://127.0.0.1:8000")  # Update port here too
```

### Disable Auto-shutdown

**File:** `backend/app/main.py`

Comment out the idle checker:
```python
# shutdown_task = asyncio.create_task(idle_shutdown_checker())
```

---

## Troubleshooting

### Issue: Browser doesn't open automatically

**Cause:** Browser path not found or blocked

**Solution:**
- Server is still running at http://127.0.0.1:8000
- Open browser manually and visit that URL

### Issue: "Frontend not built" warning

**Cause:** `frontend/dist/` doesn't exist

**Solution:**
```bash
cd frontend
npm run build
```

### Issue: .app doesn't work

**Cause:** Path to project is incorrect

**Solution:**
- Edit the .app in Automator
- Update path to match your actual project location
- Save and try again

### Issue: Python/venv not found

**Cause:** Virtual environment not set up

**Solution:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Port 8000 already in use

**Cause:** Another process using port 8000

**Solution:**
```bash
# Find process
lsof -i :8000

# Kill it
kill -9 <PID>

# Or change port (see Configuration section)
```

---

## File Structure

```
zenin_mac2/
├── backend/
│   ├── run_zenin_app.py          ← NEW: Launcher script
│   ├── app/
│   │   ├── main.py                ← UPDATED: Serves frontend, idle shutdown
│   │   ├── routes/
│   │   ├── core/
│   │   └── data/
│   ├── venv/
│   └── requirements.txt
├── frontend/
│   ├── dist/                      ← Built frontend (created by npm run build)
│   │   ├── index.html
│   │   └── assets/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts          ← UPDATED: Dynamic URLs
│   │   │   └── runsApi.ts         ← UPDATED: Dynamic URLs
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
└── Zenin EEG.app                  ← Automator launcher (create this)
```

---

## Summary

✅ **One-click launch** - Double-click .app icon  
✅ **Auto-open browser** - No manual URL entry  
✅ **Built-in frontend** - No separate dev server  
✅ **Auto-shutdown** - Saves resources when idle  
✅ **No terminal knowledge needed** - Non-technical friendly  

**User flow:**
1. Double-click "Zenin EEG.app"
2. Browser opens automatically
3. Use the application
4. Close browser when done
5. Server auto-shuts down after 10 minutes

**That's it!** 🎉
