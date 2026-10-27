"""Compare a source tree with a recorded snapshot {files: {relpath: {sha256, bytes}}}; exit 1 on any difference."""
import hashlib
import json
import os
import sys


def tree(root):
    out = {}
    for d, ds, fs in os.walk(root):
        ds[:] = sorted(x for x in ds if x not in ('.git', '__pycache__'))
        for f in fs:
            p = os.path.join(d, f)
            with open(p, 'rb') as h:
                data = h.read()
            out[os.path.relpath(p, root).replace(os.sep, '/')] = {'sha256': hashlib.sha256(data).hexdigest(),
                                                                   'bytes': len(data)}
    return out


def main():
    snap = json.load(open(sys.argv[1], encoding='utf-8'))['files']
    mine = tree(sys.argv[2])
    diff = {'mismatch': sorted(k for k in snap if k in mine and mine[k] != snap[k]),
            'missing': sorted(k for k in snap if k not in mine),
            'extra': sorted(k for k in mine if k not in snap)}
    ok = not any(diff.values())
    print(json.dumps(dict(diff, snapshot_files=len(snap), tree_files=len(mine),
                          status='IDENTICAL' if ok else 'DIFFERENT'), sort_keys=True))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
