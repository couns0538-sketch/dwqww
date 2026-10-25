#!/usr/bin/env python3
"""Package only closed S05 v2 evidence; root owns native work and publication."""
from pathlib import Path
import argparse, base64, datetime, gzip, hashlib, json, subprocess

W = Path(__file__).resolve().parent
R = Path('/workspace/dwqww')
V = R / 'validation/forge_sol_pack31_20261025'
SOURCE = W / 'forge_sol_S05_patchwork_v2_20261025/forge_sol_S05_new_Lp_v2_20261025'
PATCH = W / 'forge_sol_S05_source_checkpoint_v2_20261025/forge_sol_S05_ctestwire_v2_20261025.patch'
PSHA = 'b5f38950761743c8a53943bfc02942edc449a471cbda20b9c91438801b566090'
CHECKER_SHA = 'e7ba90e5c2bdb43c490d9c992a684f7f0d311d83c7639ad852f77a4dd079d07f'
HELPERS = ['tests/forge_sol_S05_float_parity_20261025.cpp',
           'tests/forge_sol_S05_float_threads_20261025.cpp',
           'tools/forge_sol_S05_float_uci_20261025.py',
           'tools/forge_sol_S05_fmacheck_v3_20261025.py',
           'tools/forge_sol_S05_fmacheck_tests_20261025.py']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def copy(src, out, name=None):
    dest = out / (name or src.name)
    dest.write_bytes(src.read_bytes())


def run(argv, cwd=None):
    child = subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True)
    result = {'argv': [str(x) for x in argv], 'cwd': str(cwd) if cwd else None,
              'exit': child.returncode}
    for key, raw in [('stdout', child.stdout), ('stderr', child.stderr)]:
        result[key] = {'base64': base64.b64encode(raw).decode(), 'bytes': len(raw), 'sha256': sha(raw)}
    return result


def records():
    rows = {}
    def add(path, name):
        if path.is_symlink() or not path.is_file():
            raise ValueError('Expected original regular evidence: ' + str(path))
        raw = path.read_bytes()
        if name in rows:
            raise ValueError('Duplicate record: ' + name)
        rows[name] = {'relative_path': name, 'original_path': str(path), 'bytes': len(raw),
                      'sha256': sha(raw), 'base64': base64.b64encode(raw).decode()}
    for path in sorted(W.iterdir()):
        if not path.is_file() or not path.name.startswith('forge_sol_S05_'):
            continue
        if any(word in path.name for word in ('delivery_', 'raw_restore', 'report_draft')):
            continue
        if path.suffix in ('.py', '.json', '.jsonl', '.txt', '.gz', '.stdout', '.stderr'):
            add(path, 'S05_v2/' + path.name)
    for folder in sorted(W.iterdir()):
        if not folder.is_dir() or folder.name.startswith(('forge_sol_S05_current_', 'forge_sol_S05_delivery_', 'forge_sol_S05_restore_')):
            continue
        if folder.name == 'forge_sol_S05_patchwork_v2_20261025':
            for path in folder.glob('*.json'):
                add(path, 'S05_v2/' + folder.name + '/' + path.name)
        elif '_native_' in folder.name:
            for path in sorted(folder.iterdir()):
                if path.is_file() and path.suffix in ('.json', '.cmake'):
                    add(path, 'S05_v2/' + folder.name + '/' + path.name)
            last = folder / 'build/Testing/Temporary/LastTest.log'
            if last.is_file():
                add(last, 'S05_v2/' + folder.name + '/LastTest.log')
        elif any(tag in folder.name for tag in ('source_checkpoint', 'checker_work', '_RED_', '_GREEN_')):
            for path in sorted(folder.rglob('*')):
                if path.is_file() and path.suffix in ('.json', '.py', '.txt', '.patch'):
                    add(path, 'S05_v2/' + str(path.relative_to(W)))
    for path in sorted(V.glob('forge_sol_S05_v2_*')):
        if path.is_file() and path.suffix in ('.json', '.py'):
            add(path, 'repository_validation/' + path.name)
    # Current source/engine binding uses the exact provided-handoff VERIFY logs.
    baseline = V / 'forge_sol_handoff1435_recovery_20261025/forge_sol_handoff1435_native_baseline_receipt_20261025.json'
    add(baseline, 'inherited_baseline/' + baseline.name)
    verify = W.parent / 'new_handoff_1435/selected/forge_handoff_full_20261025_1435/VERIFY_FRESH_UNZIP.sh'
    add(verify, 'inherited_baseline/VERIFY_FRESH_UNZIP.sh')
    oldprobe = W.parent / 'S05/forge_sol_S05_private_probe_evidence_20261025/forge_sol_S05_probe_results_20261025.json'
    add(oldprobe, 'inherited_helper_FMA/' + oldprobe.name)
    disassembly = oldprobe.with_name('forge_sol_S05_probe_actual_disassembly_20261025.json')
    add(disassembly, 'inherited_helper_FMA/' + disassembly.name)
    old_source = R / 'releases/forge_sol_pack31_20261025/S05/forge_sol_S05_source_identity_20261025.json'
    add(old_source, 'inherited_source_bridge/' + old_source.name)
    identity = R / 'releases/forge_sol_pack31_20261025/S05/forge_sol_S05_private_probe_source_identity_20261025.json'
    add(identity, 'inherited_helper_FMA/' + identity.name)
    return [rows[key] for key in sorted(rows)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    mp = W / 'forge_sol_S05_native_matrix_receipt_v2_20261025.json'
    matrix = json.loads(mp.read_text())
    assert matrix['completed_profiles'] == matrix['expected_profiles'] == 6
    assert matrix['status'].startswith('PASS')
    review_path = W / 'forge_sol_S05_v2_native_independent_review_20261025.json'
    review = json.loads(review_path.read_text())
    if args.seal:
        assert str(review['status']).startswith(('PASS', 'NO_MATERIAL'))
        assert not review.get('findings') and not review.get('material_findings') and not review.get('blockers')
    out = W / ('forge_sol_S05_delivery_v2_20261025' if args.seal else 'forge_sol_S05_delivery_draft_v2_20261025')
    if out.exists():
        raise ValueError('Output exists: ' + str(out))
    out.mkdir()
    assert sha(PATCH.read_bytes()) == PSHA
    copy(PATCH, out)
    for rel in HELPERS:
        copy(SOURCE / rel, out)
    copy(Path(__file__), out)
    copy(W / 'forge_sol_S05_raw_restore_v2_20261025.py', out)
    for path, name in [(mp, 'forge_sol_S05_native_matrix_v2_20261025.json'),
                       (review_path, 'forge_sol_S05_native_review_v2_20261025.json'),
                       (W / 'forge_sol_S05_v2_root_python_independent_review_20261025.json', 'forge_sol_S05_Python_review_v2_20261025.json'),
                       (W / 'forge_sol_S05_patchwork_v2_20261025/forge_sol_S05_patch_generation_receipt_v2_20261025.json', 'forge_sol_S05_source_proof_v2_20261025.json'),
                       (W / 'forge_sol_S05_actual_PE_ELF_static_GREEN_v2_20261025.json', 'forge_sol_S05_PC_Linux_static_v2_20261025.json'),
                       (V / 'forge_sol_S05_v2_skill_reference_maintenance_20261025.json', 'forge_sol_S05_skill_proof_v2_20261025.json')]:
        copy(path, out, name)
    rows = records()
    archive = out / 'forge_sol_S05_raw_evidence_v2_20261025.jsonl.gz'
    with archive.open('xb') as target:
        with gzip.GzipFile(fileobj=target, filename='', mode='wb', mtime=0, compresslevel=6) as stream:
            for row in rows:
                stream.write((json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n').encode())
    index = {'schema': 'S05_original_bytes_base64_v2', 'archive': archive.name,
             'archive_sha256': sha(archive.read_bytes()), 'records': len(rows),
             'original_bytes': sum(row['bytes'] for row in rows),
             'files': [{key: row[key] for key in ('relative_path', 'bytes', 'sha256')} for row in rows],
             'scope': 'Current original frozen source/static/fixtures/cleanup/native commands/full streams/controllers/reviews/skill proof. Prior baseline VERIFY and helper-FMA identities only; no old whole corpus, engine/weight/object/source-tree/cache-payload export.',
             'restore': 'python3 -B forge_sol_S05_raw_restore_v2_20261025.py --archive ' + archive.name + ' --index forge_sol_S05_evidence_index_v2_20261025.json --out NEW_OUTPUT_FOLDER'}
    ip = out / 'forge_sol_S05_evidence_index_v2_20261025.json'
    ip.write_text(json.dumps(index, indent=2) + '\n')
    restored = W / ('forge_sol_S05_restore_final_v2_20261025' if args.seal else 'forge_sol_S05_restore_draft_v2_20261025')
    restored_run = run(['python3', '-B', out / 'forge_sol_S05_raw_restore_v2_20261025.py', '--archive', archive, '--index', ip, '--out', restored])
    assert restored_run['exit'] == 0
    assert all((restored / row['relative_path']).read_bytes() == Path(row['original_path']).read_bytes() for row in rows)
    collision = run(['python3', '-B', out / 'forge_sol_S05_raw_restore_v2_20261025.py', '--archive', archive, '--index', ip, '--out', restored])
    assert collision['exit'] != 0
    (out / 'forge_sol_S05_restore_verification_v2_20261025.json').write_text(json.dumps({
        'status': 'PASS_ALL_ORIGINAL_RECORD_BYTES_RESTORED_AND_COMPARED', 'records': len(rows),
        'restore': restored_run, 'existing_directory_rejected': collision, 'native_executions': 0,
        'reused_restore_implementation': 'S04v2 portable decoder; only job docstring changed'}, indent=2) + '\n')
    static = json.loads((W / 'forge_sol_S05_actual_PE_ELF_static_GREEN_v2_20261025.json').read_text())
    pc = next(row for row in static['rows'] if row['label'] == 'PC_PE')
    current_tests = W.parent / 'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src/tests/tests.cpp'
    net = current_tests.parents[1] / 'src/nnue_weights.inc'
    totals = sum(row['ctest_total'] for row in matrix['profiles'])
    table = '\n'.join('|{base}|{profile}|{option}|{ctest_total}/{ctest_total}|{new_S05_ctest_targets}|`{engine_sha256}`|'.format(**row) for row in matrix['profiles'])
    changes = {}
    current = None
    for line in PATCH.read_text().splitlines():
        if line.startswith('diff --git a/'):
            current = line.split(' b/', 1)[1]; changes[current] = [0, 0]
        elif current and line.startswith('+') and not line.startswith('+++'):
            changes[current][0] += 1
        elif current and line.startswith('-') and not line.startswith('---'):
            changes[current][1] += 1
    added = sum(row[0] for row in changes.values()); removed = sum(row[1] for row in changes.values())
    (out / 'forge_sol_S05_diffstat_v2_20261025.txt').write_text('\n'.join(name + ' | +' + str(value[0]) + '/-' + str(value[1]) for name, value in changes.items()) + f'\n{len(changes)} files, +{added}/-{removed}\n')
    report = f'''# S05 v2 — copied-zero FMA qualification and fixture cleanup, 20261025

The repaired checker passes static disassembly of the supplied Windows PC lock and Linux lock, rejects the retained real helper-FMA mutant, and cleans temporary CTest fixture directories on both successful and failing test exits. All six current L-prime/B profiles pass {totals}/{totals} CTest with exactly four known outcomes and no PIN_MISMATCH/FAIL in each merged CPP suite. `FORGE_BUILD_NNUE_VALIDATION` remains OFF by default. Speed and Elo are UNPROVEN; accepted h256_e12 is unchanged. Publication remains UNVERIFIED until root's actual immutable readbacks.

Baseline code `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the supplied h256_e12 net overlay SHA256 `{sha(net.read_bytes())}`; the commit's original net differs. B retains the supplied buffer repair. Current merged `tests/tests.cpp` SHA256 `{sha(current_tests.read_bytes())}` is calculated from the actual file. No engine, NNUE arithmetic, network, search, TT, move ordering, UCI tool or CMake behavior changed from S05 v1. The two Python file updates and IDEA placement are the bounded v2 changes.

Patch `forge_sol_S05_ctestwire_v2_20261025.patch` SHA256 `{PSHA}` is a full-index Git-U5 diff: {len(changes)} files, +{added}/-{removed}, five proper new-file mode100644 headers. Actual old S05 Git checks PASS all three bases; no fabricated old Git RED is claimed. Actual v2 Git-check and GNU-F0 dry/apply PASS L/L-prime/B. CMake, both float C++ helpers and UCI tool are byte-identical to the old applied patch on each base. The same IDEA entry is relocated after a shared safe title, preserving every old note. The original publication remains untouched.

## Checker and cleanup evidence

The old checker fails two of the 27 copied-zero fixtures. Final checker SHA256 `{CHECKER_SHA}` and final runner SHA256 `152f0d77b61d69bd28d93a24b43a936b7b7bf49f1fea1998a0946d48df70e287` pass all27. Zero provenance now propagates only across an unmasked same-width YMM register `vmovaps`/`vmovups` copy from an already proven-zero source. Existing register/alias clobber invalidation and call/jump barriers remain. Memory, unknown, narrow and masked-copy sources are rejected by fixtures. This is a bounded 256-bit recognized-lowering checker requiring demangled NNUE symbols, not proof of arbitrary binary data flow or semantic equivalence. Unsupported or stripped lowerings remain unsupported.

Supplied PC PE SHA256 `{pc['exe_sha256']}` passes the copied-zero mask-clamp path, NNUE-scoped FMA0 and a separately retained whole-executable FMA count0. Linux canonical ELF also passes both counts0. Full original whole-disassembly gzip streams, original checker commands/stdout/stderr and scopes are preserved. The Windows executable was statically disassembled on Linux; Windows runtime execution is UNVERIFIED. The new checker also rejects the exact retained native helper-FMA mutant with exit1. That is a fresh static qualification of a source/binary-bound old mutant; no new mutant engine runtime or compilation is claimed.

Default fixture execution uses a temporary-directory lifetime that is closed through success and unittest SystemExit1. The actual old cleanup RED retains its leaked directory; new success and deliberate fixture-failure cases both leave an empty parent. Explicit `--out` remains persistent for review evidence. Full27 final-runner execution and selected lifetime controls are distinct recorded runs.

|Check|Status|Evidence scope|
|---|---|---|
|Old copied-zero fixtures / final27|RED2 / PASS27|Actual original commands and streams|
|Default success/failure cleanup|PASS|Both parent listings empty; explicit output persists|
|Actual PC PE / Linux scoped and whole FMA|PASS static|All counts0; both original full disassembly gzip streams|
|Actual helper-FMA mutant|PASS expected rejection|Retained exact native executable; new checker exits1|
|Git and GNU-F0 all three bases|PASS|22 original commands /44 streams; unchanged C++/CMake/UCI bytes|
|Six current merged native suites|PASS|{totals}/{totals} actual CTest; KNOWN4 /PIN0 /FAIL0|
|First bare d11|PASS fresh invocation|308972 before other runtime checks in each profile|
|Five Release refs and perft5 totals|PASS inherited|Exact canonical production engine/source binding and original current-handoff VERIFY streams|
|Float parity/thread/UCI replay|PASS current CTest|Only registered ON-suite invocations; no extra old-corpus replay|
|Windows runtime, speed, Elo|UNVERIFIED / UNPROVEN|No native PC execution or strength measurement|

## Current native scope

|Base|Profile|Option|CTest|Added S05 targets|Main ELF SHA256|
|---|---|---|---|---|---|
{table}

Current merged CPP tests are freshly compiled and the actual current CMake full suites exercise the frozen Python files. Qualified existing production main/core/native helper bytes are reused with exact source, flags, archive/member and fixture identities. No fresh full-engine all-target build is claimed. OFF adds no validation targets; ON adds the same five float/API/UCI/checker targets. H256 stays float with C++20, `-ffp-contract=off -fno-fast-math`; exact Release O3 and ASan/UBSan O1/g1 per-target flags are retained. Each registered ON parity invocation reports21306 comparisons/20194 transitions with zero lane/score/state mismatches; the warm four-worker test reports8000 transitions with zero errors. It serially bootstraps immutable data before its worker gate and does not replace S04's separate cold-first-Board test. Actual depth4 UCI searches reset via ucinewgame before each replay; NNUE c2c4/cp25 repeats around the completed HCE d2d4/cp13 search, without a universal warm/cold equality claim.

The fixed reference oracle remains d11/13/16/20/22 =308972/745494/2460422/11901452/31111774, perft5 start4865609 and kiwipete193690690. Deep refs/perfts are inherited through exact same production bytes and original provided-handoff full-VERIFY evidence. No extra old whole corpus, deep benchmark sweep or new speed measurement is claimed. Kiwipete: `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`.

Existing repository-local SIMD-validation guidance was extended for copied-register zero proofs and temporary-directory lifetime checks. The separate S05 before/after reference proof, original static/fixture/cleanup command captures and final local guide SHA256 `a1da44076c52410b87033d41fcbb7eab478b7752b12aacc54bcb0516ed70470c` are included; the frozen S04 guide2b8 identity is separate. The updated skill is `.agents/skills/validating-chess-simd/SKILL.md`; see `forge_sol_S05_skill_proof_v2_20261025.json`. This is reference-command validation and existing-skill maintenance, not a fresh-agent pressure test or cloud/global installation. The immutable v1 checker pointer remains until root qualifies and publishes its successor.

## Recoverable checkpoint

The flat delivery provides the patch, five exact helper sources, source/static/native reviews and {len(rows)} original-byte evidence records. The index records every path, size and SHA256. Prior current-handoff baseline logs and the actual helper-FMA result/identity are the only inherited corpus; the entire old S05 corpus is not resubmitted. All new fixture history, cleanup RED/GREEN, native full streams/LastTest logs, controllers, incomplete observer approaches and skill proof are retained. No ZIP, source-tree, engine ELF/PE, net, object or cache-payload export is included. Any cache payload paths remain local-only dependencies for rebuilding reused products.

```sh
sha256sum -c forge_sol_S05_SHA256SUMS_v2_20261025.txt
python3 -B forge_sol_S05_raw_restore_v2_20261025.py --archive forge_sol_S05_raw_evidence_v2_20261025.jsonl.gz --index forge_sol_S05_evidence_index_v2_20261025.json --out NEW_OUTPUT_FOLDER
```

The reused portable decoder actually restored and byte-compared every record; an existing output directory was rejected. All S05 native jobs and leases are closed. Next: independent final document/package binding and root immutable publication verification, then the saved S25 requalification/S27 order. No engine acceptance or speed/Elo claim follows.
'''
    (out / 'forge_sol_S05_report_v2_20261025.md').write_text(report)
    (out / 'forge_sol_S05_continuation_v2_20261025.json').write_text(json.dumps({
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'READY_FINAL_DOCUMENT_BINDING_AND_ROOT_PUBLICATION',
        'baseline_code_commit': '1ab50b2dd64d9b2f752f7f1285f6968cad2fd792',
        'net_sha256': sha(net.read_bytes()), 'patch_sha256': PSHA,
        'matrix_sha256': sha(mp.read_bytes()), 'native_review_sha256': sha(review_path.read_bytes()),
        'current_profiles': 6, 'current_CTest_passed': totals, 'evidence_records': len(rows),
        'default': 'OFF', 'accepted_lock_changed': False, 'speed_and_Elo': 'UNPROVEN',
        'Windows_runtime': 'UNVERIFIED static PC disassembly only',
        'publication': 'UNVERIFIED root owns commit/push/actual HTTP and Git-byte verification',
        'next': 'Final independent document binding, root publication verification, then S25 current-tree qualification'}, indent=2) + '\n')
    banned = bytes.fromhex('4f70656e4149')
    assert all(banned not in path.read_bytes() for path in out.iterdir() if path.suffix != '.gz')
    if args.seal:
        manifest = out / 'forge_sol_S05_SHA256SUMS_v2_20261025.txt'
        manifest.write_text(''.join(sha(path.read_bytes()) + '  ' + path.name + '\n' for path in sorted(out.iterdir())))
        check = run(['sha256sum', '-c', manifest.name], out)
        assert check['exit'] == 0
        (W / 'forge_sol_S05_delivery_seal_v2_20261025.json').write_text(json.dumps({
            'folder': str(out), 'files': len(list(out.iterdir())), 'manifest_sha256': sha(manifest.read_bytes()),
            'archive_sha256': index['archive_sha256'], 'original_records': len(rows), 'check': check}, indent=2) + '\n')
    print(json.dumps({'folder': str(out), 'sealed': args.seal, 'records': len(rows),
                      'report_sha256': sha(report.encode()), 'archive_sha256': index['archive_sha256']}))


if __name__ == '__main__':
    main()
