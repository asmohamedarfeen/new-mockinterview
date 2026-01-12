# How to Start the Backend Server

## The Problem
If you see `ModuleNotFoundError: No module named 'app'`, it means uvicorn can't find the app module.

## The Solution
**Always run uvicorn from the `backend` directory and use the virtual environment.**

## Method 1: Using the Script (Easiest)
```bash
cd backend
./start_server.sh
```

## Method 2: Manual Start (Step by Step)
```bash
# 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run uvicorn (IMPORTANT: Use 'python -m uvicorn', not just 'uvicorn')
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Why This Works
- Running from `backend/` directory ensures Python can find the `app` module
- Using `python -m uvicorn` ensures we use the venv's Python
- The `--reload` flag enables auto-reload on code changes

## Common Mistakes
❌ Running from project root: `uvicorn app.main:app` (won't find app module)
❌ Not activating venv: Uses system Python instead of venv Python
❌ Wrong directory: Python can't find the `app` package

✅ Always: `cd backend && source venv/bin/activate && python -m uvicorn app.main:app`
