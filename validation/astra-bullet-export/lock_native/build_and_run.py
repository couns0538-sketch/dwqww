#!/usr/bin/env python3
"""Build an AL1 evaluator from unchanged source and one explicit include asset."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

name, include_path, fens_path, *extra = sys.argv[1:]
assert re.fullmatch(r'[a-z0-9_]+', name), name
include_path, fens_path = Path(include_path).resolve(), Path(fens_path).resolve()
evidence = Path(__file__).resolve().parent / name
evidence.mkdir()
build = Path('/tmp/astra-al1-native') / name
build.mkdir(parents=True)
source = Path('/tmp/astra-al1-lock-source')
repo = Path('/tmp/forge-astra-bullet-export')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
commands = []
manifest = json.loads((evidence.parent / 'source_manifest.json').read_text())
for rel, data in manifest['files'].items():
    assert sha(source / rel) == data['sha256'], rel
shutil.copyfile(source / 'src/nnue.cpp', build / 'nnue.cpp')
shutil.copyfile(include_path, build / 'nnue_weights.inc')
identity = {'source_commit': manifest['source_commit'], 'source_manifest': '../source_manifest.json',
            'include_source': str(include_path), 'include_sha256': sha(include_path),
            'compiled_nnue_cpp_sha256': sha(build / 'nnue.cpp'),
            'fens': str(fens_path), 'fens_sha256': sha(fens_path),
            'oracle_sha256': sha(repo / 'tools/bullet/lock_oracle.cpp'),
            'compiler_version': subprocess.check_output(['/usr/bin/c++', '--version'], text=True)}
(evidence/'identity.json').write_text(json.dumps(identity, indent=2)+'\n')

def run(label, cmd):
    start = time.monotonic()
    record = {'argv': [str(x) for x in cmd], 'cwd': str(build),
              'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with (evidence/f'{label}.stdout.log').open('w') as out, (evidence/f'{label}.stderr.log').open('w') as err:
        proc = subprocess.run(cmd, cwd=build, stdout=out, stderr=err, timeout=900)
    record.update(returncode=proc.returncode, duration_seconds=time.monotonic()-start)
    commands.append(record)
    (evidence/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
    assert proc.returncode == 0, record

binary = build / 'lock_oracle'
run('build', ['/usr/bin/c++', '-std=c++20', '-O3', '-DNDEBUG', '-march=x86-64-v3', '-mtune=znver5',
    '-ffp-contract=off', '-fno-fast-math', '-DFORGE_NNUE_HIDDEN=256', '-pthread', '-Wall', '-Wextra',
    '-I'+str(source/'include'), repo/'tools/bullet/lock_oracle.cpp', source/'src/bitboard.cpp',
    source/'src/board.cpp', source/'src/eval.cpp', source/'src/eval_params.cpp', build/'nnue.cpp', '-o', binary])
identity['binary_sha256'] = sha(binary)
(evidence/'identity.json').write_text(json.dumps(identity, indent=2)+'\n')
args = [binary, fens_path, evidence/'native_cp.txt']
if extra:
    assert extra == ['--hce'], extra
    args += ['--hce', evidence/'native_hce.txt']
run('evaluate', args)
dis = subprocess.run(['objdump','-d',binary],capture_output=True,text=True,check=True)
matches = [line for line in dis.stdout.splitlines() if re.search(r'\b(?:v?fmadd|v?fmsub|v?fnmadd|v?fnmsub)',line)]
(evidence/'fma_matches.txt').write_text('\n'.join(matches)+ ('\n' if matches else ''))
result={'positions':len((evidence/'native_cp.txt').read_text().splitlines()),'fma_count':len(matches),
        'disassembly_command':['objdump','-d',str(binary)],
        'binary_sha256':sha(binary),'native_cp_sha256':sha(evidence/'native_cp.txt'),
        'source_hashes_match_after':all(sha(source/p)==v['sha256'] for p,v in manifest['files'].items()),
        'include_hash_matches_after':sha(include_path)==identity['include_sha256']}
(evidence/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
