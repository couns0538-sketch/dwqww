#!/usr/bin/env python3
"""Current merged-baseline S03 qualification; explicit inputs and new output only."""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess

S02_SHA = 'cc1d5823edbf285aab5311f40b22cd515e42d6f9872e24002a3cd237d5f217d9'
S03_SHA = '0265586224f041140e25e7fe1a46233e0c18f155324f60d83808a8ad30ae5791'
FLAGS = '-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
HELPERS = ['forge_correction_history_tests', 'forge_runtime_psqt_tests',
           'forge_pawn_span_tests', 'forge_nearest_pawn_tests', 'forge_pv_metadata_tests',
           'forge_tt_tests', 'forge_rule50_tests', 'forge_legal_witness_tests']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def raw(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'encoding': 'base64', 'data': base64.b64encode(data).decode('ascii')}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline-receipt', 's02-patch', 's03-patch', 'out', 'cmake', 'ctest'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    assert sha(args.s02_patch) == S02_SHA and sha(args.s03_patch) == S03_SHA
    baseline = json.loads(args.baseline_receipt.read_text())
    assert baseline['status'] == 'PASS'
    assert not os.path.lexists(args.out) and args.out.parent.is_dir()
    out = args.out.resolve()
    out.mkdir()
    temp = out / 'forge_sol_S03_tmp_20261025'
    temp.mkdir()
    env = dict(os.environ, TMPDIR=str(temp), TEMP=str(temp), TMP=str(temp),
               PYTHONDONTWRITEBYTECODE='1')
    record = {'status': 'RUNNING', 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'baseline_receipt_sha256': sha(args.baseline_receipt), 'S02_sha256': S02_SHA,
              'S03_sha256': S03_SHA, 'commands': [], 'profiles': [], 'mutations': []}
    def checkpoint():
        (out / 'forge_sol_S03_v2_native_results_20261025.json').write_text(
            json.dumps(record, indent=2) + '\n')
    def run(label, argv, data=None, cwd=None, allowed=(0,)):
        argv = [str(x) for x in argv]
        child = subprocess.run(argv, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=env, cwd=cwd, check=False)
        item = {'label': label, 'argv': argv, 'cwd': str(cwd) if cwd else None,
                'exit': child.returncode, 'stdin': raw(data or b''), 'stdout': raw(child.stdout),
                'stderr': raw(child.stderr), 'child_waited': True, 'stream_capture_complete': True}
        path = out / f'forge_sol_S03_raw_{len(record["commands"])+1:03d}_{label}_20261025.json'
        path.write_text(json.dumps(item, indent=2) + '\n')
        record['commands'].append({'label': label, 'path': str(path), 'exit': child.returncode})
        checkpoint()
        if child.returncode not in allowed:
            raise RuntimeError(label + ': unexpected exit ' + str(child.returncode))
        return child
    checkpoint()
    sources = {}
    builds = {}
    original_hashes = {}
    try:
        for base in ('Lp', 'B'):
            reference = next(row for row in baseline['profiles'] if row['base'] == base)
            original = Path(reference['source_root'])
            qualified = Path(reference['build'])
            original_hashes[base] = {str(p.relative_to(original)): sha(p)
                                     for p in original.rglob('*') if p.is_file()}
            assert original_hashes[base] == reference['source_hashes']
            assert sha(qualified / 'forge') == reference['main_sha256']
            assert sha(qualified / 'forge_tests') == reference['forge_tests_sha256']
            source = out / f'forge_sol_S03_{base}_source_20261025'
            shutil.copytree(original, source)
            sources[base] = source
            run(base + '_git_init', ['git', 'init', '--quiet', '--template='], cwd=source)
            for label, patch in [('S02', args.s02_patch), ('S03', args.s03_patch)]:
                run(base + '_' + label + '_git_check', ['git', 'apply', '--check', patch], cwd=source)
                run(base + '_' + label + '_F0_dryrun',
                    ['patch', '--batch', '--forward', '-p1', '-F0', '--reject-file=-', '-i', patch, '--dry-run'], cwd=source)
                run(base + '_' + label + '_F0_apply',
                    ['patch', '--batch', '--forward', '-p1', '-F0', '--reject-file=-', '-i', patch], cwd=source)
            for mode in ('OFF', 'ON'):
                tag = base + '_' + mode
                build = out / f'forge_sol_S03_{tag}_build_20261025'
                builds[(base, mode)] = build
                run(tag + '_configure', [args.cmake, '-S', source, '-B', build,
                    '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_FLAGS=' + FLAGS,
                    '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON', '-DFORGE_FIXED_REFERENCES=' + mode])
                assert 'FORGE_WARN_UNKNOWN_OPTIONS:BOOL=OFF' in (build / 'CMakeCache.txt').read_text()
                run(tag + '_fresh_build', [args.cmake, '--build', build, '--target', 'forge', 'forge_tests', '--parallel', '2'])
                # The freshly built main has never been invoked before this bare gate.
                gate = run(tag + '_first_bare_d11', [build / 'forge'], b'bench 11\nquit\n')
                assert not gate.stderr and re.fullmatch(
                    rb'info string bench depth 11 nodes 308972 time \d+ nps \d+\r?\n', gate.stdout)
                assert sha(build / 'forge') == reference['main_sha256']
                assert sha(build / 'forge_tests') == reference['forge_tests_sha256']
                direct = run(tag + '_direct_known4', [build / 'forge_tests'])
                output = direct.stdout + direct.stderr
                assert output.count(b'KNOWN_FAILURE:') == 4 and b'FAIL:' not in output and b'PIN_MISMATCH:' not in output
                row = {'base': base, 'fixed_references': mode, 'status': 'PASS_FRESH_MAIN_AND_TEST_IDENTITY',
                       'main_sha256': sha(build / 'forge'), 'forge_tests_sha256': sha(build / 'forge_tests'),
                       'first_bare_d11': 308972, 'known_count': 4, 'unexpected_fail_count': 0}
                if mode == 'ON':
                    copied = []
                    for name in HELPERS + (['forge_bad_capture_tests'] if base == 'B' else []):
                        before = sha(qualified / name)
                        shutil.copyfile(qualified / name, build / name)
                        (build / name).chmod(0o700)
                        assert sha(build / name) == before
                        copied.append({'file': name, 'source': str(qualified / name), 'sha256': before,
                                       'scope': 'Unchanged current source-qualified baseline support executable'})
                    row['reused_helpers'] = copied
                listed = run(tag + '_ctest_listing', [args.ctest, '--test-dir', build, '-N'])
                assert (b'forge_fixed_references' in listed.stdout) == (mode == 'ON')
                total = (14 if base == 'Lp' else 15) + (mode == 'ON')
                assert re.search(rb'Total Tests: ' + str(total).encode() + rb'\b', listed.stdout)
                if mode == 'ON':
                    suite = run(tag + '_full_ctest', [args.ctest, '--test-dir', build, '--output-on-failure', '-j', '1'])
                    assert b'100% tests passed, 0 tests failed out of ' + str(total).encode() in suite.stdout
                    logfile = build / 'Testing/Temporary/LastTest.log'
                    text = logfile.read_bytes()
                    assert not re.search(rb'(?:Address|Leak|Thread|UndefinedBehavior)Sanitizer|runtime error:|PIN_MISMATCH:|^FAIL:', text, re.M)
                    outputs = list((build / 'forge_sol_S03_runs_20261025').glob('*/forge_sol_S03_results_20261025.json'))
                    assert len(outputs) == 1
                    fixed = json.loads(outputs[0].read_text())
                    assert fixed['status'] == 'PASS' and len(fixed['rows']) == 70
                    assert all(item['status'] == 'PASS' for item in fixed['rows'])
                    row.update(full_CTest_total=total, full_CTest_exit=0, fixed_rows=70,
                               fixed_result_path=str(outputs[0]), full_LastTest_sha256=sha(logfile))
                record['profiles'].append(row)
                checkpoint()
                print(tag, row['status'], 'fixed_rows', row.get('fixed_rows'), flush=True)
        # Private perft-only faults leave search/NNUE production source untouched.
        board = (sources['Lp'] / 'src/board.cpp').read_text()
        changes = [('leaf', 'if (depth <= 0) return 1;', 'if (depth <= 0) return 2;', 'start_d1', 20, 40),
                   ('noep', 'for (const Move move : moves) count += is_legal(move) ? 1 : 0;',
                    'for (const Move move : moves) count += is_legal(move) && (move.flags & EnPassant) == 0U ? 1 : 0;',
                    'start_d5', 4865609, 4865351)]
        common = builds[('Lp', 'OFF')]
        for label, old, new, failure_id, expected, observed in changes:
            assert board.count(old) == 1
            folder = out / f'forge_sol_S03_{label}_mutation_20261025'
            folder.mkdir()
            source = folder / f'forge_sol_S03_{label}_board_20261025.cpp'
            source.write_text(board.replace(old, new, 1))
            obj = folder / f'forge_sol_S03_{label}_board_20261025.o'
            exe = folder / f'forge_sol_S03_{label}_mutant_20261025'
            cc = ['g++', '-std=c++20', '-O3', '-DNDEBUG', *FLAGS.split(), '-pthread']
            run(label + '_compile', [*cc, '-I' + str(sources['Lp'] / 'include'), '-c', source, '-o', obj])
            run(label + '_link', ['g++', '-pthread', common / 'CMakeFiles/forge.dir/src/uci.cpp.o',
                                 obj, common / 'libforge_core.a', '-o', exe])
            gate = run(label + '_first_bare_d11', [exe], b'bench 11\nquit\n')
            assert re.fullmatch(rb'info string bench depth 11 nodes 308972 time \d+ nps \d+\r?\n', gate.stdout) and not gate.stderr
            results = folder / 'forge_sol_S03_checker_run_20261025'
            run(label + '_actual_checker_RED', ['python3', '-B', sources['Lp'] / 'tests/forge_sol_S03_fixedrefs_20261025.py',
                exe, '--out', results], allowed=(1,))
            fixed = json.loads((results / 'forge_sol_S03_results_20261025.json').read_text())
            assert fixed['status'] == 'FAIL' and fixed['rows'][0]['actual'] == 308972 and fixed['rows'][0]['status'] == 'PASS'
            last = fixed['rows'][-1]
            assert last['id'] == failure_id and last['expected'] == expected and last['actual'] == observed and last['status'] == 'FAIL'
            record['mutations'].append({'case': label, 'status': 'PASS_EXPECTED_REAL_ENGINE_RED',
                'private_source_sha256': sha(source), 'mutant_sha256': sha(exe), 'first_bare_d11': 308972,
                'first_failed_id': failure_id, 'expected': expected, 'observed': observed,
                'checker_result': str(results / 'forge_sol_S03_results_20261025.json')})
            checkpoint()
            print(label, 'ACTUAL_MUTATION_CAUGHT', failure_id, expected, observed, flush=True)
        for base in ('Lp', 'B'):
            original = Path(next(row for row in baseline['profiles'] if row['base'] == base)['source_root'])
            assert original_hashes[base] == {str(p.relative_to(original)): sha(p)
                                            for p in original.rglob('*') if p.is_file()}
        record.update(status='PASS_FOUR_FRESH_RELEASE_PROFILES_BOTH_MUTATIONS', original_inputs_unchanged=True,
                      sanitizer_scope='No fresh fixed-reference suite under ASan. Current unchanged production C++/tests inherit separately source-qualified S02 sanitizer results; new fixed-suite ASan execution UNVERIFIED.',
                      speed_and_elo='UNPROVEN; no timing comparison or match')
    except BaseException as exc:
        record.update(status='FAIL_PRESERVED', error=type(exc).__name__ + ': ' + str(exc))
        raise
    finally:
        record['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        checkpoint()
    print(record['status'], flush=True)

if __name__ == '__main__':
    main()
