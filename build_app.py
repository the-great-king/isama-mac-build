import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_NAME = "IsamaManagement"
ENTRY_POINT = PROJECT_ROOT / "main.py"
DIST_DIR = PROJECT_ROOT / "dist"


def ensure_pyinstaller():
    """Install PyInstaller if it is not already available."""
    try:
        import PyInstaller  # noqa: F401
        print("PyInstaller is already installed.")
    except ImportError:
        print("PyInstaller not found. Installing it now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def get_windows_icon():
    """Return the best icon file for Windows builds if available."""
    icon_candidates = [
        PROJECT_ROOT / "assets" / "favicon.ico",
        PROJECT_ROOT / "assets" / "isama_icon.ico",
    ]
    for icon in icon_candidates:
        if icon.exists():
            return str(icon)
    return None


def build_executable():
    """Build the app using PyInstaller."""
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--name",
        APP_NAME,
    ]

    icon = get_windows_icon()
    if icon:
        cmd.extend(["--icon", icon])

    # Bundle project resources needed at runtime.
    for resource in ["assets", "ui"]:
        resource_path = PROJECT_ROOT / resource
        if resource_path.exists():
            cmd.extend(["--add-data", f"{resource_path}{os.pathsep}{resource}"])

    firebase_dir = PROJECT_ROOT / "firebase"
    if firebase_dir.exists():
        cmd.extend(["--add-data", f"{firebase_dir}{os.pathsep}firebase"])

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        cmd.extend(["--add-data", f"{env_file}{os.pathsep}."])

    service_key = PROJECT_ROOT / "firebase" / "service_key.json"
    if service_key.exists():
        cmd.extend(["--add-data", f"{service_key}{os.pathsep}firebase"])

    cmd.append(str(ENTRY_POINT))

    print("Building application...")
    print("Command:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(PROJECT_ROOT))


def copy_runtime_files():
    """Copy app runtime files next to the built EXE for easier local use."""
    dist_folder = DIST_DIR
    if not dist_folder.exists():
        print("No dist folder found; build may not have completed.")
        return

    exe_name = f"{APP_NAME}.exe"
    final_exe = dist_folder / exe_name
    if not final_exe.exists():
        print(f"Executable {exe_name} not found in dist folder.")
        return

    # Copy .env next to the exe if present.
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        shutil.copy2(env_file, dist_folder / ".env")

    # Copy service key next to the exe in a firebase folder.
    service_key = PROJECT_ROOT / "firebase" / "service_key.json"
    if service_key.exists():
        firebase_target = dist_folder / "firebase"
        firebase_target.mkdir(exist_ok=True)
        shutil.copy2(service_key, firebase_target / "service_key.json")

    print(f"Build complete. Your app is here: {final_exe}")


def main():
    print("=== Isama Management System Builder ===")
    ensure_pyinstaller()
    build_executable()
    copy_runtime_files()
    print("\nDone. You can run the generated EXE from the dist folder.")


if __name__ == "__main__":
    main()
