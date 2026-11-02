"""Run the bundled disposable fixture; explicit late-order auxiliary scope."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path('D:/a10')
sys.path.insert(0, str(ROOT / 'pydeps'))
import psutil
sys.path.insert(0, str(ROOT / 'wt/skills/gate-handover-pack/scripts'))
import seal_evidence as safety

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--threads', type=int, choices=[1], required=True)
args = parser.parse_args()
out = safety.checked_path(args.out)
proc = psutil.Process()
if proc.nice() != psutil.IDLE_PRIORITY_CLASS or proc.cpu_affinity() != [3]:
    raise RuntimeError('Idle CPU3-only fixture required')
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
script = ROOT / 'wt/skills/resumable-shard-job/scripts/resume_fixture.py'
before = hashlib.sha256(script.read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location('owned_resume_fixture', script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.selftest(out)
if hashlib.sha256(script.read_bytes()).hexdigest() != before:
    raise RuntimeError('fixture helper changed during execution')
ordering = {'schema': 1, 'classification': 'UNPROVEN', 'scope': 'auxiliary disposable fixture only',
            'worker_sha256': before, 'status': result['status'],
            'ordering_deviation': 'The skill requires this selftest before native adapter proof. R10 ran it after native proofs01/02/03; that ordering requirement was missed and is not retroactively satisfied.',
            'meaning': 'Only this newly created fixture child was terminated. No trainer, gate, crew or other process was touched. This result does not replace or upgrade actual adapter evidence.'}
with (out / 'ORDERING.json').open('x') as stream:
    json.dump(ordering, stream, indent=2)
print(json.dumps({'fixture': result, 'ordering': ordering}, indent=2))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
