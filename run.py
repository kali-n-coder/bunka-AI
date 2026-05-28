import subprocess
import os
import sys
import time
import signal

def run_command(command, cwd=None, shell=True):
    return subprocess.Popen(command, cwd=cwd, shell=shell)

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")

    print("--- Hakuryu Anti-Gravity System Starter ---")

    # 1. 依存関係のチェック (簡略化)
    if not os.path.exists(os.path.join(backend_dir, "venv")):
        print("Backend venv not found. Please create it first.")
        # sys.exit(1) # 今回はすでに作成済みなのでスキップ
    
    # 2. バックエンドの起動
    print("Starting Backend...")
    backend_cmd = f"\"{os.path.join(backend_dir, 'venv', 'Scripts', 'python')}\" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    backend_proc = run_command(backend_cmd, cwd=backend_dir)

    # 3. フロントエンドの起動
    print("Starting Frontend...")
    # npm install が必要かもしれないが、初回の想定
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("Frontend node_modules not found. Running npm install...")
        subprocess.run("npm install", cwd=frontend_dir, shell=True)

    frontend_proc = run_command("npm run dev", cwd=frontend_dir)

    print("\nSystem is running!")
    print(f"Backend: http://localhost:8000")
    print(f"Frontend: http://localhost:5173")
    print("Press Ctrl+C to stop both servers.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
