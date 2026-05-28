#!/usr/bin/env python3
"""
Run this once before starting the server to create the database.
Usage:  python init_db.py
"""
import os
import sys

# Make sure we can import project modules
sys.path.insert(0, os.path.dirname(__file__))

from includes.db import init_db

if __name__ == '__main__':
    print("Initialising ALChicken database...")
    init_db()
    print("Done! Database created at sql/alchicken.db")
    print("Default admin login: admin@alchicken.com  (see database.sql for password hash)")
