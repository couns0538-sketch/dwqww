#!/usr/bin/env python3
"""opus_tools_md.py - print the TOOLS.md section for the R14 finish helper tools with their current md5s.

  python opus_tools_md.py            print the section (paste or append it to D:/a14/TOOLS.md)
  python opus_tools_md.py --check    exit 1 if any md5 written in D:/a14/TOOLS.md differs from the file on disk
Own code, standard library only.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path('D:/a14')
PY = r'D:\a14\runtime\python\python.exe -I -B'
TOOLS = [
    ('tools/opus_lowrun.py', 'Run a program at Idle priority on a CPU mask (read back; exit 78 if not confirmed) with '
     'CUDA/HIP_VISIBLE_DEVICES=-1; children inherit both.',
     PY + r' D:\a14\tools\opus_lowrun.py --mask 0x4 -- <python> -c "..." (prints the child mask/priority)'),
    ('tools/opus_seal.py', 'Seal/verify tool: verify-report (every {path, md5, bytes} of a REPORT, exact file set '
     'with --dir), seal (hash list of a directory), verify-seal.',
     PY + r' D:\a14\tools\opus_seal.py verify-seal D:\a14\sep\segments-production02\MAPS_SEAL.json'),
    ('tools/opus_prod_separation.py', 'Writes sep/PROD_SEPARATION.json from the two final scan reports '
     '(md5-pinned; no typed numbers).', 'run it and compare with the committed record (only updated_vienna differs)'),
    ('tools/opus_ep.py', 'EP normaliser: legal-capture-only en-passant status / FEN normalisation; invalid EP fails '
     'closed.', PY + r' -m pytest D:\a14\tests\test_opus_ep.py -q -p no:cacheprovider; '
     + PY + r' D:\a14\tools\opus_ep.py --oracle D:\grok-pc-data\selfplay_out\forge_selfplay_013.txt --limit 300000'),
    ('tools/opus_boardstm_probe.py', 'Independent fast board+stm overlap probe (raw FEN prefix, RAM hash index, '
     'exact resolution, md5 of every byte vs pins, EP census per file).',
     PY + r' -m pytest D:\a14\tests\test_opus_boardstm_probe.py -q -p no:cacheprovider'),
    ('tools/opus_boardstm_triage.py', 'Triage classifier: ep_format_diff / real_ep_diff / other per shared key and '
     'pair, EP-normalised 4-field recount, per class / holdout file / piece count, listing cross-check.',
     PY + r' -m pytest D:\a14\tests\test_opus_boardstm_triage.py -q -p no:cacheprovider'),
    ('tools/opus_guardband.py', 'Guard-band builder: contiguous jobA split cut at an UNREACHABLE link, K-ply guards, '
     'holdout-key / val-key / mate drops, every dropped row by id; stages candidate rows.',
     'proved by opus_guardband_proof.py (sep/GUARDBAND_SEPARATION.json)'),
    ('tools/opus_guardband_proof.py', 'Independent proof of a guard-band split: accounting, payload, three-key '
     'holdout check, train/val keys, chain cut, npt-data-holdout-check audit.',
     'read checks in sep/GUARDBAND_SEPARATION.json; re-run with a new --out / --big-dir'),
    ('tools/opus_tools_md.py', 'Prints this section; --check compares every md5 in TOOLS.md with the files.',
     PY + r' D:\a14\tools\opus_tools_md.py --check'),
]


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def section():
    out = ['', '## R14 finish helper tools (Opus, branch opus-astra-r14-finish)', '',
           'Own code under D:/a14/tools (licence-clean; python-chess appears only as a test oracle). Run with the R14 '
           'runtime at Idle on CPU 2 via opus_lowrun.py.', '',
           '| Tool (full path) | md5 | Purpose | How to verify |', '|---|---|---|---|']
    for rel, purpose, verify in TOOLS:
        path = ROOT / rel
        out.append(f"| {str(path).replace('/', chr(92))} | {md5(path)} | {purpose} | `{verify}` |")
    return '\n'.join(out) + '\n'


def check():
    text = (ROOT / 'TOOLS.md').read_text(encoding='utf-8')
    bad = 0
    for rel, _, _ in TOOLS:
        path = str(ROOT / rel).replace('/', '\\')
        m = re.search(re.escape(path) + r' \| ([0-9a-f]{32}) \|', text)
        if not m or m.group(1) != md5(ROOT / rel):
            print(f'MISMATCH {path}: TOOLS.md {m.group(1) if m else None} file {md5(ROOT / rel)}')
            bad += 1
    print(f"tools md5 check {'PASS' if not bad else 'FAIL'}: {len(TOOLS)} tools, {bad} mismatches")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(check() if '--check' in sys.argv else (print(section(), end='') or 0))
