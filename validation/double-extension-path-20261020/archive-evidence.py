#!/usr/bin/env python3
"""Preserve immutable actual-engine RED/GREEN originals with trusted helper."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STAGE = Path('/workspace/.cloud-setup/double-extension-path-complete-stage')
STAGE.mkdir(exist_ok=False)
OUT = HERE / 'archive-complete'
helper = REPO / '.github/hosted-tt-strength/archive_results.py'
expected = '952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

assert sha(helper) == expected
originals = {}

def copy_file(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    value = sha(source)
    assert value == sha(dest)
    originals[str(source)] = value

def copy_tree(source, dest):
    for path in sorted(source.rglob('*')):
        if path.is_file():
            copy_file(path, dest / path.relative_to(source))

copy_tree(HERE, STAGE / 'validation')
copy_file(helper, STAGE / 'archive-helper.py')
for suffix in ['double-extension-path-source', 'double-extension-path-green-source',
               'double-extension-path-build-v2', 'double-extension-path-green-build-v2']:
    copy_tree(Path('/workspace/.cloud-setup') / suffix, STAGE / suffix)
base = Path('/workspace/.cloud-setup/forge-clock-contract-release')
for name in ['forge', 'libforge_core.a', 'CMakeCache.txt', 'compile_commands.json',
             'CMakeFiles/forge.dir/src/uci.cpp.o', 'CMakeFiles/forge.dir/link.txt']:
    copy_file(base / name, STAGE / 'frozen-baseline' / name)
(STAGE / 'ORIGINALS-SHA256.json').write_text(json.dumps(originals, indent=2) + '\n')
spec = importlib.util.spec_from_file_location('trusted_archive', helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
manifest_path = module.archive_results(STAGE, OUT, 'double-extension-actual-red-green-cecf0b9')
manifest = module.verify_archive(manifest_path)
for name, value in originals.items():
    assert sha(name) == value, name
receipt = {'status': 'PASS', 'manifest': manifest_path.name,
           'manifest_sha256': sha(manifest_path), 'archive': manifest['archive'],
           'parts': manifest['parts'], 'payload_files': len(manifest['files']),
           'payload_bytes': sum(row['size'] for row in manifest['files']),
           'originals_rehashed_after_archive': len(originals),
           'all_originals_unchanged': True, 'helper_sha256': expected,
           'scope': 'Complete actual RED and isolated unapplied GREEN source/build/core/exe/logs, frozen baseline object provenance, all failed auditor attempts.'}
(OUT / 'VERIFY-RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
