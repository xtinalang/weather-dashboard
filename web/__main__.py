#!/usr/bin/env python
"""
Main entry point for direct module execution.
This lets you run the app with:
  python -m web
"""

from .app import run

if __name__ == "__main__":
    run()
