"""R3-3 srand inventory scanner (read-only on every scanned path).

Walks file-system roots and/or git blobs, and for each text file:
  1. extracts srand / seed values found in context (JSON fields, fastchess CLI args, prose,
     Markdown tables and CSV files with an srand/seed column);
  2. records every literal occurrence of the candidate values given with --cands
     (digit-bounded 9-10 digit tokens), so a candidate that appears ANYWHERE is rejected.

Nothing is written except the --out JSON (which must be outside every scanned root or excluded).

Usage (file system):
  python -I -B srand_scan.py fs --root <dir> [--root <dir> ...] [--exclude <prefix> ...]
         [--depth1 <dir>] --cands <cands.json> --out <out.json>
Usage (git, run from a git work tree):
  python -I -B srand_scan.py git --repo <worktree> --refs-file <refs.txt> [--show-only-rev <rev>]
         --cands <cands.json> --out <out.json>
  Blobs of every listed ref are de-duplicated; blobs that exist only under --show-only-rev are read
  with `git show <rev>:<path>` (PC rule for Sol's branch), all others with `git cat-file --batch`.
"""
import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
import time

MAX_BYTES = 8 * 1024 * 1024
TEXT_EXT = {
    '.json', '.jsonl', '.md', '.txt', '.csv', '.tsv', '.ps1', '.psm1', '.py', '.sh', '.bat', '.cmd',
    '.yml', '.yaml', '.log', '.err', '.html', '.htm', '.cfg', '.ini', '.diff', '.patch', '.out',
    '.vbs', '.toml', '.xml', '.ok', '.rst', '.cpp', '.hpp', '.h', '.c', '.inc_txt', '.cmake',
}
SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'selfplay_out'}
SKIP_NAME_PARTS = ('engine_io',)
SKIP_EXT = {
    '.pgn', '.epd', '.fen', '.pos', '.bin', '.exe', '.dll', '.zip', '.gz', '.xz', '.7z', '.pt', '.pth',
    '.npy', '.npz', '.fnn2', '.nnue', '.o', '.obj', '.a', '.lib', '.pdb', '.dis', '.inc', '.png',
    '.jpg', '.jpeg', '.gif', '.pdf', '.rtbw', '.rtbz', '.pb', '.onnx', '.tar', '.whl', '.pyc',
}

# srand / seed in context. Group 1 = value.
CTX_PATTERNS = [
    ('srand_json', re.compile(r'"srand"\s*:\s*"?(\d{1,12})', re.I)),
    ('srand_cli', re.compile(r'-srand[\s"\',]+(\d{1,12})', re.I)),
    ('srand_kv', re.compile(r'\bsrand\s*[=:]\s*[`"\']?(\d{1,12})', re.I)),
    ('srand_text', re.compile(r'\bsrand[s]?\b[^0-9\n|]{0,60}?(\d{6,12})(?!\d)', re.I)),
    ('srand_ps', re.compile(r'\$srand\w*\s*=\s*(\d{1,12})', re.I)),
    ('seed_json', re.compile(r'"seed"\s*:\s*(\d{1,12})', re.I)),
    ('seed_cli', re.compile(r'(?<![\w-])--?seed[\s=]+(\d{1,12})', re.I)),
    ('seed_text', re.compile(r'\bseeds?\b[^0-9\n|]{0,30}?(\d{6,12})(?!\d)', re.I)),
]
TOKEN_RE = re.compile(r'(?<![0-9])([0-9]{9,10})(?![0-9])')
HDR_RE = re.compile(r'srand|seed', re.I)


def is_text_name(name):
    low = name.lower()
    if any(p in low for p in SKIP_NAME_PARTS):
        return False
    root, ext = os.path.splitext(low)
    if ext in SKIP_EXT:
        return False
    if ext in TEXT_EXT:
        return True
    # backup / staged copies such as forge_gates.json.bak_x, forge_queue.ps1.r7_..., x.md.bak
    for e in ('.json.', '.ps1.', '.md.', '.txt.', '.csv.', '.log.', '.py.'):
        if e in low:
            return True
    return False


def table_values(text):
    """Values from Markdown table columns and CSV columns whose header mentions srand/seed."""
    out = []
    lines = text.splitlines()
    # Markdown tables
    hdr_idx = None
    for ln in lines:
        s = ln.strip()
        if not s.startswith('|'):
            hdr_idx = None
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if hdr_idx is None:
            idx = [i for i, c in enumerate(cells) if HDR_RE.search(c)]
            if idx:
                hdr_idx = (idx, ln)
            continue
        if set(s.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
            continue  # separator row
        for i in hdr_idx[0]:
            if i < len(cells):
                for m in re.finditer(r'(?<!\d)(\d{4,12})(?!\d)', cells[i]):
                    out.append(('md_column', m.group(1), ln.strip()[:200]))
    # Pipe-separated plain tables (e.g. 'gate | folder | ... | srand | status')
    for k, ln in enumerate(lines):
        if '|' in ln and not ln.strip().startswith('|'):
            cells = [c.strip() for c in ln.split('|')]
            idx = [i for i, c in enumerate(cells) if c.lower() in ('srand', 'seed')]
            if idx:
                for ln2 in lines[k + 1:k + 400]:
                    if '|' not in ln2:
                        break
                    cells2 = [c.strip() for c in ln2.split('|')]
                    for i in idx:
                        if i < len(cells2) and re.fullmatch(r'\d{4,12}', cells2[i] or ''):
                            out.append(('pipe_column', cells2[i], ln2.strip()[:200]))
    # CSV
    first = lines[0] if lines else ''
    if ',' in first and HDR_RE.search(first):
        try:
            rd = csv.reader(io.StringIO(text))
            hdr = next(rd)
            idx = [i for i, c in enumerate(hdr) if HDR_RE.search(c or '')]
            for row in rd:
                for i in idx:
                    if i < len(row) and re.fullmatch(r'\d{4,12}', (row[i] or '').strip()):
                        out.append(('csv_column', row[i].strip(), ','.join(row)[:200]))
        except Exception:
            pass
    return out


class Scan:
    def __init__(self, cands):
        self.cands = set(cands)
        self.ctx = {}        # value -> list of [path, kind, snippet]
        self.hits = {}       # candidate -> list of paths
        self.files = 0
        self.bytes = 0
        self.skipped_big = []
        self.errors = []
        self.per_root = {}

    def scan_text(self, path, data, root_key):
        self.files += 1
        self.bytes += len(data)
        self.per_root.setdefault(root_key, [0, 0])
        self.per_root[root_key][0] += 1
        self.per_root[root_key][1] += len(data)
        text = data.decode('latin-1')
        if self.cands:
            for m in TOKEN_RE.finditer(text):
                v = m.group(1)
                if v in self.cands:
                    self.hits.setdefault(v, []).append(path)
        low = text.lower()
        if 'srand' not in low and 'seed' not in low:
            return
        for kind, rx in CTX_PATTERNS:
            for m in rx.finditer(text):
                a = max(0, m.start() - 60)
                snip = text[a:m.end() + 20].replace('\n', ' ').replace('\r', ' ')
                self.ctx.setdefault(m.group(1), []).append([path, kind, snip[:220]])
        for kind, v, snip in table_values(text):
            self.ctx.setdefault(v, []).append([path, kind, snip])

    def result(self, extra):
        used_srand = sorted({int(v) for v, srcs in self.ctx.items()
                             if any(s[1].startswith('srand') or s[1].endswith('_column') for s in srcs)})
        used_seed_only = sorted({int(v) for v, srcs in self.ctx.items()} - set(used_srand))
        d = {
            'files_scanned': self.files, 'bytes_scanned': self.bytes, 'per_root': self.per_root,
            'skipped_over_max_bytes': len(self.skipped_big), 'skipped_examples': self.skipped_big[:50],
            'errors': self.errors[:50], 'n_errors': len(self.errors),
            'used_srand_context_values': used_srand, 'seed_context_only_values': used_seed_only,
            'context': self.ctx, 'candidate_hits': self.hits, 'n_candidates': len(self.cands),
        }
        d.update(extra)
        return d


def walk(root, excludes, scan, depth1=False):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            it = list(os.scandir(d))
        except OSError as e:
            scan.errors.append(f'{d}: {e}')
            continue
        for e in it:
            p = e.path
            pn = os.path.normcase(os.path.abspath(p))
            if any(pn.startswith(x) for x in excludes):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    if not depth1 and e.name not in SKIP_DIRS:
                        stack.append(p)
                    continue
                if not e.is_file(follow_symlinks=False) or not is_text_name(e.name):
                    continue
                sz = e.stat().st_size
                if sz > MAX_BYTES:
                    scan.skipped_big.append([p, sz])
                    continue
                with open(p, 'rb') as fh:
                    data = fh.read()
                scan.scan_text(p, data, root)
            except OSError as ex:
                scan.errors.append(f'{p}: {ex}')


def cmd_fs(a):
    cands = json.load(open(a.cands)) if a.cands else []
    scan = Scan([str(c) for c in cands])
    ex = [os.path.normcase(os.path.abspath(x)) for x in (a.exclude or [])]
    t0 = time.time()
    for r in a.root or []:
        walk(r, ex, scan)
        print(f'[fs] {r}: files so far {scan.files}, {scan.bytes/1e6:.0f} MB, {time.time()-t0:.0f} s', flush=True)
    for r in a.depth1 or []:
        walk(r, ex, scan, depth1=True)
        print(f'[fs depth1] {r}: files so far {scan.files}', flush=True)
    res = scan.result({'mode': 'fs', 'roots': a.root, 'depth1_roots': a.depth1, 'excludes': a.exclude,
                       'max_bytes': MAX_BYTES, 'seconds': round(time.time() - t0, 1)})
    with open(a.out, 'w', newline='\n', encoding='utf-8') as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    print(f'[fs] done: {scan.files} files, {scan.bytes/1e6:.0f} MB, used srand values '
          f'{len(res["used_srand_context_values"])}, candidate hits {len(scan.hits)}', flush=True)


def git(repo, *args, inp=None):
    return subprocess.run(['git', '-C', repo] + list(args), input=inp, capture_output=True, check=True).stdout


def cmd_git(a):
    cands = json.load(open(a.cands)) if a.cands else []
    scan = Scan([str(c) for c in cands])
    refs = [r.strip() for r in open(a.refs_file) if r.strip() and not r.startswith('#')]
    t0 = time.time()
    blob_paths = {}   # blob -> (size, set(rev:path))
    for ref in refs:
        out = git(a.repo, 'ls-tree', '-r', '-l', '-z', ref)
        for rec in out.split(b'\0'):
            if not rec:
                continue
            meta, path = rec.split(b'\t', 1)
            mode, typ, obj, size = meta.split()
            if typ != b'blob' or size == b'-':
                continue
            path = path.decode('utf-8', 'replace')
            if not is_text_name(os.path.basename(path)):
                continue
            size = int(size)
            if size > MAX_BYTES:
                scan.skipped_big.append([f'{ref}:{path}', size])
                continue
            ent = blob_paths.setdefault(obj.decode(), [size, set()])
            ent[1].add((ref, path))
    print(f'[git] {len(refs)} refs, {len(blob_paths)} unique text blobs, {time.time()-t0:.0f} s', flush=True)
    show_only = a.show_only_rev
    via_show = {b: v for b, v in blob_paths.items() if show_only and all(r == show_only for r, _ in v[1])}
    via_cat = [b for b in blob_paths if b not in via_show]
    # cat-file --batch for blobs reachable from opus refs
    proc = subprocess.Popen(['git', '-C', a.repo, 'cat-file', '--batch'], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)
    for i, b in enumerate(via_cat):
        proc.stdin.write((b + '\n').encode())
        proc.stdin.flush()
        hdr = proc.stdout.readline().split()
        n = int(hdr[2])
        data = proc.stdout.read(n)
        proc.stdout.read(1)
        ref, path = sorted(blob_paths[b][1])[0]
        scan.scan_text(f'git:{ref}:{path}' + (f' (+{len(blob_paths[b][1])-1} refs)' if len(blob_paths[b][1]) > 1 else ''),
                       data, 'git_cat_file')
        if i % 5000 == 0:
            print(f'[git] cat-file {i}/{len(via_cat)} {time.time()-t0:.0f} s', flush=True)
    proc.stdin.close()
    proc.wait()
    # git show <rev>:<path> for blobs only in the show-only revision (one path per call keeps attribution)
    for i, (b, (size, rp)) in enumerate(sorted(via_show.items())):
        ref, path = sorted(rp)[0]
        try:
            data = git(a.repo, 'show', f'{show_only}:{path}')
        except subprocess.CalledProcessError as ex:
            scan.errors.append(f'git show {show_only}:{path}: {ex}')
            continue
        scan.scan_text(f'git:{show_only}:{path}', data, 'git_show_' + show_only)
        if i % 2000 == 0:
            print(f'[git] show {i}/{len(via_show)} {time.time()-t0:.0f} s', flush=True)
    res = scan.result({'mode': 'git', 'refs': refs, 'show_only_rev': show_only,
                       'n_blobs_cat_file': len(via_cat), 'n_blobs_git_show': len(via_show),
                       'max_bytes': MAX_BYTES, 'seconds': round(time.time() - t0, 1)})
    with open(a.out, 'w', newline='\n', encoding='utf-8') as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    print(f'[git] done: {scan.files} blobs, {scan.bytes/1e6:.0f} MB, used srand values '
          f'{len(res["used_srand_context_values"])}, candidate hits {len(scan.hits)}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    f = sub.add_parser('fs')
    f.add_argument('--root', action='append')
    f.add_argument('--depth1', action='append')
    f.add_argument('--exclude', action='append')
    f.add_argument('--cands')
    f.add_argument('--out', required=True)
    g = sub.add_parser('git')
    g.add_argument('--repo', required=True)
    g.add_argument('--refs-file', required=True)
    g.add_argument('--show-only-rev')
    g.add_argument('--cands')
    g.add_argument('--out', required=True)
    a = ap.parse_args()
    if a.cmd == 'fs':
        cmd_fs(a)
    else:
        cmd_git(a)


if __name__ == '__main__':
    sys.exit(main())
