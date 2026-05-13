"""
utils.py — Logging utilities for ForestFireMAS BDI.

Provides a context manager that redirects stdout + stderr to a
timestamped log file during crew.kickoff(), so the terminal only
shows BDI belief updates and section headers.

Usage:
    from utils import agent_log

    with agent_log("scenario1") as log_path:
        result = crew.kickoff()
    print(f"  Agent reasoning saved to: {log_path}")
"""

import os
import sys
from contextlib import contextmanager
from datetime import datetime


LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")


@contextmanager
def agent_log(label: str):
    """
    Redirect stdout and stderr to a log file for the duration of the block.

    Args:
        label: short name used in the filename (e.g. "scenario1")

    Yields:
        str: the path to the log file being written
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOGS_DIR, f"{label}_{timestamp}.log")

    print(f"\n  Agent reasoning → {log_path}")
    print(  "  (console shows BDI belief updates only)\n")

    old_stdout = sys.stdout
    old_stderr = sys.stderr

    with open(log_path, "w", encoding="utf-8") as f:
        sys.stdout = f
        sys.stderr = f
        try:
            yield log_path
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
