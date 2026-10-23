#!/usr/bin/env python3
"""Archive the closed, unused independent audit once; never evaluate payloads or nets."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import time
import zipfile

BASE = Path('/workspace/forge-nnue-handoff-20261023')
DEST = BASE / 'independent-audit128-recovery-attempt1'
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
    marker = BASE / 'INDEPENDENT-AUDIT-TOOL-CLOSED.json'
    closure = json.loads(marker.read_text())
    if (closure['status'] != 'PASS_INDEPENDENT_AUDIT_DATA_ACTUAL_TOOL_CLOSED_UNUSED_UNEVALUATED'
            or closure['actual_tool_session_id'] != 33309 or closure['actual_tool_exit_code'] != 0
            or closure['loss_computations'] != 0 or closure['audit_training_performed']):
        raise ValueError('The actual closed unused independent audit is required')
    full = Path(closure['masked_manifest_path']).parent
    if sha256(full / 'manifest.json') != closure['masked_manifest_sha256']:
        raise ValueError('Closed masked audit manifest changed')
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

    for name in ('independent-audit-frozen-sources-attempt1',
                 'independent-audit-generated128-attempt1',
                 'independent-audit-controller-attempt1',
                 'independent-audit-controller-attempt2',
                 'independent-audit-prepared-original-attempt1',
                 'independent-audit-prepared-masked-attempt1',
                 'independent-audit-native-hce-raw-attempt1'):
        add_tree(BASE / name, name)
    for name in ('INDEPENDENT-AUDIT-PROTOCOL.json', 'INDEPENDENT-AUDIT-CLOSED.json',
                 'INDEPENDENT-AUDIT-TOOL-CLOSED.json', 'FULL-PREP-CLOSED.json',
                 'FULL-PREP-CLOSED-v2.json', 'FULL-PREP-TOOL-RESULT.json',
                 'FULL-PREP-INTEGRITY-v2.json', 'full-prep-integrity.command.json',
                 'full-prep-integrity.result.json', 'full-prep-integrity.stdout',
                 'full-prep-integrity.stderr', 'full-prep-integrity-v2.command.json',
                 'full-prep-integrity-v2.result.json', 'full-prep-integrity-v2.stdout',
                 'full-prep-integrity-v2.stderr', 'close_full_preparation.py',
                 'close_full_preparation_v2.py'):
        if not (BASE / name).is_file():
            raise ValueError('Missing audit closure dependency: ' + name)
        add_file(BASE / name, 'closure-evidence/' + name)
    for name in ('generate_residual_data.py', 'prepare_residual_data.py', 'forge_selfplay.py',
                 'residual_train.py', 'train_nnue.py', 'include_parser.py', 'engine_contract.json',
                 'compare_holdout.py', 'engine_probe.cpp'):
        add_file(REPO / 'tools/nnue' / name, 'pipeline-source-reference/' + name)
    add_file(CLOUD / 'nnue-pipeline-20261023-baseline-build/forge', 'actual-native/forge-linux-source1ab50b2d')
    add_file(REPO / 'src/nnue_weights.inc', 'actual-native/shipped-weights-41487f32.inc')
    generation = json.loads((BASE / 'independent-audit-generated128-attempt1/manifest.json').read_text())
    for index, (path, expected_sha) in enumerate(sorted(generation['build_files'].items())):
        if sha256(Path(path)) != expected_sha:
            raise ValueError('Original executed native build metadata changed')
        add_file(Path(path), 'actual-native/build-metadata/' + str(index).zfill(2) + '-' + Path(path).name)
    main_data = BASE / 'prepared-all13m-reservoir-attempt1'
    add_file(main_data / 'manifest.json', 'main-data-dependency/manifest.json')
    main_manifest = json.loads((main_data / 'manifest.json').read_text())
    dependency = {
        'status': 'EXTERNAL_MAIN_ARCHIVE_PENDING_AT_AUDIT_ARCHIVE_BUILD_TIME',
        'main_manifest_path': str(main_data / 'manifest.json'),
        'main_manifest_sha256': sha256(main_data / 'manifest.json'),
        'required_main_recipe_bindings': main_manifest['artifacts'],
        'recovery_directory': str(BASE / 'full-prepared-data-recovery-attempt1'),
        'archive_manifest': 'full-prepared-data-recovery-attempt1/ARCHIVE-MANIFEST.json',
        'archive_name': 'forge-nnue-full-prepared-20261023.zip',
        'parts': 'forge-nnue-full-prepared-20261023.zip.001 onward in declared manifest order',
        'verification_requirement': 'Require independent main ARCHIVE-MANIFEST PASS_ARCHIVE_READBACK and its exact part/member hashes; audit packaging does not certify an unfinished external archive.',
        'raw_legacy_inputs_included': False,
        'main_1m_arrays_recipes_3038_native_receipts_duplicated_in_audit_archive': False,
    }
    write_new(DEST / 'MAIN-DATA-RECOVERY-REFERENCE.json', dependency)
    add_file(DEST / 'MAIN-DATA-RECOVERY-REFERENCE.json', 'main-data-dependency/MAIN-DATA-RECOVERY-REFERENCE.json')
    add_file(Path(__file__), 'archive_independent_audit.py')

    readme = "# Forge NNUE independent audit128 recovery checkpoint\n\nThis is a CLOSED, UNUSED, UNEVALUATED independent audit. No model forwards, NNUE outputs, model losses, training, tuning, candidate selection or Elo inference occurred. Root must freeze exactly one final full-data candidate solely from the original4,149-position validation before evaluating this separate audit once. All arrays named train are UNUSED and must remain unused.\n\nThe audit was preregistered before generation. Seed20271023 for both generation and game-hash split has a possible ten-attempt opening-seed range disjoint from the original256-game run. Actual original engine02d6ba26/source1ab50b2d/shipped network41487f32 generated128 completed games with2 workers, Threads1, Hash16, OwnBookfalse,5000nodes. Both owned native engines closed cleanly; the complete original raw UCI logs, generatedJSONL and exact executed generator902b1c70/helpers are included.\n\nOriginal fresh preparation contains8,899 validation positions and1,321 UNUSED train positions. There are111 declared validation partition gameIDs, but109 games have represented eligible rows. Do not infer111 represented games. The separate raw HCE-only replay verified all10,220 original prepared positions against the actual frozen native probe d2f400df, retaining every original stdin/stdout/stderr and process receipt. HCE integer scores and unordered active perspective feature sets match exactly; no NNUE inference was requested.\n\nThe first audit finalizer (actual session86162) correctly stopped on the original FAILED main closure marker before masking. The main data job itself had actually exited0; its checker incorrectly demanded retained rows from all200 assigned training games.196 retained games and4 valid zero-row games are documented. Root explicitly authorized a separately preserved v2 closure gate and second audit controller; neither data generation nor training was repeated. All original failures, source versions, tests, logs, protocols and corrected success receipts remain present.\n\nThe first actual mask execution (controller33309 exit0) removed18 audit validation rows whose first-four-FEN key occurred in authenticated1M main training or original4,149 validation recipes. The masked audit contains8,881 rows from109 represented games (111 declared partition IDs). Every array and provenance row is an exact ordered subset of original data. The1,321 UNUSED train arrays are byte-identical copies.128 authentic audit gameIDs are disjoint from the canonical256 original gameIDs. Legacy identities in main training remain explicitly unknown; none were invented. Masked manifest SHA:d7a9a4e01cfcbc1c0bd25ec0aec9d38cf8786ce4309dba9b4d6bef6e659c7c74.\n\nThe main1M arrays, full train/validation recipes and3,038 native receipts are not duplicated. Recover them from full-prepared-data-recovery-attempt1/ using its authoritative ARCHIVE-MANIFEST.json, README and forge-nnue-full-prepared-20261023.zip.001 onward. That separate archive was still packaging at this audit build time: require its own verified PASS_ARCHIVE_READBACK and actual tool closure; do not treat this reference as a success claim. The included main manifest and MAIN-DATA-RECOVERY-REFERENCE.json bind exact recipe SHAs/counts for independent overlap inspection. Raw888MB legacy inputs are excluded; their separate recovery reference is in the main archive.\n\nARCHIVE-MANIFEST.json binds every member (including CONTENT-MANIFEST.json) by path, bytes, mode and SHA. CONTENT-MANIFEST lists source payload mappings without its own self-hash; the external full manifest closes that relation. Packaging reassembles its actual31MiB-or-smaller parts and verifies every member/CRC/path/mode/hash plus unchanged original source bytes. All sources are preserved; no recovered code is executed during readback. Historical provenance uses original absolute paths: explicitly remap them when replaying elsewhere. The archived native binary is Linux, not a Windows engine build.\n\nRecover on Linux or Windows with the following standard-library code after authenticating ARCHIVE-MANIFEST.json against the published Git SHA:\n\n```python\nimport hashlib, json, os, pathlib, stat, zipfile\nroot = pathlib.Path('.')\nm = json.loads((root / 'ARCHIVE-MANIFEST.json').read_text())\ndef digest(path):\n    h = hashlib.sha256()\n    with path.open('rb') as f:\n        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)\n    return h.hexdigest()\narchive = root / 'recovered.zip'\nwith archive.open('xb') as out:\n    for part in m['parts']:\n        p = root / part['name']\n        assert p.stat().st_size == part['bytes'] and digest(p) == part['sha256']\n        with p.open('rb') as f:\n            for b in iter(lambda: f.read(1024*1024), b''): out.write(b)\nassert archive.stat().st_size == m['archive']['bytes'] and digest(archive) == m['archive']['sha256']\nexpected = {v['path']: v for v in m['members']}\nwith zipfile.ZipFile(archive) as z:\n    assert len(z.infolist()) == len(expected) and set(z.namelist()) == set(expected)\n    for info in z.infolist():\n        name = pathlib.PurePosixPath(info.filename)\n        assert not name.is_absolute() and '..' not in name.parts and '\\\\\\\\' not in info.filename\n        assert not stat.S_ISLNK(info.external_attr >> 16)\n        rec = expected[info.filename]\n        h = hashlib.sha256(); size = 0\n        with z.open(info) as f:\n            for b in iter(lambda: f.read(1024*1024), b''): h.update(b); size += len(b)\n        assert size == rec['bytes'] and h.hexdigest() == rec['sha256']\n        assert stat.S_IMODE(info.external_attr >> 16) == rec['mode']\n    target = root / 'restored-checkpoint'\n    target.mkdir()  # Fails rather than overwriting an existing directory.\n    z.extractall(target)\n    if os.name != 'nt':\n        for name, rec in expected.items(): (target / name).chmod(rec['mode'])\n```\n\nUse a NEW extraction directory. This archive preserves evidence and data only; it is not a promoted network or an Elo result.\n"
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

    archive = DEST / 'forge-nnue-independent-audit128-20261023.zip'
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
        'actual_audit_tool_session_id': 33309, 'actual_audit_tool_exit_code': 0,
        'audit_closed_marker_sha256': sha256(marker), 'masked_audit_manifest_sha256': closure['masked_manifest_sha256'],
        'audit_successful_native_derived_streams_retained': True,
        'audit_uci_raw_streams_retained': True, 'audit_validation_rows': 8881,
        'audit_validation_games_represented': 109, 'audit_validation_partition_game_ids': 111,
        'all_audit_train_arrays_unused': True, 'audit_loss_computations': 0,
        'legacy_raw_inputs_duplicated': False,
        'main_data_recovery': 'full-prepared-data-recovery-attempt1/ARCHIVE-MANIFEST.json and numbered parts; verify independent actual closure',
        'main_1m_data_and_recipes_duplicated': False,
        'scope': 'Independent unused audit data/source/evidence checkpoint; no model forwards, losses, training, selection or Elo conclusions',
    }
    write_new(DEST / 'ARCHIVE-MANIFEST.json', result)
    print(json.dumps({'status': result['status'], 'archive': archive_record, 'parts': parts,
                      'members': len(members), 'expanded_bytes': result['expanded_bytes'],
                      'manifest_path': str(DEST / 'ARCHIVE-MANIFEST.json'),
                      'manifest_sha256': sha256(DEST / 'ARCHIVE-MANIFEST.json')}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
