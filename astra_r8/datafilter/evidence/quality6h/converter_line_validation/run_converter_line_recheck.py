"""Owned bounded converter replay, preserving every previous output. UNPROVEN."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

WORK = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter')
HERE = WORK/'astra_r8/datafilter'
sys.path.insert(0, str(HERE))
from audit_followup import run
from filter_positions import low_priority, sha256
from resource_policy import storage_guard

low_priority()
root = Path('C:/astra8_data/quality6h_20261102/converter_line_validation')
storage_guard(root, allowance=100_000_000)
root.mkdir()
watched = [HERE/name for name in ('audit_followup.py', 'audit.py',
           'audit_stm_roundtrip.py', 'convert_forge.py', 'records.py',
           'result_codec.py', 'filter_lichess_rec.py', 'signcheck.py',
           'pgn_input.py', 'filter_positions.py', 'resource_policy.py')]
before = {str(p):sha256(p) for p in watched}
started = time.perf_counter()
receipt = dict(source_commit=subprocess.check_output(
    ['git','rev-parse','HEAD'],cwd=WORK,text=True).strip(),
    candidate_files=before, purpose='Reviewed CR/LF admission correction',
    strength='UNPROVEN', threads=1, priority='BelowNormal')
(root/'RUN.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
for stage in ('identity','orientation'):
    print('START '+stage,flush=True)
    report=run(stage,root)
    print(json.dumps(report),flush=True)
after={str(p):sha256(p) for p in watched}
if before!=after:
    raise ValueError('candidate changed during converter replay')
receipt.update(status='PASS',runtime_unchanged=True,
               elapsed_seconds=time.perf_counter()-started,
               artifacts={p.name:sha256(p) for p in root.glob('*_receipt.json')})
(root/'RECHECK.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt),flush=True)
