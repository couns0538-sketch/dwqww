#!/usr/bin/env python3
"""Export exact source/headers, compile actual-source pickers, compare full bytes.
Run only after root's Release gate. No repository writes or engine games.
"""
import argparse, datetime, hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
BASE = '4e15dea025c4b1ced9cbb5c9000a0cb627edcf15'
CAND = '2c0c7efa49023d8e3f49de3f5596f333a3f01202'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo', type=Path, default='/workspace/dwqww')
p.add_argument('--out', type=Path, required=True)
p.add_argument('--baseline-core', type=Path, default='/workspace/.cloud-setup/forge-qsearch-query-release/libforge_core.a')
p.add_argument('--candidate-core', type=Path, default='/workspace/.cloud-setup/forge-lazy-movepicker-release/libforge_core.a')
p.add_argument('--fixtures', type=Path, default='/workspace/.cloud-setup/legal-witness-investigation/fixtures.tsv')
a = p.parse_args()
a.repo, a.out = a.repo.resolve(strict=True), a.out.resolve()
a.baseline_core, a.candidate_core = a.baseline_core.resolve(strict=True), a.candidate_core.resolve(strict=True)
a.fixtures = a.fixtures.resolve(strict=True)
source = Path(__file__).resolve().with_name('picker_differential.cpp')
corpus = a.repo / 'tools/openings/forge-10000.epd'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, data): path.write_text(json.dumps(data, indent=2) + '\n')
a.out.mkdir(parents=True, exist_ok=False)
inputs = {'harness': source, 'runner': Path(__file__).resolve(), 'corpus': corpus, 'fixtures': a.fixtures,
          'baseline_core': a.baseline_core, 'candidate_core': a.candidate_core}
frozen = {name: {'path': str(path), 'sha256': sha(path)} for name, path in inputs.items()}
protocol = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'baseline_commit': BASE, 'candidate_commit': CAND, 'inputs': frozen,
            'scope': 'Actual-source MovePicker full ordered outputs/legality/parent restoration only; no timing/strength claim',
            'cases': {'corpus': 10000, 'curated': 23, 'variants': 6, 'expected_rows': 60138},
            'histories': 'One deterministic nonzero butterfly/capture/continuation initialization per executable; real8entry stack',
            'variants': ['Mainnone', 'MainTT', 'Mainskipquiet', 'skipafter3legal', 'QSnone', 'QSTT'],
            'contract': 'No next on child; every returned legal move make/unmake plus FEN/key/pawnkey/checkers/history check;<=256+none'}
save(a.out / 'protocol.json', protocol)
result = {'status': 'running', 'exact_byte_equality': False, 'builds': {}}
try:
    compiler = subprocess.check_output(['g++', '--version'], text=True)
    for label, commit, archive in [('baseline', BASE, a.baseline_core), ('candidate', CAND, a.candidate_core)]:
        export = a.out / label / 'source'
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', commit, 'include'], cwd=a.repo, text=True).splitlines()
        paths.append('src/search.cpp')
        exported = {}
        for relative in paths:
            target = export / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=a.repo))
            exported[relative] = sha(target)
        save(a.out / label / 'source-hashes.json', exported)
        binary = a.out / label / 'picker_differential'
        command = ['g++', '-std=c++20', '-O3', '-march=x86-64-v3', '-mtune=znver5', '-fno-fast-math',
                   '-ffp-contract=off', '-fno-lto', '-I', str(export / 'include'),
                   '-DFORGE_PICKER_SOURCE="' + str(export / 'src/search.cpp') + '"',
                   str(source), str(archive), '-pthread', '-o', str(binary)]
        metadata = {'compiler': compiler, 'argv': command, 'source_commit': commit,
                    'source_sha256': exported, 'archive': str(archive), 'archive_sha256': sha(archive)}
        save(a.out / label / 'build.json', metadata)
        with (a.out / label / 'build.log').open('w') as log:
            compiled = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        metadata['build_exit_code'] = compiled.returncode
        save(a.out / label / 'build.json', metadata)
        if compiled.returncode: raise RuntimeError(label + ' actual-source link failed; inspect build.log')
        metadata['binary_sha256'] = sha(binary)
        save(a.out / label / 'build.json', metadata)
        argv = [str(binary), str(corpus), str(a.fixtures)]
        metadata['run_argv'] = argv
        with (a.out / label / 'sequences.tsv').open('xb') as stdout, (a.out / label / 'stderr.log').open('xb') as stderr:
            ran = subprocess.run(argv, stdout=stdout, stderr=stderr, timeout=120)
        metadata['run_exit_code'] = ran.returncode
        metadata['stdout_sha256'] = sha(a.out / label / 'sequences.tsv')
        metadata['stderr_sha256'] = sha(a.out / label / 'stderr.log')
        metadata['stdout_bytes'] = (a.out / label / 'sequences.tsv').stat().st_size
        with (a.out / label / 'sequences.tsv').open('rb') as stdout: metadata['rows'] = sum(1 for _ in stdout)
        save(a.out / label / 'build.json', metadata)
        result['builds'][label] = metadata
        if ran.returncode or metadata['rows'] != 60138:
            raise RuntimeError(label + ' differential execution failed; inspect stderr.log')
    left, right = (a.out / name / 'sequences.tsv' for name in ('baseline', 'candidate'))
    # Compare complete streams in blocks, not just digests/checksums.
    offset = 0
    with left.open('rb') as first, right.open('rb') as second:
        while True:
            a_bytes, b_bytes = first.read(1024 * 1024), second.read(1024 * 1024)
            if a_bytes != b_bytes: raise RuntimeError('full output byte mismatch in block at offset' + str(offset))
            if not a_bytes: break
            offset += len(a_bytes)
    result.update(status='passed', exact_byte_equality=True, compared_bytes=offset)
except Exception as error:
    result.update(status='failed_or_incomplete', error=str(error))
finally:
    changes = [name for name, path in inputs.items() if not path.is_file() or sha(path) != frozen[name]['sha256']]
    if changes: result.update(status='failed_or_incomplete', exact_byte_equality=False, error='input changed:' + ','.join(changes))
    result['outputs_sha256'] = {path.relative_to(a.out).as_posix(): sha(path) for path in a.out.rglob('*')
                                if path.is_file() and path != a.out / 'result.json'}
    save(a.out / 'result.json', result)
print(json.dumps({'status': result['status'], 'exact_byte_equality': result['exact_byte_equality'],
                  'compared_bytes': result.get('compared_bytes'), 'error': result.get('error')}, indent=2))
raise SystemExit(0 if result['status'] == 'passed' else 1)
