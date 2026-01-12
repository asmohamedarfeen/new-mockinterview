#!/usr/bin/env python3
"""
Unified startup script for Virtual AI Interview Room.

This script can:
- Start the backend server (FastAPI/uvicorn)
- Start the frontend development server (Vite)
- Build the frontend for production
- Run both servers concurrently

Usage:
    python start.py                    # Start both backend and frontend
    python start.py --backend-only     # Start only backend
    python start.py --frontend-only    # Start only frontend
    python start.py --build           # Build frontend then start both
    python start.py --build-only      # Only build frontend, don't start servers
"""

import os
import sys
import subprocess
import signal
import time
import argparse
from pathlib import Path

# Get the project root directory (where this script is located)
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.RESET):
    """Print a colored message."""
    print(f"{color}{message}{Colors.RESET}")

def check_backend_setup():
    """Check if backend is properly set up."""
    venv_path = BACKEND_DIR / "venv"
    if not venv_path.exists():
        print_colored("❌ Backend virtual environment not found!", Colors.RED)
        print_colored("   Run: cd backend && python -m venv venv", Colors.YELLOW)
        return False
    
    requirements_file = BACKEND_DIR / "requirements.txt"
    if not requirements_file.exists():
        print_colored("❌ Backend requirements.txt not found!", Colors.RED)
        return False
    
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        print_colored("⚠️  Backend .env file not found!", Colors.YELLOW)
        print_colored("   Create backend/.env with your configuration", Colors.YELLOW)
        print_colored("   See backend/.env.example for reference", Colors.YELLOW)
    
    return True

def check_frontend_setup():
    """Check if frontend is properly set up."""
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print_colored("⚠️  Frontend node_modules not found!", Colors.YELLOW)
        print_colored("   Run: cd frontend && npm install", Colors.YELLOW)
        return False
    
    package_json = FRONTEND_DIR / "package.json"
    if not package_json.exists():
        print_colored("❌ Frontend package.json not found!", Colors.RED)
        return False
    
    return True

def start_backend():
    """Start the backend server."""
    print_colored("\n🚀 Starting Backend Server...", Colors.BLUE)
    
    # Change to backend directory
    os.chdir(BACKEND_DIR)
    
    # Activate venv and start uvicorn
    # On Unix/Mac: source venv/bin/activate
    # On Windows: venv\Scripts\activate
    if sys.platform == "win32":
        activate_script = BACKEND_DIR / "venv" / "Scripts" / "activate.bat"
        python_exe = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    else:
        activate_script = BACKEND_DIR / "venv" / "bin" / "activate"
        python_exe = BACKEND_DIR / "venv" / "bin" / "python"
    
    if not python_exe.exists():
        print_colored("❌ Python executable not found in venv!", Colors.RED)
        return None
    
    # Start uvicorn server
    cmd = [
        str(python_exe),
        "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    print_colored(f"   Backend will be available at: http://localhost:8000", Colors.GREEN)
    print_colored(f"   API docs at: http://localhost:8000/docs", Colors.GREEN)
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    return process

def start_frontend():
    """Start the frontend development server."""
    print_colored("\n🚀 Starting Frontend Server...", Colors.BLUE)
    
    # Change to frontend directory
    os.chdir(FRONTEND_DIR)
    
    # Check if npm is available
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_colored("❌ npm not found! Please install Node.js and npm.", Colors.RED)
        return None
    
    # Start Vite dev server
    cmd = ["npm", "run", "dev"]
    
    print_colored(f"   Frontend will be available at: http://localhost:5173", Colors.GREEN)
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    return process

def build_frontend():
    """Build the frontend for production."""
    print_colored("\n🔨 Building Frontend...", Colors.BLUE)
    
    # Change to frontend directory
    original_dir = os.getcwd()
    os.chdir(FRONTEND_DIR)
    
    try:
        # Check if npm is available
        try:
            subprocess.run(["npm", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_colored("❌ npm not found! Please install Node.js and npm.", Colors.RED)
            return False
        
        # Run build command
        cmd = ["npm", "run", "build"]
        
        print_colored("   Running: npm run build", Colors.YELLOW)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_colored("✅ Frontend build completed successfully!", Colors.GREEN)
            # Show build output summary
            if "built in" in result.stdout:
                for line in result.stdout.split('\n'):
                    if "built in" in line or "dist/" in line:
                        print_colored(f"   {line.strip()}", Colors.GREEN)
            return True
        else:
            print_colored("❌ Frontend build failed!", Colors.RED)
            if result.stderr:
                print_colored(f"   Error: {result.stderr[:200]}", Colors.RED)
            return False
    finally:
        os.chdir(original_dir)

def print_output(process, name, color):
    """Print output from a subprocess."""
    try:
        for line in process.stdout:
            line = line.rstrip()
            if line:
                print_colored(f"[{name}] {line}", color)
    except Exception as e:
        print_colored(f"Error reading {name} output: {e}", Colors.RED)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print_colored("\n\n🛑 Shutting down servers...", Colors.YELLOW)
    sys.exit(0)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Start Virtual AI Interview Room servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start.py                 # Start both backend and frontend
  python start.py --backend-only  # Start only backend
  python start.py --frontend-only # Start only frontend
  python start.py --build         # Build frontend then start both
  python start.py --build-only   # Only build frontend
        """
    )
    
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Start only the backend server"
    )
    
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Start only the frontend server"
    )
    
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build frontend before starting servers (recommended for production)"
    )
    
    parser.add_argument(
        "--unified",
        action="store_true",
        help="Build frontend and serve from backend on same port (production mode)"
    )
    
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Only build frontend, don't start servers"
    )
    
    args = parser.parse_args()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print_colored("=" * 60, Colors.BOLD)
    print_colored("  Virtual AI Interview Room - Startup Script", Colors.BOLD)
    print_colored("=" * 60, Colors.RESET)
    
    # Handle build-only mode
    if args.build_only:
        if check_frontend_setup():
            build_frontend()
        sys.exit(0)
    
    # Handle unified mode (build + serve from backend)
    if args.unified:
        print_colored("\n🚀 Unified Mode: Building frontend and serving from backend", Colors.BOLD)
        if not check_frontend_setup():
            sys.exit(1)
        if not build_frontend():
            sys.exit(1)
        # In unified mode, only start backend (frontend is served by it)
        start_backend_flag = True
        start_frontend_flag = False
        print_colored("\n✅ Frontend built! Backend will serve it on port 8000", Colors.GREEN)
        print_colored("   Access the app at: http://localhost:8000", Colors.GREEN)
    else:
        # Build frontend if requested (but still run dev servers)
        if args.build:
            if not check_frontend_setup():
                sys.exit(1)
            if not build_frontend():
                sys.exit(1)
    
    # Check setups (unless unified mode already set them)
    if not args.unified:
        start_backend_flag = not args.frontend_only
        start_frontend_flag = not args.backend_only
    
    if start_backend_flag and not check_backend_setup():
        print_colored("\n❌ Backend setup check failed!", Colors.RED)
        sys.exit(1)
    
    if start_frontend_flag and not check_frontend_setup():
        print_colored("\n❌ Frontend setup check failed!", Colors.RED)
        sys.exit(1)
    
    # Start servers
    processes = []
    
    if start_backend_flag:
        backend_process = start_backend()
        if backend_process:
            processes.append(("Backend", backend_process, Colors.BLUE))
        else:
            print_colored("❌ Failed to start backend!", Colors.RED)
            sys.exit(1)
    
    if start_frontend_flag:
        # Wait a bit for backend to start
        if start_backend_flag:
            time.sleep(2)
        
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(("Frontend", frontend_process, Colors.GREEN))
        else:
            print_colored("❌ Failed to start frontend!", Colors.RED)
            # Kill backend if it was started
            if start_backend_flag and backend_process:
                backend_process.terminate()
            sys.exit(1)
    
    # Print startup summary
    print_colored("\n" + "=" * 60, Colors.BOLD)
    print_colored("  ✅ Servers Starting...", Colors.GREEN)
    print_colored("=" * 60, Colors.RESET)
    
    if start_backend_flag:
        if args.unified:
            print_colored("   Backend + Frontend: http://localhost:8000", Colors.BLUE)
            print_colored("   API Docs: http://localhost:8000/docs", Colors.BLUE)
            print_colored("   Health: http://localhost:8000/api/health", Colors.BLUE)
        else:
            print_colored("   Backend:  http://localhost:8000", Colors.BLUE)
            print_colored("   API Docs: http://localhost:8000/docs", Colors.BLUE)
    
    if start_frontend_flag:
        print_colored("   Frontend: http://localhost:5173", Colors.GREEN)
    
    print_colored("\n   Press Ctrl+C to stop all servers\n", Colors.YELLOW)
    print_colored("=" * 60 + "\n", Colors.RESET)
    
    # Monitor processes and print output
    try:
        import threading
        
        def monitor_process(name, process, color):
            """Monitor a single process."""
            try:
                for line in process.stdout:
                    line = line.rstrip()
                    if line:
                        print_colored(f"[{name}] {line}", color)
            except Exception as e:
                print_colored(f"Error monitoring {name}: {e}", Colors.RED)
        
        # Start monitoring threads
        threads = []
        for name, process, color in processes:
            thread = threading.Thread(
                target=monitor_process,
                args=(name, process, color),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        # Wait for processes
        for name, process, _ in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print_colored("\n\n🛑 Shutting down servers...", Colors.YELLOW)
    
    finally:
        # Terminate all processes
        for name, process, _ in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print_colored(f"Error stopping {name}: {e}", Colors.RED)
        
        print_colored("✅ All servers stopped.", Colors.GREEN)

if __name__ == "__main__":
    main()
