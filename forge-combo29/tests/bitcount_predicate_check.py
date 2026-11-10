#!/usr/bin/env python3
"""Frozen-source Bitcount predicate validation. No speed or strength claim.

Usage: bitcount_predicate_check.py SOURCE_COMMIT OUTPUT_DIRECTORY
Only src/include are archived, never the repository's bundled binaries.
"""
import hashlib
import json
import os
import pathlib
import subprocess as sp
import sys

repo = pathlib.Path(__file__).resolve().parents[2]
tests = repo / 'forge-combo29/tests'
ref = sp.check_output(['git', 'rev-parse', sys.argv[1]], cwd=repo, text=True).strip()
out = pathlib.Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
root = out / 'source'
root.mkdir(exist_ok=True)
archive = sp.Popen(['git', 'archive', ref, '--', 'forge-combo29/src', 'forge-combo29/include'],
                   cwd=repo, stdout=sp.PIPE)
sp.run(['tar', '-x', '-C', str(root)], stdin=archive.stdout, check=True)
archive.stdout.close()
assert archive.wait() == 0
source = root / 'forge-combo29'
compiler = os.environ.get('CXX', 'g++-14')
flags = ('-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 '
         '-DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 '
         '-DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 '
         '-ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Iinclude -Isrc').split()
commands = []


def run(command, log=None, **kwargs):
    command = [str(v) for v in command]
    commands.append(command)
    if log:
        with (out / log).open('w') as stream:
            sp.run(command, check=True, stdout=stream, stderr=sp.STDOUT, **kwargs)
    else:
        sp.run(command, check=True, **kwargs)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


test_names = ['bitcount_predicate_unit.cpp', 'bitcount_predicate_oracle.cpp', 'bitcount_predicate_check.py',
              'equivalence_screen.py', 'equivalence_positions.fen']
test_hashes = {name: sha(tests / name) for name in test_names}
engine_sources = sorted((source / 'src').glob('*.cpp'))
unit_sources = [tests / 'bitcount_predicate_unit.cpp', tests / 'bitcount_predicate_oracle.cpp',
                *[source / 'src' / (name + '.cpp') for name in ['board', 'bitboard', 'eval', 'eval_params']]]
for mode in (0, 1):
    variant = [*flags, f'-DFORGE_SPD_EVAL_BITCOUNT_PREDICATES={mode}']
    run([compiler, *variant, *engine_sources, '-o', out / f'engine{mode}'], cwd=source)
    run([compiler, *variant, *unit_sources, '-o', out / f'unit{mode}'], cwd=source)
    run([out / f'unit{mode}', tests / 'equivalence_positions.fen'], log=f'unit{mode}.json')
    run([compiler, *variant, '-c', 'src/eval.cpp', '-o', out / f'eval{mode}.o',
         f'-fdump-tree-optimized={out}/eval{mode}.optimized'], cwd=source)
    run(['objdump', '-d', '-C', out / f'eval{mode}.o'], log=f'eval{mode}.assembly')
    run(['size', out / f'eval{mode}.o'], log=f'eval{mode}.size')

expected = '1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6'
assert sha(out / 'engine0') == expected, 'Default-off binary differs from immutable lock build'
assert sha(out / 'eval0.o') != sha(out / 'eval1.o'), 'No opt-in code generation change'
for mode in (0, 1):
    pin_dir = out / f'pins{mode}'
    pin_dir.mkdir(exist_ok=True)
    run(['bash', repo / 'forge-combo29/scripts/check_pins.sh', out / f'engine{mode}'],
        log=f'pins{mode}.log', cwd=pin_dir)
    run(['python3', tests / 'review_evidence/uci_smoke.py', out / f'engine{mode}'],
        log=f'uci{mode}.json')

run(['python3', tests / 'equivalence_screen.py', out / 'engine0', out / 'engine1',
     '--output', out / 'equivalence.json', '--depth', '7'])
for mode in (0, 1):
    run([compiler, *flags, '-O1', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
         '-fno-omit-frame-pointer', f'-DFORGE_SPD_EVAL_BITCOUNT_PREDICATES={mode}', *unit_sources,
         '-o', out / f'unit-sanitize{mode}'], cwd=source)
    run([out / f'unit-sanitize{mode}', tests / 'equivalence_positions.fen'], log=f'sanitize{mode}.log',
        env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'})

# Mutate only opt-in lines; the included default-off oracle stays unchanged.
original_eval = (source / 'src/eval.cpp').read_text()
mutations = {
    'pawn_single_support': ('more_than_one(supported)', 'supported != 0'),
    'bishop_single_counts': ('more_than_one(board.pieces(White, Bishop))', 'board.pieces(White, Bishop) != 0'),
    'bishop_exact_two': ('more_than_one(board.pieces(White, Bishop))', 'popcount(board.pieces(White, Bishop)) == 2'),
}
mutation_results = []
for name, (before, after) in mutations.items():
    assert original_eval.count(before) == 1
    mutant = out / (name + '.cpp')
    mutant.write_text(original_eval.replace(before, after))
    sources = [mutant if p == source / 'src/eval.cpp' else p for p in unit_sources]
    run([compiler, *flags, '-DFORGE_SPD_EVAL_BITCOUNT_PREDICATES=1', *sources,
         '-o', out / name], cwd=source)
    command = [str(out / name), str(tests / 'equivalence_positions.fen')]
    commands.append(command)
    result = sp.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and 'FAIL:' in result.stderr, (name, result.stdout, result.stderr)
    mutation_results.append({'name': name, 'returncode': result.returncode, 'stderr': result.stderr})
(out / 'mutations.json').write_text(json.dumps(mutation_results, indent=2) + '\n')

assert test_hashes == {name: sha(tests / name) for name in test_names}, 'Test changed during validation'
receipt = {
    'source_commit': ref, 'test_hashes': test_hashes, 'commands': commands,
    'compiler': sp.check_output([compiler, '--version'], text=True).splitlines()[0],
    'source_hashes': {str(p.relative_to(source)): sha(p) for folder in ('src', 'include') for p in sorted((source / folder).rglob('*')) if p.is_file()},
    'artifacts': {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()},
    'immutable_lock_commit': '16833ecc03b425586f91f4c8834dea8807bf4c22',
    'default_off_matches_lock': True, 'codegen_changed': True,
    'official_pins_both_modes': True, 'equivalence_comparisons': 256,
    'asan_ubsan_both_modes': True, 'native_speed_gate': 'UNPROVEN', 'native_elo_gate': 'UNPROVEN',
}
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('PASS: lock identity, changed codegen, unit/oracle, pins, UCI, 256 comparisons, ASan/UBSan')
