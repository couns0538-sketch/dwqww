#!/usr/bin/env python3
"""Recompile only isolated changed search.cpp; reuse byte-frozen other objects."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import time

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = Path('/workspace/.cloud-setup/double-extension-path-green-source')
BUILD = Path('/workspace/.cloud-setup/double-extension-path-green-build-v2')
BASE = Path('/workspace/.cloud-setup/forge-clock-contract-release')
OUT = HERE / 'green-v2-attempt1'
OUT.mkdir(exist_ok=False)
BUILD.mkdir(exist_ok=False)
(BUILD / 'CMakeFiles/forge.dir').mkdir(parents=True)
ENV = os.environ.copy()
ENV['PYTHONDONTWRITEBYTECODE'] = '1'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

frozen = json.loads((REPO / 'validation/upstream-clock-reconcile-20261020/frozen-release-attempt1/summary.json').read_text())
assert frozen['status'] == 'PASS'
assert sha(BASE / 'libforge_core.a') == frozen['binary_sha256_after']['libforge_core.a']
assert sha(BASE / 'forge') == frozen['binary_sha256_after']['forge']
original_inputs = [BASE / 'libforge_core.a', BASE / 'forge', BASE / 'compile_commands.json',
                   BASE / 'CMakeFiles/forge.dir/link.txt', BASE / 'CMakeFiles/forge.dir/src/uci.cpp.o']
source_before = {str(p.relative_to(SOURCE)): sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()}
report = {'source_sha': frozen['source_commit'],
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'scope': 'Isolated unapplied candidate and same instrumentation; not full Release/sanitizer/Elo acceptance',
          'build_method': 'Recompile changed search.cpp only; replace its archive member; relink exact frozen UCI object with same flags. All other members byte-identical.',
          'source_hashes_before': source_before,
          'original_inputs_before': {str(p): sha(p) for p in original_inputs}, 'steps': [], 'status': 'RUNNING'}

def save():
    (OUT / 'commands.json').write_text(json.dumps(report, indent=2) + '\n')

def run(label, command, stdin=None, timeout=180, cwd=BUILD):
    if stdin is not None:
        (OUT / (label + '.stdin')).write_bytes(stdin)
    start = time.monotonic()
    with (OUT / (label + '.stdout')).open('xb') as stdout, (OUT / (label + '.stderr')).open('xb') as stderr:
        proc = subprocess.run(command, input=stdin, stdout=stdout, stderr=stderr,
                              env=ENV, cwd=cwd, timeout=timeout)
    row = {'label': label, 'command': command, 'cwd': str(cwd), 'exit_code': proc.returncode,
           'timeout_seconds': timeout, 'elapsed_seconds_diagnostic_only': time.monotonic() - start,
           'stdout_sha256': sha(OUT / (label + '.stdout')),
           'stderr_sha256': sha(OUT / (label + '.stderr'))}
    report['steps'].append(row)
    save()
    print(json.dumps(row), flush=True)
    assert proc.returncode == 0, (label, proc.returncode)

save()
try:
    commands = json.loads((BASE / 'compile_commands.json').read_text())
    cmd = shlex.split(next(row['command'] for row in commands if row['file'].endswith('/search.cpp')))
    cmd = [('-I' + str(SOURCE / 'include')) if arg.startswith('-I') else arg for arg in cmd]
    cmd[cmd.index('-o') + 1] = str(BUILD / 'search.cpp.o')
    cmd[cmd.index('-c') + 1] = str(SOURCE / 'src/search.cpp')
    run('compile-search', cmd)
    shutil.copyfile(BASE / 'libforge_core.a', BUILD / 'libforge_core.a')
    run('replace-search-member', ['ar', 'r', str(BUILD / 'libforge_core.a'), str(BUILD / 'search.cpp.o')])
    names = subprocess.check_output(['ar', 't', str(BASE / 'libforge_core.a')], text=True).splitlines()
    member_rows = {}
    for name in names:
        left = subprocess.check_output(['ar', 'p', str(BASE / 'libforge_core.a'), name])
        right = subprocess.check_output(['ar', 'p', str(BUILD / 'libforge_core.a'), name])
        member_rows[name] = {'baseline_sha256': hashlib.sha256(left).hexdigest(),
                             'candidate_sha256': hashlib.sha256(right).hexdigest(),
                             'identical': left == right}
        assert (left == right) == (name != 'search.cpp.o'), name
    report['core_members'] = member_rows
    cmd = shlex.split((BASE / 'CMakeFiles/forge.dir/link.txt').read_text())
    cmd = [str(BASE / arg) if arg == 'CMakeFiles/forge.dir/src/uci.cpp.o' else arg for arg in cmd]
    run('link', cmd)
    report['diagnostic_binary_sha256'] = sha(BUILD / 'forge')
    report['diagnostic_core_sha256'] = sha(BUILD / 'libforge_core.a')
    run('diagnostic-bench11', [str(BUILD / 'forge')], b'setoption name OwnBook value false\nbench 11\nquit\n', timeout=30)
    text = (OUT / 'diagnostic-bench11.stdout').read_text()
    report['bench11_nodes'] = int(re.search(r'bench depth 11 nodes (\d+)', text).group(1))
    report['bench11_baseline_nodes'] = 419798
    report['bench11_same_nodes'] = report['bench11_nodes'] == 419798
    data = (OUT / 'diagnostic-bench11.stderr').read_text()
    traces = [json.loads(line.removeprefix('DE_TRACE ')) for line in data.splitlines() if line.startswith('DE_TRACE ')]
    summaries = [json.loads(line.removeprefix('DE_SUMMARY ')) for line in data.splitlines() if line.startswith('DE_SUMMARY ')]
    assert len(summaries) == 8, len(summaries)
    (OUT / 'traces.json').write_text(json.dumps(traces, indent=2) + '\n')
    (OUT / 'summaries.json').write_text(json.dumps(summaries, indent=2) + '\n')
    report['summary_totals'] = {key: sum(row[key] for row in summaries) for key in summaries[0]}
    mismatch_keys = ['same_ply_changed', 'single_parent_mismatch', 'eligibility_mismatch',
                     'actual_vs_true_path_mismatch', 'null_parent_path_mismatch',
                     'probcut_parent_path_mismatch', 'incoming_parent_path_mismatch']
    assert all(report['summary_totals'][key] == 0 for key in mismatch_keys), report['summary_totals']
    after = {str(p.relative_to(SOURCE)): sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()}
    assert source_before == after
    original_after = {str(p): sha(p) for p in original_inputs}
    assert report['original_inputs_before'] == original_after
    assert report['diagnostic_binary_sha256'] == sha(BUILD / 'forge')
    assert report['diagnostic_core_sha256'] == sha(BUILD / 'libforge_core.a')
    report.update(status='PASS', inputs_unchanged=True, source_hashes_after=after,
                  original_inputs_after=original_after,
                  completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save()
    print(json.dumps({'status': 'PASS', 'summary_totals': report['summary_totals'], 'bench11_nodes': report['bench11_nodes']}), flush=True)
except Exception as error:
    report.update(status='FAILED_OR_INCOMPLETE', error=repr(error))
    save()
    raise
