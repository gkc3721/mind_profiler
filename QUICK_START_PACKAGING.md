# Quick Start - Package for Boss

## 🎯 Goal

Package the app so your boss can double-click an icon and use it without touching Terminal.

---

## 📋 Steps (5 minutes)

### 1. Build the Frontend

```bash
cd frontend
npm run build
```

**Wait for:** `✓ built in XXXms`

**Result:** Creates `frontend/dist/` with the UI

---

### 2. Test the Launcher

```bash
cd ../backend
source venv/bin/activate
python run_zenin_app.py
```

**Expected:**
- Terminal shows startup messages
- Browser opens automatically after 2 seconds
- UI loads at http://127.0.0.1:8000

**Test:**
- Navigate to "Run Pipeline"
- Select a folder
- Run a pipeline
- Verify results appear

**Stop:** Press `Ctrl+C`

---

### 3. Create macOS .app (Automator)

**3.1 Open Automator:**
- Press `Cmd+Space`
- Type "Automator"
- Press Enter

**3.2 Create Application:**
- Choose "Application"
- Click "Choose"

**3.3 Add Shell Script:**
- Search for "Run Shell Script" in the left panel
- Drag it to the right panel

**3.4 Configure Script:**

**Paste this (update path if needed):**
```bash
#!/bin/bash

# Navigate to project
cd "/Users/umutkaya/Documents/Zenin Mind Reader/zenin_mac2/backend"

# Activate venv
source venv/bin/activate

# Run app
python run_zenin_app.py
```

**3.5 Save:**
- File → Save
- Name: "Zenin EEG"
- Location: Desktop (or Applications)
- Format: Application
- Click Save

---

### 4. Test the .app

**4.1 Close everything:**
- Close any open browsers
- Close any running servers

**4.2 Double-click:**
- Find "Zenin EEG.app" on Desktop
- Double-click it

**Expected:**
- Terminal window appears
- Browser opens automatically
- UI loads

**4.3 Test functionality:**
- Run a pipeline
- View results
- Check that everything works

**4.4 Test auto-shutdown:**
- Don't interact for 10 minutes
- Server should auto-stop
- OR press `Ctrl+C` to stop manually

---

## ✅ Success Checklist

After completing all steps:

- [ ] `frontend/dist/` exists with built files
- [ ] `backend/run_zenin_app.py` exists
- [ ] Running `python run_zenin_app.py` opens browser automatically
- [ ] "Zenin EEG.app" exists on Desktop
- [ ] Double-clicking .app opens browser and loads UI
- [ ] Running a pipeline from .app works
- [ ] Server auto-shuts down after 10 minutes of inactivity

---

## 🎁 Deliver to Boss

**What your boss needs:**

1. **The .app file** - "Zenin EEG.app"
2. **The project folder** - Entire `zenin_mac2` directory
3. **Instructions:**
   ```
   Double-click "Zenin EEG.app" to start.
   Browser will open automatically.
   Server stops automatically after 10 minutes of no use.
   ```

**Usage:**
- Double-click icon
- Browser opens
- Use the application
- Close browser when done
- Server stops automatically

---

## 🔧 Quick Fixes

### Frontend not built?

```bash
cd frontend
npm install  # If first time
npm run build
```

### Port 8000 in use?

```bash
# Find what's using it
lsof -i :8000

# Kill it
kill -9 <PID>
```

### .app path wrong?

1. Right-click "Zenin EEG.app"
2. Choose "Show Package Contents"
3. Open `Contents/document.wflow` in Automator
4. Update the `cd` path
5. Save

### venv not found?

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📝 What Changed

### New Files

1. **`backend/run_zenin_app.py`**
   - Python launcher script
   - Starts server + opens browser

2. **`Zenin EEG.app`**
   - macOS launcher (you create this)
   - Runs the Python script

### Updated Files

1. **`backend/app/main.py`**
   - Now serves built frontend from `frontend/dist/`
   - Added idle shutdown feature
   - Added activity tracking middleware

2. **`frontend/src/api/client.ts`**
   - Dynamic base URL (dev vs production)

3. **`frontend/src/api/runsApi.ts`**
   - Dynamic URLs for plots/logs/summary

---

## 🚀 How It Works

```
User double-clicks .app
  ↓
Automator runs shell script
  ↓
Shell script:
  - cd to backend
  - activate venv
  - python run_zenin_app.py
  ↓
Python script:
  - starts FastAPI server
  - opens browser after 2s
  ↓
FastAPI:
  - serves frontend from dist/
  - handles API requests
  - tracks activity
  ↓
Browser shows UI
  ↓
User works
  ↓
10 minutes of no activity
  ↓
Server auto-shuts down
```

---

## 🎉 Done!

Your boss can now:
1. Double-click "Zenin EEG.app"
2. Use the application
3. Not worry about Terminal, ports, servers, etc.

That's it! 🌊
