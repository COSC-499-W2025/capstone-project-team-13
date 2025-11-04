#!/usr/bin/env python3
"""
install_dependencies.py
Ensures all dependencies in requirements.txt are installed before running the main project.
"""

import subprocess
import sys
import pkg_resources
from pathlib import Path

def install_requirements(requirements_file: str = "requirements.txt"):
    """Installs any missing dependencies listed in requirements.txt."""
    req_path = Path(requirements_file)

    if not req_path.exists():
        print(f"❌ {requirements_file} not found. Please create one with your dependencies.")
        sys.exit(1)

    with req_path.open() as f:
        dependencies = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = [pkg for pkg in dependencies if pkg.lower().split("==")[0] not in installed]

    if not missing:
        print("✅ All dependencies already installed.")
        return

    print(f"📦 Installing missing packages: {', '.join(missing)}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
    print("✅ Installation complete.")


if __name__ == "__main__":
    install_requirements()
