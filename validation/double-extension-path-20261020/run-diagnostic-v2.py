#!/usr/bin/env python3
"""Build an isolated, instrumentation-only actual-engine double-extension witness."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import subprocess
import time

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = Path('/workspace/.cloud-setup/double-extension-path-source')
BUILD = Path('/workspace/.cloud-setup/double-extension-path-build-v2')
OUT = HERE / 'diagnostic-v2-attempt1'
OUT.mkdir(exist_ok=False)
assert not BUILD.exists(), 'Never reuse a diagnostic build directory'
ENV = os.environ.copy()
ENV['PYTHONDONTWRITEBYTECODE'] = '1'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save():
    (OUT / 'commands.json').write_text(json.dumps(report, indent=2) + '\n')

report = {'source_sha': 'cecf0b9e3af5602053bcaf5c5d16ffc09f58850d',
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'scope': 'Actual-engine instrumentation only; no production, performance or Elo claim',
          'steps': [], 'status': 'RUNNING'}
baseline = json.loads((HERE / 'BASELINE-SOURCE.json').read_text())
before = {str(p.relative_to(SOURCE)): sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()}
assert before.keys() == baseline['source_sha256'].keys()
for name, value in baseline['source_sha256'].items():
    assert before[name] == (sha(HERE / 'instrumented-search-v2.cpp') if name == 'src/search.cpp' else value), name
report['source_hashes_before'] = before
save()

def run(label, command, stdin=None, timeout=600):
    if stdin is not None:
        (OUT / (label + '.stdin')).write_bytes(stdin)
    start = time.monotonic()
    with (OUT / (label + '.stdout')).open('xb') as stdout, (OUT / (label + '.stderr')).open('xb') as stderr:
        proc = subprocess.run(command, input=stdin, stdout=stdout, stderr=stderr,
                              env=ENV, cwd=REPO, timeout=timeout)
    row = {'label': label, 'command': command, 'exit_code': proc.returncode,
           'timeout_seconds': timeout, 'elapsed_seconds_diagnostic_only': time.monotonic() - start,
           'stdout_sha256': sha(OUT / (label + '.stdout')),
           'stderr_sha256': sha(OUT / (label + '.stderr'))}
    report['steps'].append(row)
    save()
    print(json.dumps(row), flush=True)
    assert proc.returncode == 0, (label, proc.returncode)

try:
    run('configure', ['/workspace/.cloud-setup/venv/bin/cmake', '-S', str(SOURCE), '-B', str(BUILD),
                      '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                      '-DFORGE_ENABLE_SANITIZERS=OFF', '-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto'])
    run('build', ['/workspace/.cloud-setup/venv/bin/cmake', '--build', str(BUILD), '--target', 'forge', '--parallel', '1'])
    report['diagnostic_binary_sha256'] = sha(BUILD / 'forge')
    report['diagnostic_core_sha256'] = sha(BUILD / 'libforge_core.a')
    original = Path('/workspace/.cloud-setup/forge-clock-contract-release/forge')
    known = json.loads((REPO / 'validation/upstream-clock-reconcile-20261020/frozen-release-attempt1/summary.json').read_text())
    assert known['status'] == 'PASS' and sha(original) == known['binary_sha256_after']['forge']
    report['baseline_binary_sha256'] = sha(original)
    run('baseline-bench11', [str(original)], b'setoption name OwnBook value false\nbench 11\nquit\n', timeout=30)
    run('diagnostic-bench11', [str(BUILD / 'forge')], b'setoption name OwnBook value false\nbench 11\nquit\n', timeout=30)
    def nodes(label):
        data = (OUT / (label + '.stdout')).read_text()
        return int(re.search(r'bench depth 11 nodes (\d+)', data).group(1))
    assert nodes('baseline-bench11') == nodes('diagnostic-bench11') == 419798
    report['bench_nodes_parity'] = 419798
    data = (OUT / 'diagnostic-bench11.stderr').read_text()
    traces = [json.loads(line.removeprefix('DE_TRACE ')) for line in data.splitlines() if line.startswith('DE_TRACE ')]
    summaries = [json.loads(line.removeprefix('DE_SUMMARY ')) for line in data.splitlines() if line.startswith('DE_SUMMARY ')]
    assert len(summaries) == 8, len(summaries)
    (OUT / 'traces.json').write_text(json.dumps(traces, indent=2) + '\n')
    (OUT / 'summaries.json').write_text(json.dumps(summaries, indent=2) + '\n')
    report['summary_totals'] = {key: sum(row[key] for row in summaries) for key in summaries[0]}
    after = {str(p.relative_to(SOURCE)): sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()}
    assert before == after
    assert report['baseline_binary_sha256'] == sha(original)
    assert report['diagnostic_binary_sha256'] == sha(BUILD / 'forge')
    assert report['diagnostic_core_sha256'] == sha(BUILD / 'libforge_core.a')
    report.update(status='PASS', inputs_unchanged=True, source_hashes_after=after,
                  completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save()
    print(json.dumps({'status': 'PASS', 'summary_totals': report['summary_totals']}), flush=True)
except Exception as error:
    report.update(status='FAILED_OR_INCOMPLETE', error=repr(error))
    save()
    raise
