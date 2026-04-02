import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT / "job_bot"

for candidate in (ROOT, PACKAGE_DIR):
    value = str(candidate)
    if value not in sys.path:
        sys.path.insert(0, value)
