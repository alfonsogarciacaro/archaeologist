#!/usr/bin/env python3
"""
Scanner Benchmark Runner

This script provides a convenient way to run the RAG benchmark
from the scanner directory with proper Python path setup.
"""

import sys
import os
import subprocess
from pathlib import Path

# Set environment variables
env_file = Path(__file__).parent.parent / ".env.dev"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Run as module properly
if __name__ == "__main__":
    # Change to scanner directory and run as module
    scanner_dir = Path(__file__).parent
    cmd = ["uv", "run", "python", "-m", "app.benchmark"] + sys.argv[1:]
    subprocess.run(cmd, cwd=scanner_dir)