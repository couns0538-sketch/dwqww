#!/usr/bin/env python3
"""Assembly-only subset screen; no timing or strength inference.
Usage: bitcount_predicate_codegen.py SOURCE_COMMIT OUTPUT_DIRECTORY
Archives src/include only and modifies temporary copies, never the checkout.
"""
import hashlib
import json
import os
import pathlib
import subprocess as sp
import sys

repo = pathlib.Path(__file__).resolve().parents[2]
ref = sp.check_output(['git', 'rev-parse', sys.argv[1]], cwd=repo, text=True).strip()
out = pathlib.Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
archive_root = out / 'source'
archive_root.mkdir(exist_ok=True)
archive = sp.Popen(['git', 'archive', ref, '--', 'forge-combo29/src', 'forge-combo29/include'],
                   cwd=repo, stdout=sp.PIPE)
sp.run(['tar', '-x', '-C', str(archive_root)], stdin=archive.stdout, check=True)
archive.stdout.close()
assert archive.wait() == 0
source = archive_root / 'forge-combo29'
compiler = os.environ.get('CXX', 'g++-14')
flags = ('-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 '
         '-DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 '
         '-DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 '
         '-ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Iinclude').split()
original = (source / 'src/eval.cpp').read_text()
# Use the immutable pre-experiment source. Reject a guarded input rather than
# accidentally editing both arms and misidentifying the tested experiment.
assert 'FORGE_SPD_EVAL_BITCOUNT_PREDICATES' not in original
replacements = {
    'pawn': [('popcount(supported) > 1', 'more_than_one(supported)')],
    'bishop': [(f'popcount(board.pieces({c}, Bishop)) >= 2', f'more_than_one(board.pieces({c}, Bishop))')
               for c in ('White', 'Black')],
    'one': [('popcount(white_bishops) == 1 && popcount(black_bishops) == 1',
             'white_bishops != 0 && !more_than_one(white_bishops) && black_bishops != 0 && !more_than_one(black_bishops)')],
}
replacements['before'] = []
replacements['both'] = replacements['pawn'] + replacements['bishop']
commands = []
results = {}
for name in ('before', 'pawn', 'bishop', 'both', 'one'):
    variant = out / name
    variant.mkdir(exist_ok=True)
    text = original
    for before, after in replacements[name]:
        assert text.count(before) == 1
        text = text.replace(before, after)
    path = variant / 'eval.cpp'
    path.write_text(text)
    for tail in (['-S', '-fverbose-asm', '-o', str(variant / 'eval.s')],
                 ['-c', '-o', str(variant / 'eval.o'), f'-fdump-tree-optimized={variant}/eval.optimized']):
        command = [compiler, *flags, str(path), *tail]
        commands.append(command)
        sp.run(command, cwd=source, check=True)
    for command, filename in ((['size', variant / 'eval.o'], 'size.txt'),
                               (['nm', '-S', '--size-sort', '-C', variant / 'eval.o'], 'symbols.txt'),
                               (['objdump', '-d', '-C', variant / 'eval.o'], 'assembly.txt')):
        command = [str(x) for x in command]
        commands.append(command)
        (variant / filename).write_text(sp.check_output(command, text=True))
    assembly = (variant / 'eval.s').read_text()
    results[name] = {
        'static_popcntq_sites': assembly.count('\tpopcntq\t'),
        'static_blsr_sites': assembly.count('\tblsr\t'),
        'size': (variant / 'size.txt').read_text(),
        'eval_symbols': [line for line in (variant / 'symbols.txt').read_text().splitlines()
                         if 'scale_factor' in line or 'evaluate_position' in line],
        'artifacts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(variant.iterdir()) if p.is_file()},
    }
report = {'source_commit': ref, 'compiler': sp.check_output([compiler, '--version'], text=True).splitlines()[0],
          'commands': commands, 'variants': results, 'speed_gate': 'UNPROVEN', 'elo_gate': 'UNPROVEN'}
(out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({name: result['static_popcntq_sites'] for name, result in results.items()}))
