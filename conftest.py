import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
TEST_SUITE_DIR = REPO_ROOT / "test_suite"

# Make the application code and test helpers importable without manual PYTHONPATH setup.
for extra_path in (REPO_ROOT / "src", TEST_SUITE_DIR):
    extra_path_str = str(extra_path)
    if extra_path_str not in sys.path:
        sys.path.insert(0, extra_path_str)


def pytest_sessionstart(session):
    # Most tests use paths relative to the historical `cd test_suite && pytest` workflow.
    os.chdir(TEST_SUITE_DIR)
