#!/usr/bin/env python3
"""Put git status --short and ls -la at the end of REPORT.md."""
import subprocess
from pathlib import Path

repo = Path("/agent/repos/dwqww")
seat = repo / "forge-combo29" / "grok" / "017"
report_path = seat / "REPORT.md"
text = report_path.read_text()
marker = "## git status --short"
start = text.find(marker)
if start < 0:
    raise SystemExit("marker missing")
head = text[:start]
status = subprocess.check_output(["git", "status", "--short"], cwd=repo, text=True)
listing = subprocess.check_output(["ls", "-la", str(seat)], text=True)
body = (
    head
    + "## git status --short\n\n```\n"
    + status
    + "```\n\n## ls -la\n\n```\n"
    + listing
    + "```\n"
)
report_path.write_text(body)
listing2 = subprocess.check_output(["ls", "-la", str(seat)], text=True)
status2 = subprocess.check_output(["git", "status", "--short"], cwd=repo, text=True)
body = (
    head
    + "## git status --short\n\n```\n"
    + status2
    + "```\n\n## ls -la\n\n```\n"
    + listing2
    + "```\n"
)
report_path.write_text(body)
print("status lines", len(status2.splitlines()))
print("ls lines", len(listing2.splitlines()))
print("has RESULT", "RESULT.txt" in listing2)
print("has REPORT", "REPORT.md" in listing2)
