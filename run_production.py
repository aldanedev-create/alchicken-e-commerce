#!/usr/bin/env python
"""
ALChicken Production Server Launcher
Run with: python run_production.py
"""

import os
from app import app

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run with Gunicorn (this is just a launcher, actual server uses gunicorn command)
    print(f"Starting ALChicken production server on port {port}")
    print("Use: gunicorn --config gunicorn.conf.py app:app")