#!/usr/bin/env python3
"""Record the exact offline validation command, output, and source hashes."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


package = Path(__file__).resolve().parent
repo = package.parents[1]
command = [sys.executable, "-B", str(package / "test_recovery.py")]
result = subprocess.run(command, cwd=repo, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(package / "offline-checks.log").write_text(result.stdout, encoding="utf-8")
inputs = [repo / ".github/workflows/forge-recover-confirmation.yml",
          repo / ".github/hosted-nnue-strength/archive_results.py",
          repo / ".github/workflows/forge-hosted-confirmation.yml"]
inputs += [package / name for name in ("recover.py", "test_recovery.py", "validate.py", "protocol.json")]
counts = re.findall(r"Ran (\d+) tests?", result.stdout)
record = {"schema_version": 1, "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
          "command": command, "cwd": str(repo), "environment_override": {"PYTHONDONTWRITEBYTECODE": "1"},
          "returncode": result.returncode, "test_count": int(counts[-1]) if counts else None,
          "checks": ["frozen REST identities", "no retrieval after mismatched identity or pending review",
                     "HTTPS redirects remove bearer", "log failure still permits original ZIP retrieval",
                     "original ZIP and extracted byte equality", "nonregular raw nodes rejected",
                     "unmodified original joblog", "frozen archive helper round-trip and full raw inventory",
                     "publication allowlist and maximum manifest/part size", "YAML trigger and action pins",
                     "14-minute maximum sum of step budgets within 15-minute job", "bash -n on every shell block"],
          "source_sha256": {str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
          "not_executed": ["network retrieval", "Git mutation", "push", "hosted workflow launch", "match/engine/test binary"]}
(package / "offline-checks.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
sys.stdout.write(result.stdout)
raise SystemExit(result.returncode)
