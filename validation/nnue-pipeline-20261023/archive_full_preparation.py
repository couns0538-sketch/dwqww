#!/usr/bin/env python3
"""Archive the closed, unchanged main dataset once; never execute payload content."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import time
import zipfile

BASE = Path('/workspace/forge-nnue-handoff-20261023')
DEST = BASE / 'full-prepared-data-recovery-attempt1'
CLOUD = Path('/workspace/.cloud-setup')
REPO = Path('/workspace/dwqww')
PART_BYTES = 31 * 1024 * 1024
CHUNK = 1024 * 1024


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(CHUNK), b''):
            h.update(b)
    return h.hexdigest()


def safe_name(name):
    p = PurePosixPath(name)
    if not name or '\\' in name or p.is_absolute() or any(x in ('', '.', '..') for x in p.parts):
        raise ValueError('Unsafe archive member: ' + repr(name))
    return name


def write_new(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def main():
    os.nice(10)  # Single-process, single-thread ZIP work yields to the main training run.
    started = time.monotonic()
    DEST.mkdir()
    marker = BASE / 'FULL-PREP-CLOSED-v2.json'
    closure = json.loads(marker.read_text())
    if closure['status'] != 'PASS_PREPARED_DATA_CLOSED' or closure['actual_tool_exit_code'] != 0:
        raise ValueError('The explicitly closed original dataset is required')
    full = Path(closure['manifest_path']).parent
    if sha256(full / 'manifest.json') != closure['manifest_sha256']:
        raise ValueError('Closed prepared manifest changed')
    origins = {}

    def add_file(source, name):
        if source.is_symlink():
            raise ValueError('Symlink source rejected: ' + str(source))
        source = source.resolve(strict=True)
        name = safe_name(name)
        if name in origins:
            raise ValueError('Duplicate member: ' + name)
        if not stat.S_ISREG(source.stat().st_mode):
            raise ValueError('Nonregular source: ' + str(source))
        origins[name] = source

    def add_tree(source, prefix):
        if source.is_symlink():
            raise ValueError('Symlink root rejected: ' + str(source))
        for p in sorted(source.rglob('*')):
            if p.is_symlink():
                raise ValueError('Symlink rejected: ' + str(p))
            if p.is_file():
                add_file(p, prefix + '/' + p.relative_to(source).as_posix())
            elif not p.is_dir():
                raise ValueError('Nonregular input rejected: ' + str(p))

    add_tree(full, 'prepared-all13m-reservoir-attempt1')
    add_tree(BASE / 'prepared-fresh-only-attempt1', 'prepared-fresh-only-attempt1')
    add_tree(BASE / 'generated-games-256-attempt1', 'generated-games-256-attempt1')
    add_tree(BASE / 'generated-games-smoke-2-attempt1', 'generated-games-smoke-2-attempt1')
    for name in ('nnue-pipeline-20261023-preparer-frozen-v1', 'nnue-pipeline-20261023-generator-frozen-v1'):
        add_tree(CLOUD / name, 'frozen-tools/' + name)
    add_file(CLOUD / 'nnue-pipeline-20261023-baseline-build/forge', 'frozen-tools/actual-generation-baseline-forge-linux')
    for p in sorted(BASE.iterdir()):
        if p.is_file() and (p.name.startswith(('data-', 'DATA-', 'FULL-PREP-', 'full-prep-', 'close_full_preparation'))
                            or p.name == 'LEGACY-LABEL-PLAUSIBILITY.json'):
            add_file(p, 'evidence/' + p.name)
    for p in sorted((BASE / 'selfplay-input').iterdir()):
        if p.is_file() and (p.suffix.lower() in ('.json', '.md', '.py', '.stdout', '.stderr')
                            or p.name == 'INSPECTION-SHA256SUMS'):
            add_file(p, 'legacy-input-inspection/' + p.name)
    original_parts = REPO / 'validation/nnue-pipeline-20261023/original-selfplay-parts'
    for name in ('README.md', 'MANIFEST.json'):
        add_file(original_parts / name, 'original-selfplay-parts-reference/' + name)
    for name in ('generate_residual_data.py', 'prepare_residual_data.py', 'forge_selfplay.py', 'residual_train.py'):
        add_file(REPO / 'tools/nnue' / name, 'reviewed-current-tools/' + name)
    add_file(REPO / 'tools/nnue/tests/test_residual_data.py', 'reviewed-current-tools/tests/test_residual_data.py')
    add_file(Path(__file__), 'archive_full_preparation.py')

    readme = '''# Forge NNUE full prepared-data recovery checkpoint

This checkpoint contains the original successful full preparation, its authentic generated games and UCI traces, the unchanged fresh-only reference dataset, actual frozen preparer/probe and generator-v1 source, reviewed current data tools, and all original data-workflow logs. The original false closure assertion and its FAILED marker are preserved; FULL-PREP-CLOSED-v2.json is the corrected successful gate. No engine strength or Elo improvement is asserted.

The main data manifest SHA-256 is 0bce5a466e51449dace54bd65f38a0ff2c79a7e0755a963096fa97fb1ea39216. It binds 1,000,000 training positions (14,895 fresh, 985,105 legacy) and the unchanged 4,149 held-out positions from 56 represented validation games. There are 200 assigned training-game IDs, of which 196 have retained rows; the four zero-retained games and exact reasons are recorded in integrity-v2. Legacy game IDs and original teacher source identity are unknown and never invented. Legacy records are training only; exact first-four-FEN validation keys were excluded from every training source.

All nine legacy inputs were fully examined (13,500,000 rows). The declared seed-20261023 Algorithm R reservoir sampled eligible unique legacy positions across all nine files, rather than a prefix. Native HCE/features came from the actual Forge C++ probe. All 3,038 successful native batch receipts are retained, but their full derived stdin/stdout streams were deliberately not stored; receipts bind byte counts and stream hashes. Original input text, source-line recipes, native probe and the build/source identities permit replay. Failure paths retained original streams. This is an evidence limitation, not a claim that successful native streams are present.

The 888 MB legacy text and original uploaded archive bytes are not duplicated here. Recover the original six parts from couns0538-sketch/dwqww at validation/nnue-pipeline-20261023/original-selfplay-parts, following the included reference MANIFEST/README and legacy-input-inspection hashes. Combined original 7z SHA-256: 3900947d2555b3fce43132f8b4b4cbe2e0bb85ee07df18118f138fde674ec6f4. The genuine 256-game generation used archived frozen generator-v1; newer reviewed failure-only guards were added after that run and are not relabeled as the executed generator.

Recovery uses Python's standard library on Linux or Windows. Download ARCHIVE-MANIFEST.json and every numbered .zip.00N part into one new directory. Authenticate the manifest against the Git-published SHA first. Concatenate parts in its declared order; verify every part's bytes/SHA and the reconstructed archive's bytes/SHA. The code below verifies all member bytes, CRCs, paths and permission bits before extracting into a NEW directory. It does not execute any recovered code. Paths inside historical provenance are original absolute workspace paths; retain them as evidence and explicitly remap paths when replaying on a different machine. The archived Linux executable is not a Windows engine build.

```python
import hashlib, json, os, pathlib, stat, zipfile
root = pathlib.Path('.')
m = json.loads((root / 'ARCHIVE-MANIFEST.json').read_text())
def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
archive = root / 'recovered.zip'
with archive.open('xb') as out:
    for part in m['parts']:
        p = root / part['name']
        assert p.stat().st_size == part['bytes'] and digest(p) == part['sha256']
        with p.open('rb') as f:
            for b in iter(lambda: f.read(1024*1024), b''): out.write(b)
assert archive.stat().st_size == m['archive']['bytes'] and digest(archive) == m['archive']['sha256']
expected = {v['path']: v for v in m['members']}
with zipfile.ZipFile(archive) as z:
    assert len(z.infolist()) == len(expected) and set(z.namelist()) == set(expected)
    for info in z.infolist():
        name = pathlib.PurePosixPath(info.filename)
        assert not name.is_absolute() and '..' not in name.parts and '\\\\' not in info.filename
        assert not stat.S_ISLNK(info.external_attr >> 16)
        rec = expected[info.filename]
        h = hashlib.sha256(); size = 0
        with z.open(info) as f:
            for b in iter(lambda: f.read(1024*1024), b''): h.update(b); size += len(b)
        assert size == rec['bytes'] and h.hexdigest() == rec['sha256']
        assert stat.S_IMODE(info.external_attr >> 16) == rec['mode']
    target = root / 'restored-checkpoint'
    target.mkdir()  # Fails rather than overwriting an existing directory.
    z.extractall(target)
    if os.name != 'nt':
        for name, rec in expected.items(): (target / name).chmod(rec['mode'])
```

NPZ arrays have exactly features:int16[N,2,32] with -1 padding, hce:int32[N], score:int32[N], result_stm:float32[N]. Scores/HCE/results use side-to-move POV. The retained accepted residual architecture is unchanged (768→128×2 SCReLU). Use the shared strict residual_train.load_prepared_data validator after restoring/remapping declared source paths. Source and network remain in Git; this archive is a data/evidence checkpoint, not a promoted network.
'''
    (DEST / 'README.md').write_text(readme)
    add_file(DEST / 'README.md', 'README.md')

    def describe(name, source):
        facts = source.stat()
        return {'path': name, 'origin_path': str(source), 'bytes': facts.st_size,
                'mode': stat.S_IMODE(facts.st_mode), 'sha256': sha256(source)}

    inventory = [describe(name, source) for name, source in sorted(origins.items())]
    write_new(DEST / 'CONTENT-MANIFEST.json', {'schema_version': 1, 'files': inventory,
              'scope': 'Payload list excludes this manifest itself; external ARCHIVE-MANIFEST binds every ZIP member including it.'})
    add_file(DEST / 'CONTENT-MANIFEST.json', 'CONTENT-MANIFEST.json')
    members = [describe(name, source) for name, source in sorted(origins.items())]
    write_new(DEST / 'SOURCE-SNAPSHOT.json', {'members': members, 'utc': datetime.now(timezone.utc).isoformat()})

    archive = DEST / 'forge-nnue-full-prepared-20261023.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for name, source in sorted(origins.items()):
            z.write(source, arcname=name)
    archive_record = {'name': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha256(archive),
                      'compression': 'ZIP_DEFLATED', 'compresslevel': 6}
    parts = []
    with archive.open('rb') as source:
        index = 1
        while True:
            first = source.read(CHUNK)
            if not first:
                break
            part = DEST / (archive.name + '.' + str(index).zfill(3))
            digest, count = hashlib.sha256(), 0
            with part.open('xb') as out:
                chunk = first
                while chunk:
                    out.write(chunk); digest.update(chunk); count += len(chunk)
                    if count == PART_BYTES:
                        break
                    chunk = source.read(min(CHUNK, PART_BYTES - count))
            parts.append({'name': part.name, 'bytes': count, 'sha256': digest.hexdigest()})
            index += 1

    reassembled = DEST / 'READBACK-reassembled.zip'
    with reassembled.open('xb') as out:
        for part in parts:
            source = DEST / part['name']
            if source.stat().st_size != part['bytes'] or sha256(source) != part['sha256']:
                raise ValueError('Actual split-part readback differs')
            with source.open('rb') as f:
                for chunk in iter(lambda: f.read(CHUNK), b''):
                    out.write(chunk)
    if reassembled.stat().st_size != archive_record['bytes'] or sha256(reassembled) != archive_record['sha256']:
        raise ValueError('Actual reassembled archive differs')
    expected = {item['path']: item for item in members}
    with zipfile.ZipFile(reassembled) as z:
        if len(z.infolist()) != len(expected) or set(z.namelist()) != set(expected):
            raise ValueError('Readback member paths/count differ')
        for info in z.infolist():
            safe_name(info.filename)
            item = expected[info.filename]
            if not stat.S_ISREG(info.external_attr >> 16) or stat.S_IMODE(info.external_attr >> 16) != item['mode']:
                raise ValueError('Readback file type/mode differs: ' + info.filename)
            digest, size = hashlib.sha256(), 0
            with z.open(info) as f:
                for chunk in iter(lambda: f.read(CHUNK), b''):
                    digest.update(chunk); size += len(chunk)
            if size != item['bytes'] or digest.hexdigest() != item['sha256']:
                raise ValueError('Readback member bytes differ: ' + info.filename)
    for item in members:
        source = Path(item['origin_path'])
        if source.stat().st_size != item['bytes'] or stat.S_IMODE(source.stat().st_mode) != item['mode'] or sha256(source) != item['sha256']:
            raise ValueError('Original source changed during archiving: ' + str(source))
    result = {
        'schema_version': 1, 'status': 'PASS_ARCHIVE_READBACK', 'utc': datetime.now(timezone.utc).isoformat(),
        'elapsed_seconds': time.monotonic() - started, 'archive': archive_record, 'parts': parts,
        'part_max_bytes': PART_BYTES, 'members': members, 'member_count': len(members),
        'expanded_bytes': sum(item['bytes'] for item in members),
        'all_member_sha256_size_modes_verified_from_part_reassembly': True,
        'original_source_bytes_and_modes_rechecked_unchanged': True,
        'main_closed_marker_sha256': sha256(marker), 'main_manifest_sha256': closure['manifest_sha256'],
        'successful_native_derived_streams_retained': False,
        'legacy_raw_inputs_duplicated': False,
        'legacy_raw_input_recovery': 'Git validation/nnue-pipeline-20261023/original-selfplay-parts and included reference manifests',
        'scope': 'Data/source/evidence checkpoint; no training or Elo conclusions',
    }
    write_new(DEST / 'ARCHIVE-MANIFEST.json', result)
    print(json.dumps({'status': result['status'], 'archive': archive_record, 'parts': parts,
                      'members': len(members), 'expanded_bytes': result['expanded_bytes'],
                      'manifest_path': str(DEST / 'ARCHIVE-MANIFEST.json'),
                      'manifest_sha256': sha256(DEST / 'ARCHIVE-MANIFEST.json')}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
