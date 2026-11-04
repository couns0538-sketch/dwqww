#!/usr/bin/env python3
"""opus_seal.py - R14 finish (Opus): seal and verify file sets (own code, standard library only).

  verify-report <REPORT.json> [--dir D]  every object in the report that names a file ("path" + "md5", optional
                                          "bytes") must match the file; with --dir, the directory must hold exactly the
                                          report's files below it (no extra, none missing). Exit 0 = PASS.
  seal <dir> --out <hashlist.json>        hash list of every file below <dir>: relative path, bytes, md5, sha256
                                          (the output file is refused inside <dir>, so it never lists itself).
  verify-seal <hashlist.json> [--root R]  re-hash every listed file (root = the list's own "root" unless --root);
                                          exit 0 only if every file exists with the listed bytes / md5 / sha256.
Fail closed: an unreadable file, a missing field or an extra file is a FAIL, never a skip.
"""
import argparse
import hashlib
import json
import os
import sys


def digests(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    n = 0
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            md5.update(block)
            sha.update(block)
            n += len(block)
    return n, md5.hexdigest(), sha.hexdigest()


def file_entries(obj, out):
    if isinstance(obj, dict):
        if isinstance(obj.get('path'), str) and isinstance(obj.get('md5'), str):
            out.append(obj)
        for v in obj.values():
            file_entries(v, out)
    elif isinstance(obj, list):
        for v in obj:
            file_entries(v, out)
    return out


def cmd_verify_report(a):
    report = json.load(open(a.report, encoding='utf-8'))
    entries = file_entries(report, [])
    bad = 0
    seen = set()
    for e in entries:
        p = e['path']
        try:
            n, md5, _ = digests(p)
        except OSError as err:
            print(f'FAIL {p}: {err}')
            bad += 1
            continue
        ok = md5 == e['md5'].lower() and (e.get('bytes') is None or int(e['bytes']) == n)
        bad += not ok
        seen.add(os.path.normcase(os.path.abspath(p)))
        print(f"{'ok  ' if ok else 'FAIL'} {p} md5 {md5}" + ('' if ok else f" (report {e['md5']}, bytes {e.get('bytes')} vs {n})"))
    if a.dir:
        root = os.path.abspath(a.dir)
        listed = {s for s in seen if s.startswith(os.path.normcase(root) + os.sep)}
        on_disk = {os.path.normcase(os.path.join(dp, f)) for dp, _, fs in os.walk(root) for f in fs}
        extra, missing = sorted(on_disk - listed), sorted(listed - on_disk)
        for x in extra:
            print(f'FAIL extra file not in the report: {x}')
        for x in missing:
            print(f'FAIL listed file missing: {x}')
        bad += len(extra) + len(missing)
        print(f'directory {root}: {len(on_disk)} files on disk, {len(listed)} listed by the report')
    print(f"verify-report {'PASS' if bad == 0 and entries else 'FAIL'}: {len(entries)} file entries, {bad} problems")
    return 0 if bad == 0 and entries else 1


def cmd_seal(a):
    root = os.path.abspath(a.dir)
    out = os.path.abspath(a.out)
    if os.path.normcase(out).startswith(os.path.normcase(root) + os.sep):
        sys.exit('refusing: the hash list would list itself (write it outside the sealed directory)')
    if os.path.exists(out):
        sys.exit(f'refusing: {out} exists')
    files = []
    for dp, _, fs in os.walk(root):
        for f in sorted(fs):
            p = os.path.join(dp, f)
            n, md5, sha = digests(p)
            files.append({'path': os.path.relpath(p, root).replace('\\', '/'), 'bytes': n, 'md5': md5, 'sha256': sha})
    files.sort(key=lambda e: e['path'])
    rec = {'schema': 1, 'tool': 'opus_seal.py seal', 'root': root, 'files': files,
           'total_bytes': sum(e['bytes'] for e in files), 'count': len(files)}
    with open(out, 'x', encoding='utf-8', newline='\n') as f:
        json.dump(rec, f, indent=1)
    print(f'sealed {len(files)} files ({rec["total_bytes"]} bytes) below {root} -> {out}')
    return 0


def cmd_verify_seal(a):
    rec = json.load(open(a.hashlist, encoding='utf-8'))
    root = a.root or rec['root']
    bad = 0
    for e in rec['files']:
        p = os.path.join(root, e['path'])
        try:
            n, md5, sha = digests(p)
        except OSError as err:
            print(f'FAIL {p}: {err}')
            bad += 1
            continue
        ok = (n, md5, sha) == (e['bytes'], e['md5'], e['sha256'])
        bad += not ok
        if not ok:
            print(f'FAIL {p}')
    print(f"verify-seal {'PASS' if bad == 0 and rec['files'] else 'FAIL'}: {len(rec['files'])} files, {bad} problems")
    return 0 if bad == 0 and rec['files'] else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    v = sub.add_parser('verify-report')
    v.add_argument('report')
    v.add_argument('--dir')
    s = sub.add_parser('seal')
    s.add_argument('dir')
    s.add_argument('--out', required=True)
    w = sub.add_parser('verify-seal')
    w.add_argument('hashlist')
    w.add_argument('--root')
    a = ap.parse_args()
    sys.exit({'verify-report': cmd_verify_report, 'seal': cmd_seal, 'verify-seal': cmd_verify_seal}[a.cmd](a))


if __name__ == '__main__':
    main()
