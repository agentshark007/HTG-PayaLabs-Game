import subprocess
import sys

def run_pyinstaller():
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "main.py"], check=True)
        print("PyInstaller completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with error code {e.returncode}.")

if __name__ == "__main__":
    run_pyinstaller()
