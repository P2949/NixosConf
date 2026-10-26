"""Compatibility entry point: the selection tests live in test_validation_targets.py."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_validation_targets import *  # noqa: E402,F401,F403

if __name__ == "__main__":
    unittest.main()
