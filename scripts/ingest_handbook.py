#!/usr/bin/env python3
"""
Root forwarder for scripts/ingest_handbook.py.
Delegates to backend/scripts/ingest_handbook.py.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_SCRIPT = ROOT_DIR / "backend" / "scripts" / "ingest_handbook.py"

if not BACKEND_SCRIPT.exists():
    print(f"Error: Could not locate {BACKEND_SCRIPT}")
    sys.exit(1)

import subprocess

cmd = [sys.executable, str(BACKEND_SCRIPT)] + sys.argv[1:]
sys.exit(subprocess.call(cmd))
