#!/usr/bin/env python3
"""index_check_o30.py [INDEX.md] - Opus 30-h job: every net section of D:\\o30\\nets\\INDEX.md must cite files whose
hashes match: the net's sha256 AND md5 (row `net sha256 / md5`) and the gate exe's sha256 (row `exe (gate)`). A section
without one of these rows is a FAIL (the generator's format changed), so a check cannot pass by matching nothing.
Exit 0 only if every section was checked and every hash matched (own code; replaces final_checks check 12's regex,
which matched the exe rows only)."""
import hashlib
import re
import sys


def digest(path, algo):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    index = sys.argv[1] if len(sys.argv) > 1 else r'D:\o30\nets\INDEX.md'
    text = open(index, encoding='utf-8').read()
    sections = re.split(r'^## ', text, flags=re.M)[1:]
    bad = checked = 0
    for s in sections:
        name = s.splitlines()[0].strip()
        net = re.search(r'^\| net \(full path\) \| `([^`]+)` \|', s, re.M)
        nh = re.search(r'^\| net sha256 / md5 \| ([0-9a-f]{64}) / ([0-9a-f]{32}) \|', s, re.M)
        exe = re.search(r'^\| exe \(gate\) \| `([^`]+)` sha256 ([0-9a-f]{64}) \|', s, re.M)
        if not (net and nh and exe):
            print(f'FAIL {name}: a net / hash / exe row is missing')
            bad += 1
            continue
        for path, want, algo in ((net.group(1), nh.group(1), 'sha256'), (net.group(1), nh.group(2), 'md5'),
                                 (exe.group(1), exe.group(2), 'sha256')):
            try:
                got = digest(path, algo)
            except OSError as e:
                print(f'FAIL {name}: {path}: {e}')
                bad += 1
                continue
            checked += 1
            ok = got == want
            bad += not ok
            print(f"{'ok  ' if ok else 'BAD '} {name} {algo} {path}" + ('' if ok else f' (file {got}, cited {want})'))
    print(f'index_check_o30: {len(sections)} sections, {checked} hashes checked, {bad} problems')
    sys.exit(0 if bad == 0 and sections else 1)


if __name__ == '__main__':
    main()
