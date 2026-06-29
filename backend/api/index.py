"""
Vercel serverless entry point for the QueryMind FastAPI backend.

Vercel's Python runtime serves the ASGI `app` exported from this module.
All incoming requests are routed here via vercel.json, and FastAPI matches
the original path (e.g. /api/chats).
"""

import os
import sys

# Make the backend root (parent of this /api dir) importable so `main` resolves.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: E402,F401  (re-exported for Vercel)
