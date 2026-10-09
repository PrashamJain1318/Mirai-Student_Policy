"""
Root backend entry point loading FastAPI app from backend/backend.py.
Allows running `uvicorn backend:app` from the project root directory.
"""

import sys
import importlib.util
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure sys.modules["backend"] points to backend/backend.py
_backend_file = BACKEND_DIR / "backend.py"
_spec = importlib.util.spec_from_file_location("backend", str(_backend_file))
if _spec and _spec.loader:
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["backend"] = _mod
    _spec.loader.exec_module(_mod)
    globals().update(_mod.__dict__)
else:
    raise ImportError(f"Could not load backend application from {_backend_file}")
