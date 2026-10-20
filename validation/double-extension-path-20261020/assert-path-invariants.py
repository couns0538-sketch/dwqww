#!/usr/bin/env python3
"""One unchanged invariant assertion for baseline RED and candidate GREEN."""
from pathlib import Path
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('--summary', type=Path, required=True)
args = parser.parse_args()
summary = json.loads(args.summary.read_text())
assert summary['status'] == 'PASS' and summary['inputs_unchanged']
totals = summary['summary_totals']
assert totals['children'] > 0 and totals['single_extensions'] > 0
assert totals['double_extensions'] > 0 and totals['singular_attempts'] > 0
keys = ['same_ply_changed', 'single_parent_mismatch', 'eligibility_mismatch',
        'actual_vs_true_path_mismatch', 'null_parent_path_mismatch',
        'probcut_parent_path_mismatch', 'incoming_parent_path_mismatch']
failures = {key: totals[key] for key in keys if totals[key] != 0}
print(json.dumps({'status': 'FAIL' if failures else 'PASS', 'failures': failures,
                  'checked_selected_children': totals['children'],
                  'actual_double_extensions': totals['double_extensions']}))
raise SystemExit(1 if failures else 0)
