#!/usr/bin/env python3
"""Refresh the package/workflow SHA256 inventory after reviewed metadata edits."""
import hashlib
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
package = repo / '.github/hosted-nnue-strength'
inventory = package / 'PACKAGE-SHA256SUMS'
files = sorted(path for path in package.rglob('*') if path.is_file() and path != inventory)
assert not any('__pycache__' in path.parts or path.suffix == '.pyc' for path in files), 'Unexpected package bytecode'
files += [repo / '.github/workflows/forge-hosted-nnue-strength.yml']
inventory.write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' +
                           path.relative_to(repo).as_posix() + '\n' for path in files))
print(str(inventory.relative_to(repo)), len(files), 'frozen files',
      hashlib.sha256(inventory.read_bytes()).hexdigest())
