#!/usr/bin/env python3
"""Freeze final helper code and re-export the retained checkpoint without retraining."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

import torch

ROOT = Path(__file__).resolve().parents[3]
base = Path(__file__).resolve().parent
original = base / 'run1'
out = base / 'export_revalidation'
out.mkdir(exist_ok=False)
source = out / 'source'
source.mkdir()
paths = [ROOT / 'tools/bullet/lock_export.py', ROOT / 'tools/bullet/export_forge.py',
         ROOT / 'tools/bullet/train_lock_cpu_smoke.py', ROOT / 'tools/data/forge_pos.py']
source_hashes = {}
for path in paths:
    shutil.copyfile(path, source / path.name)
    source_hashes[path.name] = hashlib.sha256((source / path.name).read_bytes()).hexdigest()
sys.path.insert(0, str(source))
import lock_export

torch.set_num_threads(1)
checkpoint = torch.load(original / 'trained/state.pt', map_location='cpu', weights_only=True)
arrays = {key: value.numpy() for key, value in checkpoint['state_dict'].items()}
manifest = json.loads((original / 'trained/manifest.json').read_text())
lock_export.write_checkpoint(out / 'trained', arrays, manifest['provenance'], manifest['description'])
q = lock_export.load_quantized(out / 'trained/weights.bin', out / 'trained/manifest.json')
with (out / 'sample.inc').open('xb') as stream:
    stream.write(lock_export.render_include(q))
fens = Path(sys.argv[1]).resolve()
with fens.open() as stream, (out / 'reference12k.txt').open('x') as reference:
    count = 0
    for line in stream:
        cp, bits = lock_export.evaluate(q, line.strip())
        reference.write(f'{cp} {bits}\n')
        count += 1
checks = {}
for name in ('trained/weights.bin', 'trained/manifest.json', 'sample.inc', 'reference12k.txt'):
    before = hashlib.sha256((original / name).read_bytes()).hexdigest()
    after = hashlib.sha256((out / name).read_bytes()).hexdigest()
    checks[name] = {'original_sha256': before, 'revalidated_sha256': after, 'identical': before == after}
unchanged = all(hashlib.sha256(path.read_bytes()).hexdigest() == source_hashes[path.name] for path in paths)
result = {'status': 'PASS' if unchanged and all(item['identical'] for item in checks.values()) else 'FAIL',
          'reason': 'Exporter changed concurrently after run1; exact frozen final code replay verifies preserved outputs without retraining.',
          'source_hashes': source_hashes, 'source_unchanged_during_revalidation': unchanged,
          'run1_recorded_implementation': json.loads((original / 'metrics.json').read_text())['implementation'],
          'fens_sha256': hashlib.sha256(fens.read_bytes()).hexdigest(), 'positions': count, 'checks': checks}
with (out / 'receipt.json').open('x') as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(result))
raise SystemExit(int(result['status'] != 'PASS'))
