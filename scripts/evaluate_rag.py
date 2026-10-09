#!/usr/bin/env python3
"""
Root forwarder for scripts/evaluate_rag.py.
Delegates to backend/scripts/evaluate_rag.py.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_SCRIPT = ROOT_DIR / "backend" / "scripts" / "evaluate_rag.py"

if not BACKEND_SCRIPT.exists():
    print(f"Error: Could not locate {BACKEND_SCRIPT}")
    sys.exit(1)

import subprocess

cmd = [sys.executable, str(BACKEND_SCRIPT)] + sys.argv[1:]
sys.exit(subprocess.call(cmd))
