"""Inventory the independent interpreter without importing numerical modules."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import sys


def main():
    root = Path('D:/a14')
    runtime = root / 'runtime'
    if not Path(sys.executable).resolve().is_relative_to(runtime.resolve()):
        raise RuntimeError('Independent interpreter required')
    out = root / 'evidence/r14/runtime-files.jsonl'
    if out.exists():
        raise FileExistsError(out)
    total = count = 0
    with out.open('x', encoding='utf-8', newline='\n') as stream:
        for path in sorted(runtime.rglob('*')):
            if path.is_symlink():
                raise RuntimeError(f'Redirected runtime entry: {path}')
            if not path.is_file():
                continue
            md5, sha = hashlib.md5(), hashlib.sha256()
            with path.open('rb') as handle:
                while data := handle.read(1024 * 1024):
                    md5.update(data)
                    sha.update(data)
            size = path.stat().st_size
            total += size
            count += 1
            stream.write(json.dumps(dict(path=str(path), bytes=size, md5=md5.hexdigest(), sha256=sha.hexdigest())) + '\n')
    packages = sorted((dict(name=d.metadata['Name'], version=d.version,
                            location=str(d.locate_file('')))
                       for d in importlib.metadata.distributions()), key=lambda x: x['name'].lower())
    receipt = dict(python=sys.version, executable=sys.executable, sys_path=sys.path,
                   packages=packages, files=count, bytes=total,
                   inventory=str(out), inventory_md5=hashlib.md5(out.read_bytes()).hexdigest())
    destination = root / 'evidence/r14/runtime-identity.json'
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
