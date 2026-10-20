#!/usr/bin/env python3
"""One explicit inventory refresh after root metadata edits; never run automatically."""
import hashlib
from pathlib import Path
repo=Path(__file__).resolve().parents[2];package=repo/'.github/hosted-pin-mask-strength';out=package/'PACKAGE-SHA256SUMS'
files=[p for p in package.rglob('*') if p.is_file() and p!=out]+[repo/'.github/workflows/forge-hosted-pin-mask-strength.yml']
files.sort(key=lambda p:p.relative_to(repo).as_posix());assert not any('__pycache__' in p.parts or p.suffix=='.pyc' for p in files)
out.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(repo).as_posix()+'\n' for p in files))
print(len(files),'files',hashlib.sha256(out.read_bytes()).hexdigest())
