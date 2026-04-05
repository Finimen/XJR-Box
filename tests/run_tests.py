#!/usr/bin/env python
#poetry run pytest tests/unit/ -v --cov=scr.services --cov-report=term-missing

import subprocess
import sys


def run_tests():
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--cov=scr",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--asyncio-mode=auto"
    ])
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())