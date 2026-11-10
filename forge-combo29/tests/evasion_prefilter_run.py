#!/usr/bin/env python3
"""Explicit opt-in, bounded legality probe. No timing/matches/production edits."""
import argparse, hashlib, json, pathlib, subprocess, tempfile
LOCK = '16833ecc03b425586f91f4c8834dea8807bf4c22'
p = argparse.ArgumentParser()
p.add_argument('--run', action='store_true', help='Required explicit opt-in after CPU coordination')
p.add_argument('--cxx', default='g++')
p.add_argument('--output', type=pathlib.Path)
a = p.parse_args()
if not a.run:
    p.exit(message='Default off. Use --run only after CPU coordination.\n')
repo = pathlib.Path(__file__).resolve().parents[2]
def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])
assert git('branch', '--show-current').decode().strip() == 'dot/review-20261110'
probe = pathlib.Path(__file__).with_name('evasion_prefilter_probe.cpp')
with tempfile.TemporaryDirectory(prefix='forge-evasion-prefilter-') as directory:
    root = pathlib.Path(directory)
    manifest = {}
    # Exact source-only allowlist: headers plus board and bitboard, no Windows artifacts.
    names = git('ls-tree', '-r', '--name-only', LOCK, 'forge-combo29/include').decode().splitlines()
    names += ['forge-combo29/src/board.cpp', 'forge-combo29/src/bitboard.cpp']
    for name in names:
        data = git('show', f'{LOCK}:{name}')
        target = root / pathlib.Path(name).relative_to('forge-combo29')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest[name] = hashlib.sha256(data).hexdigest()
    fixture = pathlib.Path(__file__).with_name('evasion_prefilter_positions.fen').read_bytes()
    # Double-check, rook check with nonking distractors, EP capturing a checking pawn,
    # pinned nonking survivor, and promotion capture of a checking rook.
    fixture += b'\n4r2k/8/8/8/1b6/8/PP6/4K1N1 w - - 0 1\n'
    fixture += b'4r2k/8/8/8/8/8/PP6/R3K1N1 w - - 0 1\n'
    fixture += b'7k/8/8/3pP3/4K3/8/8/8 w - d6 0 1\n'
    fixture += b'4r2k/8/8/8/1b6/8/3R4/4K3 w - - 0 1\n'
    fixture += b'4r2k/3P4/8/8/8/8/8/4K3 w - - 0 1\n'
    (root/'fixtures.fen').write_bytes(fixture)
    (root/'probe.cpp').write_bytes(probe.read_bytes())
    flags=['-std=c++20','-O2','-DNDEBUG','-DFORGE_NNUE_HIDDEN=256',
           '-DFORGE_SPD_SLIDER_PEXT=0','-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-I'+str(root/'include')]
    command=[a.cxx,*flags,str(root/'probe.cpp'),str(root/'src/board.cpp'),str(root/'src/bitboard.cpp'),'-o',str(root/'probe')]
    subprocess.run(command,check=True,timeout=120)
    result=json.loads(subprocess.check_output([str(root/'probe'),str(root/'fixtures.fen')],timeout=60))
    receipt={'baseline':LOCK,'purpose':'bounded predicate correctness and fixture frequency, not timing or search distribution',
             'compiler':subprocess.check_output([a.cxx,'--version']).decode().splitlines()[0],
             'flags':flags[:-1]+['-I<snapshot>/include'], 'snapshot_sha256':manifest,
             'probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),
             'fixtures_sha256':hashlib.sha256(fixture).hexdigest(), 'counts':result}
    output=json.dumps(receipt,indent=2)+'\n'
    if a.output: a.output.write_text(output)
    print(output,end='')
