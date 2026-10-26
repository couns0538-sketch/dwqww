#!/usr/bin/env python3
"""Configuration contract only: imports tests, launches no tests or engines."""
import importlib.util
import os
from pathlib import Path
import sys
module_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("s07_locator_subject", module_path)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
assert subject.SOURCE == Path(os.environ["FORGE_S07_FILES_ROOT"]), "test fixture SOURCE ignored FORGE_S07_FILES_ROOT"
assert subject.SUITE == Path(os.environ["FORGE_S07_WAC_SUITE"]), "test fixture SUITE ignored FORGE_S07_WAC_SUITE"
print("PASS: both fixture overrides are honored")
