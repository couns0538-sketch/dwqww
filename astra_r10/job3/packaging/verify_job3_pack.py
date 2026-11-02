"""Reuse the independent Job1 checksum verifier; enforce incomplete-data purpose."""
import argparse
import importlib.util
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--threads', type=int, choices=[1], required=True)
parser.add_argument('--pack', type=Path, required=True)
args = parser.parse_args()
helper = Path('D:/a10/wt/astra_r10/job1/packaging/verify_pack.py')
spec = importlib.util.spec_from_file_location('independent_pack_checksums', helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.check(args.pack.is_absolute() and args.pack.is_relative_to(Path('D:/a10')), 'D:/a10 pack required')
module.safe(args.pack, args.pack)
report = json.loads((args.pack / 'REPORT.json').read_text(encoding='utf-8'))
module.check(report.get('purpose') == 'incomplete-data' and report.get('training_clearance') == 'BLOCKED',
             'Job3 must remain explicitly incomplete-data with blocked training')
module.verify(args.pack)
