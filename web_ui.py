#!/usr/bin/env python3
"""
ReelPublisher Web UI Runner
Entrypoint for local and container studio execution.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from server import start_server, PORT

if __name__ == "__main__":
    start_server(port=PORT)
