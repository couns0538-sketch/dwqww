#!/usr/bin/env python3
"""Assemble closed S04 evidence only; --seal requires the final native review."""
from pathlib import Path
import argparse
import base64
import datetime
import gzip
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess

W = Path(__file__).resolve().parent
R = Path('/workspace/dwqww')
V = R / 'validation/forge_sol_pack31_20261025'
OLD = R / 'releases/forge_sol_pack31_20261025/S04'
PATCH = W / 'forge_sol_S04_patchwork_retry_v2_20261025/forge_sol_S04_v2_20261025.patch'
TEST = W / 'forge_sol_S04_current_Lp_source_v2_20261025/tests/forge_sol_S04_tsan_test_20261025.cpp'
CURRENT_TESTS = W / 'forge_sol_S04_current_Lp_source_v2_20261025/tests/tests.cpp'
PATCH_SHA = 'b425157e6e9521a544e3612f3c32c3955bb1fd3195735692975d5a6d6d89590b'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def copy(source, out, name=None):
    path = out / (name or source.name)
    path.write_bytes(source.read_bytes())
    return path


def command(argv, cwd=None):
    p = subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True)
    return {'argv': [str(x) for x in argv], 'cwd': str(cwd) if cwd else None,
            'exit': p.returncode, 'stdout': {'base64': base64.b64encode(p.stdout).decode(),
              'bytes': len(p.stdout), 'sha256': sha(p.stdout)},
            'stderr': {'base64': base64.b64encode(p.stderr).decode(),
              'bytes': len(p.stderr), 'sha256': sha(p.stderr)}}


def collect():
    records = {}
    def add(path, name):
        if path.is_symlink() or not path.is_file():
            raise ValueError('Not a regular frozen evidence file: ' + str(path))
        raw = path.read_bytes()
        row = {'relative_path': name, 'original_path': str(path), 'bytes': len(raw),
               'sha256': sha(raw), 'base64': base64.b64encode(raw).decode()}
        if name in records:
            raise ValueError('duplicate record: ' + name)
        records[name] = row
    for path in sorted(OLD.iterdir()):
        if path.is_file():
            add(path, 'S04_v1/' + path.name)
    for path in sorted(W.iterdir()):
        if not path.is_file() or not path.name.startswith('forge_sol_S04_'):
            continue
        if any(token in path.name for token in ('delivery_', 'raw_restore')):
            continue
        if path.suffix in ('.json', '.jsonl', '.py', '.txt', '.stdout', '.stderr', '.gz'):
            add(path, 'S04_v2/' + path.name)
    for folder in sorted(W.glob('forge_sol_S04_*_native*_v2_20261025')):
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.suffix in ('.json', '.cmake'):
                add(path, 'S04_v2/' + folder.name + '/' + path.name)
        last = folder / 'build/Testing/Temporary/LastTest.log'
        if last.is_file():
            add(last, 'S04_v2/' + folder.name + '/LastTest.log')
    for folder in ['forge_sol_S04_source_checkpoint_v2_20261025',
                   'forge_sol_S04_patchwork_v2_20261025',
                   'forge_sol_S04_patchwork_retry_v2_20261025']:
        for path in sorted((W / folder).iterdir()):
            if path.is_file() and path.suffix in ('.json', '.py', '.txt', '.patch', '.md'):
                add(path, 'S04_v2/' + folder + '/' + path.name)
    for path in sorted(V.glob('forge_sol_S04_v2_*')):
        if path.is_file() and path.suffix in ('.json', '.py'):
            add(path, 'repository_validation/' + path.name)
    # Identity-bearing generation maps are metadata only: no local cache payloads.
    for generation in ['fourth', 'fifth', 'followup']:
        folder = W.parent / ('forge_sol_S00_' + generation + '_space_20261025')
        for path in sorted(folder.glob('*restore_map*.json')):
            add(path, 'cache_metadata/' + path.name)
    return [records[key] for key in sorted(records)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    matrix_path = W / 'forge_sol_S04_native_matrix_receipt_v2_20261025.json'
    matrix = json.loads(matrix_path.read_text())
    assert matrix['status'] == 'PASS_ALL_EIGHT_CURRENT_PROFILES' and matrix['completed_profiles'] == 8
    review_path = W / 'forge_sol_S04_v2_native_independent_review_20261025.json'
    review = json.loads(review_path.read_text())
    if args.seal:
        assert 'EIGHT' in review['status'] or 'ALL8' in review['status'] or len(review.get('closed_independently_reviewed_native_profiles', [])) == 8
        assert str(review['status']).startswith(('PASS', 'NO_MATERIAL'))
        assert not review.get('material_findings')
    out = W / ('forge_sol_S04_delivery_v2_20261025' if args.seal else 'forge_sol_S04_delivery_draft_v2_20261025')
    if out.exists():
        raise ValueError('Output exists: ' + str(out))
    out.mkdir()
    assert sha(PATCH.read_bytes()) == PATCH_SHA
    copy(PATCH, out)
    copy(TEST, out, 'forge_sol_S04_cold_tsan_v2_20261025.cpp')
    copy(Path(__file__), out)
    copy(W / 'forge_sol_S04_raw_restore_v2_20261025.py', out)
    copy(matrix_path, out, 'forge_sol_S04_native_matrix_v2_20261025.json')
    copy(review_path, out, 'forge_sol_S04_native_review_v2_20261025.json')
    for source, name in [
        (W / 'forge_sol_S04_patchwork_retry_v2_20261025/forge_sol_S04_patch_format_receipt_v2_20261025.json', 'forge_sol_S04_source_proof_v2_20261025.json'),
        (W / 'forge_sol_S04_v2_source_independent_review_20261025.json', 'forge_sol_S04_source_review_v2_20261025.json'),
        (W / 'forge_sol_S04_production_provenance_v2_20261025.json', 'forge_sol_S04_production_provenance_v2_20261025.json'),
        (W / 'forge_sol_S04_release_inheritance_receipt_v2_20261025.json', 'forge_sol_S04_release_inheritance_v2_20261025.json'),
        (W / 'forge_sol_S04_controller_scope_audit_v2_20261025.json', 'forge_sol_S04_scope_audit_v2_20261025.json'),
        (W / 'forge_sol_S04_base_RED_inheritance_v2_20261025.json', 'forge_sol_S04_base_RED_inheritance_v2_20261025.json'),
        (V / 'forge_sol_S04_v2_cache_generation_skill_proof_20261025.json', 'forge_sol_S04_cache_skill_proof_v2_20261025.json'),
        (V / 'forge_sol_S04_v2_target_name_skill_proof_20261025.json', 'forge_sol_S04_target_name_skill_proof_v2_20261025.json')]:
        copy(source, out, name)
    rows = collect()
    archive = out / 'forge_sol_S04_raw_evidence_v2_20261025.jsonl.gz'
    with archive.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0, compresslevel=6) as stream:
            for row in rows:
                stream.write((json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n').encode())
    entries = [{key: row[key] for key in ('relative_path', 'bytes', 'sha256')} for row in rows]
    index = {'schema': 'S04_original_bytes_base64_v2', 'archive': archive.name,
             'archive_sha256': sha(archive.read_bytes()), 'records': len(rows),
             'original_bytes': sum(row['bytes'] for row in rows), 'files': entries,
             'restore': 'python3 -B forge_sol_S04_raw_restore_v2_20261025.py --archive ' + archive.name + ' --index forge_sol_S04_evidence_index_v2_20261025.json --out NEW_EMPTY_PATH',
             'scope': 'Original closed source-proof, native/controller/failure/review, v1 inherited evidence, four fresh whole-disassembly gzip streams and local skill reference proofs. No engine/weight/object/source-tree/cache-payload export.'}
    index_path = out / 'forge_sol_S04_evidence_index_v2_20261025.json'
    index_path.write_text(json.dumps(index, indent=2) + '\n')
    # Actual complete decode/restore and original-file hash comparison.
    restored = W / ('forge_sol_S04_restore_final_v2_20261025' if args.seal else 'forge_sol_S04_restore_draft_v2_20261025')
    result = command(['python3', '-B', out / 'forge_sol_S04_raw_restore_v2_20261025.py',
                      '--archive', archive, '--index', index_path, '--out', restored])
    if result['exit'] != 0:
        raise ValueError('Restore failed: ' + json.dumps(result))
    assert all((restored / row['relative_path']).read_bytes() == Path(row['original_path']).read_bytes() for row in rows)
    rejected = command(['python3', '-B', out / 'forge_sol_S04_raw_restore_v2_20261025.py',
                        '--archive', archive, '--index', index_path, '--out', restored])
    assert rejected['exit'] != 0
    (out / 'forge_sol_S04_restore_verification_v2_20261025.json').write_text(json.dumps({
        'status': 'PASS_ALL_ORIGINAL_BYTES_RESTORED_AND_REHASHED', 'records': len(rows),
        'original_byte_comparisons': len(rows), 'new_directory_restore': result,
        'existing_directory_rejected': rejected, 'native_engine_executions': 0}, indent=2) + '\n')
    table = '\n'.join('|{base}|{profile}|{option}|{ctest_total}/{ctest_total}|`{engine_sha256}`|'.format(**row) for row in matrix['profiles'])
    totals = sum(row['ctest_total'] for row in matrix['profiles'])
    current_test_sha = sha(CURRENT_TESTS.read_bytes())
    net = W / 'forge_sol_S04_current_Lp_source_v2_20261025/src/nnue_weights.inc'
    net_sha = sha(net.read_bytes())
    diffstat = '\n'.join(['CMakeLists.txt | +25', 'IDEA_SOURCE.md | +11 (same paragraph at safe common title)',
                          'src/bitboard.cpp | +12', 'tests/forge_sol_S04_tsan_test_20261025.cpp | +62',
                          '4 files changed, 110 insertions(+), 0 deletions(-)']) + '\n'
    (out / 'forge_sol_S04_diffstat_v2_20261025.txt').write_text(diffstat)
    report = f'''# S04 v2 — patch format and current-tree qualification, 20261025

Status: optional correctness candidate, OFF by default. All eight current L-prime/B profiles pass, {totals}/{totals} CTest tests, exactly four KNOWN_FAILURE lines and zero PIN_MISMATCH/FAIL in each current CPP suite. Performance and Elo remain UNPROVEN. The accepted h256_e12 lock is unchanged. Publication is UNVERIFIED until root performs immutable HTTP/SHA/Git-byte readbacks.

The code base is `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the supplied h256_e12 network overlay SHA256 `{net_sha}`. The raw commit's own net differs. B additionally retains the supplied buffer fix SHA256 `9ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c`. Current merged test source SHA256 `{current_test_sha}` is calculated from the supplied file; no expected engine value or pin was edited here.

Patch `forge_sol_S04_v2_20261025.patch`, SHA256 `{PATCH_SHA}`, was produced by private `git diff --full-index -U5`. Four files, +110/-0. It includes the new test's explicit `new file mode 100644`. Actual original patch `29ee0866e90185a6a50f8389d8792399b890338c4e10f6457459652bbb6c15e7` Git checks fail on all L/L-prime/B with `error: dev/null: No such file or directory`; its GNU-F0 applications pass. The v2 Git checks and GNU-F0 dry/apply all pass. All nine applied C++/CMake/test file pairs exactly match v1. Only the unchanged additive IDEA paragraph moves to a safe shared title anchor; removing it recovers every original document byte on its own base. Existing notes remain intact. Dedicated cold-test source SHA256 `{sha(TEST.read_bytes())}`; patch target path is `tests/forge_sol_S04_tsan_test_20261025.cpp`.

`FORGE_ATTACKS_INIT_ONCE` stays OFF. ON uses the already validated std::call_once publication repair around the existing initialization writes. The original cold API race is reproduced when simultaneous first Board constructors arrive before tables exist. The shipped UCI executable constructs its first Board on the main thread, so this cold-constructor race is not reached by its normal startup flow. This patch adds no search, evaluation, NNUE arithmetic, public-layout, TT, move-order, runtime UCI option, counter or default-output change.

|Check|Status|Evidence scope|
|---|---|---|
|Git-check and GNU-F0, L/L-prime/B|PASS|Actual original RED/new GREEN and per-base resulting source hashes|
|20 production files per current base|PASS|Exact original candidate source/include identity; current merged CPP tests freshly compiled|
|Current Release/ASan OFF/ON full suites|PASS|Eight closed actual current CTests; {totals}/{totals}; KNOWN4, no PIN_MISMATCH/FAIL|
|First bare d11|PASS|Fresh invocation of each qualified main engine before other runtime checks; 308972|
|All five fixed Release references, OFF and ON|PASS inherited|Exact v1 main ELF + source/flags binding, original closed logs; not five new deep runs|
|Both Release perft5 totals, OFF and ON|PASS inherited|4865609 / 193690690 through the same exact main-identity binding|
|NNUE-scoped FMA0|PASS inherited|Original supplied checker result, same exact binary/source; no new checker claim|
|Four whole-executable FMA counts|PASS fresh|Actual objdump mnemonic count0 with all four original disassembly streams preserved|
|Four ON cold TSan CTest targets|PASS fresh|Each newly built from the three current real TUs; separate TSan link excludes ASan|
|Standalone 1000 cold TSan processes|PASS inherited|Exact historical probe/source/flags/raw1000 identity; not rerun|
|Original baseline cold TSan RED|PASS inherited|Actual exit66 race trace; exact current relevant source/test identity, header evidence separately bound|
|Native Windows/PC, speed, Elo|UNVERIFIED / UNPROVEN|No PC work, timed comparison or strength test in this revision|

## Current matrix and build scope

|Base|Profile|Option|CTest|Main ELF SHA256|
|---|---|---|---|---|
{table}

These are current merged CPP tests and current CMake registrations against explicitly qualified reused main engines, core archives and ordinary helpers. Each source closure, per-target flags, object-member/archive identity and complete LastTest log is in the evidence. Current tests are compiled fresh; the four ON dedicated cold TSan targets are built fresh. No fresh full-target engine rebuild is claimed. Flags retain C++20, H256 float, `-march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math`, Release O3 or ASan/UBSan O1/g1 with documented per-target scopes. Core's ON macro is PRIVATE; frontend/test flags are recorded separately. The standalone historical TSan probe is distinct from current generated CMake targets. Toolchain/system-header bytes were not directly frozen by the original RED capture; this limitation is retained.

The inherited fixed references are depths11/13/16/20/22 = 308972 / 745494 / 2460422 / 11901452 / 31111774. Kiwipete is `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`. Native stdout NPS fields are preserved raw and uninterpreted; historical advisory timing is retained separately without a speed verdict.

## Preserved failures and workflow maintenance

The original patch's Git-header defect, metadata producer's overly strict added-blank-line alignment assertion, first controller diagnostic parser error, incomplete archive-generation lookup, and guessed helper-target name are retained separately from successful retries. The latter lookup/name failures blocked observers, not engine or sanitizer correctness. L-prime ASan OFF resumed only pending gates after its first actual d11/current CPP checks had passed. Reports explicitly identify missing independently saved stderr in older pure-observer assertions; no reconstructed raw logs are presented as originals.

Existing repository-local `validating-chess-simd` guidance was improved for complete archive-generation inventories and deriving names from actual generated CTest/CMake registrations. Two before/after reference-command proofs, two probes and four raw control JSONs are bundled. Final local guide SHA256 `2b8b7c906853ae06dfb14f83b34f4b7f0472f96bc35cea2f175ea384a70d1f69`; the intermediate guide/proof is retained in root's7036d53 checkpoint, while the final additive paragraph is subject to root's separate publication verification. This is local reference validation, not a fresh-agent pressure test or cloud/global skill installation. No duplicate skill was created.

## Evidence and continuation

The flat archive's index lists each of {len(rows)} original records with path, byte length and SHA256. Original v1 evidence, all current closed commands/full streams, controller revisions/failures, original1000 cold records, source proofs, reviews and four fresh whole-disassembly gzip streams are reversible base64 records inside `forge_sol_S04_raw_evidence_v2_20261025.jsonl.gz`. No binary, object, network, source-tree, cache gzip payload, ZIP, license or agent-instruction export is included. Cache restore metadata refers to local-only retained payloads. Published v1 remains untouched.

Verify outer hashes from this folder, then verify or restore raw evidence:

```sh
sha256sum -c forge_sol_S04_SHA256SUMS_v2_20261025.txt
python3 -B forge_sol_S04_raw_restore_v2_20261025.py --archive forge_sol_S04_raw_evidence_v2_20261025.jsonl.gz --index forge_sol_S04_evidence_index_v2_20261025.json
python3 -B forge_sol_S04_raw_restore_v2_20261025.py --archive forge_sol_S04_raw_evidence_v2_20261025.jsonl.gz --index forge_sol_S04_evidence_index_v2_20261025.json --out NEW_OUTPUT_FOLDER
```

The builder actually restored and compared all {len(rows)} original file bytes; an existing output directory is rejected. All S04 native jobs and cache leases are closed. The final independent native/source review passed all eight profiles. Root performs the final report/checkpoint binding and publication plus per-file immutable download comparison, then S05 fix-ups in the user's saved order. No accepted lock switch or speed/Elo claim follows from this correctness qualification.
'''
    (out / 'forge_sol_S04_report_v2_20261025.md').write_text(report)
    (out / 'forge_sol_S04_continuation_v2_20261025.json').write_text(json.dumps({
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'READY_FINAL_REVIEW_AND_ROOT_PUBLICATION' if args.seal else 'DRAFT_UNSEALED',
        'baseline_code_commit': '1ab50b2dd64d9b2f752f7f1285f6968cad2fd792',
        'net_sha256': net_sha, 'patch_sha256': PATCH_SHA,
        'matrix_sha256': sha(matrix_path.read_bytes()), 'native_review_sha256': sha(review_path.read_bytes()),
        'records': len(rows), 'closed_native_profiles': 8, 'ctest_passed': totals,
        'default': 'OFF', 'native_jobs': 'CLOSED', 'accepted_lock_changed': False,
        'publication': 'UNVERIFIED root owns commit/push/immutable HTTP and Git-byte readback',
        'speed_and_Elo': 'UNPROVEN', 'next': 'Root immutable publication verification, then S05 fixups'}, indent=2) + '\n')
    # Every plain delivery byte is checked before creating the outer manifest.
    forbidden = bytes.fromhex('4f70656e4149')
    assert all(forbidden not in p.read_bytes() for p in out.iterdir() if p.suffix != '.gz')
    if args.seal:
        manifest = out / 'forge_sol_S04_SHA256SUMS_v2_20261025.txt'
        manifest.write_text(''.join(sha(p.read_bytes()) + '  ' + p.name + '\n' for p in sorted(out.iterdir())))
        check = command(['sha256sum', '-c', manifest.name], out)
        assert check['exit'] == 0
        (W / 'forge_sol_S04_delivery_seal_v2_20261025.json').write_text(json.dumps({
            'folder': str(out), 'files': len(list(out.iterdir())), 'manifest_sha256': sha(manifest.read_bytes()),
            'check': check, 'archive_sha256': index['archive_sha256'], 'original_records': len(rows)}, indent=2) + '\n')
    print(json.dumps({'out': str(out), 'sealed': args.seal, 'records': len(rows),
                      'archive_sha256': index['archive_sha256'], 'report_sha256': sha(report.encode())}))


if __name__ == '__main__':
    main()
