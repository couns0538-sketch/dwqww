#!/usr/bin/env python3
"""Package closed S25 qualification and the exact inherited negative evidence."""
from pathlib import Path
import argparse, base64, datetime, gzip, hashlib, json, subprocess

W = Path(__file__).resolve().parent
R = Path('/workspace/dwqww')
V = R / 'validation/forge_sol_pack31_20261025'
SOURCE = W / 'forge_sol_S25_source_checkpoint_v2_20261025'
PATCH = SOURCE / 'forge_sol_S25_outcontract_v2_20261025.patch'
PSHA = '32bc590c23f05944fe112bc6691578e9e041a26d5268bbb4b70f6963b3214d49'
FILES = ['forge_sol_S25_outcontract_20261025.py', 'forge_sol_S25_options_20261025.json', 'forge_sol_S25_parser_tests_20261025.py']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(argv, cwd=None):
    p = subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True)
    row = {'argv': [str(x) for x in argv], 'cwd': str(cwd) if cwd else None, 'exit': p.returncode}
    for key, data in [('stdout', p.stdout), ('stderr', p.stderr)]:
        row[key] = {'base64': base64.b64encode(data).decode(), 'bytes': len(data), 'sha256': sha(data)}
    return row


def collect():
    rows = {}
    def add(path, name):
        if not path.is_file() or path.is_symlink():
            raise ValueError('Expected frozen regular evidence: ' + str(path))
        raw = path.read_bytes()
        if name in rows:
            raise ValueError('duplicate record: ' + name)
        rows[name] = {'relative_path': name, 'original_path': str(path), 'bytes': len(raw),
                      'sha256': sha(raw), 'base64': base64.b64encode(raw).decode()}
    for path in sorted(W.iterdir()):
        if path.is_file() and path.name.startswith('forge_sol_S25_') and path.suffix in ('.json', '.py', '.txt', '.stdout', '.stderr'):
            if not any(token in path.name for token in ('delivery_', 'raw_restore')):
                add(path, 'S25_v2/' + path.name)
    for folder in sorted(W.iterdir()):
        if not folder.is_dir() or folder.name.startswith(('forge_sol_S25_current_', 'forge_sol_S25_delivery_', 'forge_sol_S25_restore_')):
            continue
        if folder == SOURCE:
            for path in sorted(folder.iterdir()):
                if path.is_file():
                    add(path, 'S25_v2/source_checkpoint/' + path.name)
        elif '_native_' in folder.name:
            for path in sorted(folder.iterdir()):
                if path.is_file() and path.suffix in ('.json', '.cmake'):
                    add(path, 'S25_v2/' + folder.name + '/' + path.name)
            last = folder / 'build/Testing/Temporary/LastTest.log'
            if last.is_file():
                add(last, 'S25_v2/' + folder.name + '/LastTest.log')
            # Native checker children persist their exact stdin/streams/results.
            for path in sorted((folder / 'build').rglob('forge_sol_S25_*raw*.json')):
                add(path, 'S25_v2/' + str(path.relative_to(W)))
            for path in sorted((folder / 'build').rglob('forge_sol_S25_contract_result_20261025.json')):
                add(path, 'S25_v2/' + str(path.relative_to(W)))
        elif 'patchwork' in folder.name:
            for path in folder.glob('*.json'):
                add(path, 'S25_v2/' + folder.name + '/' + path.name)
    audit = W.parent / 'S25_v2_audit'
    for path in sorted(audit.glob('*.json')):
        add(path, 'resume_audit/' + path.name)
    selected = json.loads((W / 'forge_sol_S25_inherited_evidence_selection_v2_20261025.json').read_text())
    old_container = Path(selected['old_raw_schema']['path'])
    assert sha(old_container.read_bytes()) == selected['old_raw_schema']['sha256']
    old_records = {row['relative_path']: row for row in json.loads(old_container.read_text())['files']}
    for row in selected['required_small_original_metadata']:
        path = Path(row['path']); assert sha(path.read_bytes()) == row['sha256']
        add(path, 'inherited_negative/' + path.name)
    for row in selected['required_original_raw_records']:
        path = Path(row['local_path']); data = path.read_bytes()
        original = base64.b64decode(old_records[row['record_key']]['data_base64'], validate=True)
        assert data == original and sha(data) == row['sha256']
        add(path, 'inherited_negative/' + row['record_key'])
    for row in selected['baseline_inheritance_replacement']:
        path = Path(row['path']); assert sha(path.read_bytes()) == row['sha256']
        add(path, 'inherited_baseline/' + path.name)
    # Small source/native authority, not the prior complete source or raw corpus.
    for name in ['forge_sol_S05_native_matrix_receipt_v2_20261025.json', 'forge_sol_S05_frozen_overlay_cache_binding_v2_20261025.json']:
        path = W.parent / 'S05_v2' / name
        add(path, 'qualified_S05/' + name)
    return [rows[name] for name in sorted(rows)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seal', action='store_true')
    args = ap.parse_args()
    mp = W / 'forge_sol_S25_native_matrix_receipt_v2_20261025.json'
    matrix = json.loads(mp.read_text())
    assert matrix['status'] == 'PASS_ALL_FOUR_CURRENT_PROFILES' and matrix['completed_profiles'] == 4
    rp = W / 'forge_sol_S25_native_independent_review_v2_20261025.json'
    review = json.loads(rp.read_text())
    if args.seal:
        assert str(review['status']).startswith(('PASS', 'NO_MATERIAL'))
        assert not review.get('findings') and not review.get('material_findings') and not review.get('blockers')
    out = W / ('forge_sol_S25_delivery_v2_20261025' if args.seal else 'forge_sol_S25_delivery_draft_v2_20261025')
    if out.exists():
        raise ValueError('output exists: ' + str(out))
    out.mkdir()
    def copy(path, name=None):
        (out / (name or path.name)).write_bytes(path.read_bytes())
    assert sha(PATCH.read_bytes()) == PSHA
    copy(PATCH)
    for name in FILES:
        copy(SOURCE / name)
    copy(Path(__file__))
    copy(W / 'forge_sol_S25_raw_restore_v2_20261025.py')
    for path, name in [(mp, 'forge_sol_S25_native_matrix_v2_20261025.json'),
                       (rp, 'forge_sol_S25_native_review_v2_20261025.json'),
                       (W / 'forge_sol_S25_source_independent_review_v2_20261025.json', 'forge_sol_S25_source_review_v2_20261025.json'),
                       (SOURCE / 'forge_sol_S25_patch_generation_receipt_v2_20261025.json', 'forge_sol_S25_source_proof_v2_20261025.json'),
                       (W / 'forge_sol_S25_inherited_evidence_selection_v2_20261025.json', 'forge_sol_S25_inheritance_v2_20261025.json')]:
        copy(path, name)
    records = collect()
    archive = out / 'forge_sol_S25_raw_evidence_v2_20261025.jsonl.gz'
    with archive.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, filename='', mode='wb', mtime=0, compresslevel=6) as stream:
            for row in records:
                stream.write((json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n').encode())
    index = {'schema': 'S25_original_bytes_base64_v2', 'archive': archive.name,
             'archive_sha256': sha(archive.read_bytes()), 'records': len(records),
             'original_bytes': sum(row['bytes'] for row in records),
             'files': [{key: row[key] for key in ('relative_path', 'bytes', 'sha256')} for row in records],
             'scope': 'Closed current source/native/defaultOFF/cache/controller/failure/review evidence, exact seven prior negative/parser raw records, three prior metadata records and original baseline identity proof. No old whole corpus or engine/backend/net/source-tree/cache export.',
             'restore': 'python3 -B forge_sol_S25_raw_restore_v2_20261025.py --archive ' + archive.name + ' --index forge_sol_S25_evidence_index_v2_20261025.json --out NEW_OUTPUT_FOLDER'}
    ip = out / 'forge_sol_S25_evidence_index_v2_20261025.json'
    ip.write_text(json.dumps(index, indent=2) + '\n')
    restored = W / ('forge_sol_S25_restore_final_v2_20261025' if args.seal else 'forge_sol_S25_restore_draft_v2_20261025')
    result = run(['python3', '-B', out / 'forge_sol_S25_raw_restore_v2_20261025.py', '--archive', archive, '--index', ip, '--out', restored])
    assert result['exit'] == 0
    assert all((restored / row['relative_path']).read_bytes() == Path(row['original_path']).read_bytes() for row in records)
    collision = run(['python3', '-B', out / 'forge_sol_S25_raw_restore_v2_20261025.py', '--archive', archive, '--index', ip, '--out', restored])
    assert collision['exit'] != 0
    (out / 'forge_sol_S25_restore_verification_v2_20261025.json').write_text(json.dumps({
        'status': 'PASS_ALL_RECORDS_RESTORED_AND_ORIGINAL_BYTES_COMPARED', 'records': len(records),
        'restore': result, 'existing_directory_rejected': collision,
        'decoder': 'Reuse qualified S05/S04 portable decoder; job docstring changed only',
        'native_engine_parser_executions': 0}, indent=2) + '\n')
    selected = json.loads((W / 'forge_sol_S25_inherited_evidence_selection_v2_20261025.json').read_text())
    negative = selected['verified_negative_facts']
    total = sum(row['ctest_total'] for row in matrix['profiles'])
    table = '\n'.join('|{base}|{profile}|{ctest_total}/{ctest_total}|{default_OFF_registered_tests}|`{engine_sha256}`|'.format(**row) for row in matrix['profiles'])
    base = W.parent / 'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src'
    net_sha = sha((base / 'src/nnue_weights.inc').read_bytes())
    test_sha = sha((base / 'tests/tests.cpp').read_bytes())
    changes = {}; current = None
    for line in PATCH.read_text().splitlines():
        if line.startswith('diff --git a/'):
            current = line.split(' b/', 1)[1]; changes[current] = [0, 0]
        elif current and line[:1] in ('+', '-') and not line.startswith(('+++', '---')):
            changes[current][0 if line.startswith('+') else 1] += 1
    added = sum(x[0] for x in changes.values()); removed = sum(x[1] for x in changes.values())
    (out / 'forge_sol_S25_diffstat_v2_20261025.txt').write_text('\n'.join(k + f' | +{v[0]}/-{v[1]}' for k, v in changes.items()) + f'\n{len(changes)} files, +{added}/-{removed}\n')
    report = f'''# S25 v2 — strict bench/UCI output contract, 20261025

The output-contract checker passes on all four current L-prime/B Release and ASan/UBSan profiles, with {total}/{total} current CTest tests passing and exactly four known outcomes in each CPP suite. The exact prior shelved default-OFF fixture remains a verified negative for both the post-summary bytes and the extra typed UCI option. It was not replayed, rebuilt or adopted. `FORGE_OUTPUT_CONTRACT` remains OFF by default; accepted h256_e12 is unchanged. Speed and Elo remain UNPROVEN. Publication is UNVERIFIED until root's immutable HTTP/SHA/Git-byte readbacks.

The code base is `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the explicit supplied h256_e12 network overlay SHA256 `{net_sha}`; the raw commit's net differs. B retains its supplied buffer fix. Current merged `tests/tests.cpp` SHA256 `{test_sha}` is calculated from the file. Production src/include and all pre-existing tests are preserved.

Patch `forge_sol_S25_outcontract_v2_20261025.patch` SHA256 `{PSHA}` is private Git full-index/U5 output, {len(changes)} files, +{added}/-{removed}, with three explicit new-file mode100644 headers. Actual old patch Git checks fail `dev/null` on L/L-prime/B while GNU-F0 passes. New Git-check and GNU-F0 dry/apply all pass. The CMake bytes, checker, typed allowlist and parser test file are exactly v1 on each corresponding base. The same additive IDEA paragraph uses a safe common title anchor and preserves all existing notes. Original16-file publication at afb285e2044741e4598b0dea3222390acdb45a8a remains untouched.

## Contract and actual negative

The checked-in allowlist comes from the original source authority, not from candidate output. It defines ten option names with exact types/defaults and spin bounds: Hash, Threads, Move Overhead, Ponder, OwnBook, Book File, Book Depth, Book Variety, UseNNUE and Clear Hash. The first engine invocation is only `bench 11` then `quit`, requiring308972 nodes. One exact LF or CRLF summary terminator is required and zero bytes may follow it. Blank/stat tails, malformed/duplicate summaries, prefixes and missing terminators fail. When the fixed-node precondition holds, a separate `uci`/`quit` process still runs after a tail failure, so both problems are retained. Extra/missing/duplicated/malformed or metadata-changed options fail the typed comparison. Captures wait for EOF and child exit; no caller affinity/host-limit/signal changes are made.

The retained negative ELF SHA256 is `{negative['actual_ELF_sha256']}`, distinct from the QA reference `{negative['QA_reference_different_sha256']}`. Its exact source/flags binding records the shelved backend compile switch OFF, no backend define, static linking and `-march=znver5`; it is a separate fixture, not the current dynamic x86-64-v3 canonical build. Both original engine child processes exit0 with EOF observed. The first d11 node gate passes308972, but the checker exits1 with both `bench_post_summary_bytes` (134 original bytes, SHA256 `67f2c884cd33897f009c752ce668c36eaf9866a1647cff83b1b6485051845d30`) and `unexpected_option` (`NnueExactInt32`, check/default false). Original int32 refresh/update counters are zero; no backend activation/adoption is claimed. The checker/allowlist/parser remain byte-identical, so these exact original control bytes are inherited without running or rebuilding the shelved implementation.

|Check|Status|Scope|
|---|---|---|
|Git-check/GNU-F0 all three bases|PASS|Actual old RED/new GREEN;26 source-application streams|
|v1 CMake/checker/allowlist/parser identity|PASS|Exact corresponding applied bytes; no expectation edits|
|Implicit default OFF cache/registration|PASS|Four actual configurations; new targets absent; L-prime14/B15 baseline counts|
|Current ON full CTest|PASS|Four actual suites, {total}/{total}, KNOWN4/PIN0/FAIL0|
|Current parser controls|PASS|12 cases per registered current parser CTest|
|Current native contract|PASS|Each current bench/uci child exits0/EOF; strict summary tail and typed list accepted|
|Exact shelved negative|PASS inherited expected RED|Both independent violations in original byte records; no new execution|
|Release five reference depths/perft5/FMA|PASS inherited only|Exact current production/main/source/flags binding, prior original qualification; no fresh deep sweep|
|Windows runtime/speed/Elo|UNVERIFIED / UNPROVEN|No PC or strength work in S25 v2|

## Native matrix and reuse

|Base|Profile|ON CTest|Implicit OFF target count|Main ELF SHA256|
|---|---|---|---|---|
{table}

These are fresh current CMake registrations and actual full-suite executions. The source/flag-bound main/core/ordinary helpers and exact current merged CPP executables are reused from the qualified S05 matrix. No fresh C++ compilation or full-engine all-target rebuild is claimed. Each profile preserves current all-target implicit-OFF/ON flag equality, all seven core archive-member identities and complete LastTest output. The existing current CPP source is still the exact merged55334 version, not a historical four-FAIL executable. Both new Python targets are present only ON. Current Release/ASan direct engine invocations obey the first bare d11 gate. The source patch changes tests/docs/registration only; no evaluation, search, NNUE/backend, network, TT, move-order, runtime UCI option or default-output change.

H256 remains float with C++20, `-march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math`; Release O3 and ASan/UBSan O1/g1 scopes are in the exact per-target records. Fixed d11/13/16/20/22 references remain308972/745494/2460422/11901452/31111774 and perft5 totals4865609/193690690. Release deep refs/perfts and FMA proof are inherited by exact engine/source identity rather than repeated; ASan profiles have their actual first d11/current full suites, without a new deep-ASan sweep claim. Existing ordinary-helper and current CPP passes are retained separately from prior old FAIL-format test history.

Two native-preflight observer attempts failed before engine work while assuming incompatible recorded-blob/native-authority schema fields. A later last-profile low-free-space guard stopped preparation and resumed only its pending gates after verified closed-cache recovery, preserving the first three completed cases. Both original failures and corrected preflight metadata are preserved; they are provenance preparation failures, not engine/sanitizer regressions. The current four-case native matrix records its own actual outcomes and resource-stop history. Existing SIMD patch-format and exact-record-schema guidance already covers the metadata-only lesson; it was reused without creating a duplicate skill; this S25 requalification makes no guide edits and preserves the frozen S04/S05 artifacts. The existing guide's later S05 publication-pointer/blob-schema refresh is additive, recorded separately at validation/forge_sol_pack31_20261025/forge_sol_S05_v2_skill_reference_refresh_20261025.json. No cloud/global skill installation is claimed.

## Evidence and continuation

The flat delivery has the patch, three exact test/allowlist files, source/native review and {len(records)} reversible original-byte records. The index gives each path, byte count and SHA256. All current native commands/full streams, original strict-contract child captures/results, complete LastTest logs, source application, controller/cache/preflight failures and resume audits are preserved. Inherited negative evidence is limited to three metadata files and seven exact raw records; baseline qualification uses the original provided-handoff receipt/script and small S05 source/current-matrix authority. The entire old101-record corpus is not redelivered. No shelved backend patch, engine, network, object, source-tree, cache payload, ZIP, license or agent-instruction export is included. Cache payloads referred to by prior recipes remain local-only.

```sh
sha256sum -c forge_sol_S25_SHA256SUMS_v2_20261025.txt
python3 -B forge_sol_S25_outcontract_20261025.py /path/to/forge --out /path/to/NEW_RESULTS_FOLDER
python3 -B forge_sol_S25_raw_restore_v2_20261025.py --archive forge_sol_S25_raw_evidence_v2_20261025.jsonl.gz --index forge_sol_S25_evidence_index_v2_20261025.json --out NEW_OUTPUT_FOLDER
```

Keep the exact options JSON beside the standalone checker. The reused portable decoder actually restored and byte-compared every record; existing output is rejected. All S25 native jobs/cache leases are closed. Next: final independent report/checkpoint binding, root publication plus actual per-file immutable readbacks, then S27 in the saved order. No engine acceptance, speed gain or Elo claim follows from these tests.
'''
    (out / 'forge_sol_S25_report_v2_20261025.md').write_text(report)
    (out / 'forge_sol_S25_continuation_v2_20261025.json').write_text(json.dumps({
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'READY_FINAL_DOCUMENT_BINDING_AND_ROOT_PUBLICATION',
        'patch_sha256': PSHA, 'matrix_sha256': sha(mp.read_bytes()), 'native_review_sha256': sha(rp.read_bytes()),
        'closed_current_profiles': 4, 'current_CTest_passed': total, 'default': 'OFF',
        'evidence_records': len(records), 'negative_backend_replayed_or_adopted': False,
        'negative_ELF_sha256': negative['actual_ELF_sha256'], 'native_jobs': 'CLOSED',
        'accepted_lock_changed': False, 'speed_and_Elo': 'UNPROVEN',
        'publication': 'UNVERIFIED root owns Git and immutable HTTP/SHA/Git-byte verification',
        'next': 'Final independent document binding/root publication, then S27'}, indent=2) + '\n')
    banned = bytes.fromhex('4f70656e4149')
    assert all(banned not in p.read_bytes() for p in out.iterdir() if p.suffix != '.gz')
    if args.seal:
        m = out / 'forge_sol_S25_SHA256SUMS_v2_20261025.txt'
        m.write_text(''.join(sha(p.read_bytes()) + '  ' + p.name + '\n' for p in sorted(out.iterdir())))
        result = run(['sha256sum', '-c', m.name], out); assert result['exit'] == 0
        (W / 'forge_sol_S25_delivery_seal_v2_20261025.json').write_text(json.dumps({
            'folder': str(out), 'files': len(list(out.iterdir())), 'manifest_sha256': sha(m.read_bytes()),
            'archive_sha256': index['archive_sha256'], 'original_records': len(records), 'check': result}, indent=2) + '\n')
    print(json.dumps({'folder': str(out), 'sealed': args.seal, 'records': len(records),
                      'report_sha256': sha(report.encode()), 'archive_sha256': index['archive_sha256']}))


if __name__ == '__main__':
    main()
