#!/usr/bin/env python3
"""
install_dependencies.py
Ensures all dependencies in src/Settings/requirements.txt are installed
before running the main project.
"""

import subprocess
import sys
import pkg_resources
from pathlib import Path

def get_requirements_path() -> Path:
    """Locate src/Settings/requirements.txt relative to the project root."""
    # Start from this file and move upward until we find the src directory
    current_dir = Path(__file__).resolve().parent

    # Walk upward until we find a folder named 'src'
    for parent in current_dir.parents:
        src_dir = parent / "src"
        if src_dir.exists() and src_dir.is_dir():
            return src_dir / "Settings" / "requirements.txt"

    # Fallback: assume top-level structure
    return Path(__file__).resolve().parent.parent / "src" / "Settings" / "requirements.txt"


def install_requirements():
    """Check for and install missing dependencies."""
    req_path = get_requirements_path()

    if not req_path.exists():
        print(f"❌ Could not find requirements file at: {req_path}")
        sys.exit(1)

    with req_path.open() as f:
        dependencies = [
            line.strip() for line in f
            if line.strip() and not line.startswith("#")
        ]

    if not dependencies:
        print("⚠️ No dependencies listed in requirements.txt.")
        return

    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = [
        dep for dep in dependencies
        if dep.lower().split("==")[0] not in installed
    ]

    if not missing:
        print("✅ All dependencies already installed.")
        return

    print(f"📦 Installing missing packages: {', '.join(missing)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        print("✅ Installation complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        sys.exit(1)


if __name__ == "__main__":
    install_requirements()
