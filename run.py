import os
import subprocess
import sys

def run():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Check if requirements are installed
    try:
        import fastapi
    except ImportError:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    print("Starting Python Backend on http://localhost:3001...")
    subprocess.check_call([sys.executable, "main.py"])

if __name__ == "__main__":
    run()
