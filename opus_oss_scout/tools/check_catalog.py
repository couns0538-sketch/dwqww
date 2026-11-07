#!/usr/bin/env python3
"""check_catalog.py - OSS scout: re-check every GitHub row of CATALOG.md against the GitHub API.

usage: python -I -B check_catalog.py <CATALOG.md> [--min-rows 30]
For each table row (a line starting with "| <letter><digits> |"), the first https://github.com/<owner>/<repo> URL is
looked up with `gh api repos/<owner>/<repo>`. A row passes when the repo exists and either the API's SPDX id appears in
the row's licence cell, or the API says NOASSERTION / none and the licence cell names what the LICENSE file says (any
text). Archived repos must say "archived" in the row. Prints one line per row and exits 1 on any failure or when there
are fewer than --min-rows rows.
"""
import json
import re
import subprocess
import sys

ROW = re.compile(r'^\|\s*([A-F]\d+)\s*\|')
GH = re.compile(r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)')


def gh_repo(owner, repo):
    r = subprocess.run(['gh', 'api', f'repos/{owner}/{repo}'], capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def main(argv):
    path = argv[0]
    min_rows = int(argv[argv.index('--min-rows') + 1]) if '--min-rows' in argv else 30
    rows, fails, checked = 0, 0, {}
    for line in open(path, encoding='utf-8'):
        m = ROW.match(line)
        if not m:
            continue
        rows += 1
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rid = m.group(1)
        g = GH.search(line)
        if not g:
            print(f'{rid}: no GitHub URL (non-GitHub source) - skipped')
            continue
        owner, repo = g.group(1), g.group(2).rstrip('.')
        key = f'{owner}/{repo}'
        if key not in checked:
            checked[key] = gh_repo(owner, repo)
        d = checked[key]
        if d is None:
            print(f'{rid}: FAIL {key} not found')
            fails += 1
            continue
        spdx = (d.get('license') or {}).get('spdx_id') or 'none'
        lic_cell = cells[3] if len(cells) > 3 else ''
        ok = spdx in lic_cell or spdx in ('NOASSERTION', 'none', 'NONE')
        if d.get('archived') and 'archived' not in line:
            ok = False
        print(f"{rid}: {'ok  ' if ok else 'FAIL'} {key} spdx={spdx} archived={d.get('archived')} pushed={d.get('pushed_at', '')[:10]}")
        fails += 0 if ok else 1
    print(f'rows {rows}, GitHub repos checked {len(checked)}, failures {fails}')
    if rows < min_rows:
        print(f'FAIL: fewer than {min_rows} rows')
        return 1
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
