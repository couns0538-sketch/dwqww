#!/usr/bin/env python3
"""Metadata-only helper-name control using actual generated CTest registrations."""
from pathlib import Path
import argparse, ast, hashlib, json, re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mode', choices=('old', 'generated'), required=True)
parser.add_argument('--old-script', type=Path, required=True)
parser.add_argument('--cmake', type=Path, required=True)
parser.add_argument('--ctest', type=Path, required=True)
parser.add_argument('--history-root', type=Path, required=True)
parser.add_argument('--archive-build-root', type=Path, required=True)
args = parser.parse_args()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
targets = set(re.findall(r'add_executable\((\w+)', args.cmake.read_text()))
registered = {Path(path).name for path in re.findall(r'add_test\(\S+ "([^"]+)"', args.ctest.read_text())}
required = sorted((targets & registered) - {'forge', 'forge_tests', 'forge_bench'})
old_sets = [ast.literal_eval(node) for node in ast.walk(ast.parse(args.old_script.read_text()))
            if isinstance(node, ast.Set) and all(isinstance(x, ast.Constant) and isinstance(x.value, str) for x in node.elts)
            and any(x.value == 'libforge_core.a' for x in node.elts)]
if len(old_sets) != 1 or not required:
    raise ValueError('actual helper-name source is ambiguous or missing')
inventory = {}
for path in sorted(args.history_root.glob('forge_sol_S00_*/forge_sol_S00_*cache_restore_map_20261025.json')):
    for row in json.loads(path.read_text())['files']:
        inventory.setdefault(row['path'], []).append(row)
allowed = old_sets[0] if args.mode == 'old' else set(required)
rows = []
for target in required:
    original = args.archive_build_root / target
    records = inventory.get(str(original), [])
    status = 'MISSING_GUESSED_ALLOWLIST_NAME' if target not in allowed else ('MISSING_EXACT_ARCHIVE_PATH' if not records else 'READY_NAME_AND_IDENTITY_RECORD')
    rows.append({'target': target, 'original_path': str(original), 'status': status,
                 'archive_identities': sorted({row['sha256'] for row in records})})
result = {'status': 'PASS' if all(x['status'] == 'READY_NAME_AND_IDENTITY_RECORD' for x in rows) else 'FAIL',
          'mode': args.mode, 'cmake_sha256': sha(args.cmake), 'ctest_sha256': sha(args.ctest),
          'old_script_sha256': sha(args.old_script), 'required_helpers': len(required), 'rows': rows,
          'scope': 'Target-name and archive metadata control only; no restore, native execution, deletion or binary qualification'}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
