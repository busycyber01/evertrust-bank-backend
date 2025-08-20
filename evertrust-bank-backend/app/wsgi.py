#!/usr/bin/env python3
"""
Production WSGI entry point for EverTrust Bank
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    # This allows running with: python wsgi.py
    app.run()