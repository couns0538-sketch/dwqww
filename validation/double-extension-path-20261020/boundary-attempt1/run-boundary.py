#!/usr/bin/env python3
"""Synthetic ancestral-budget boundary coverage using actual unretuned search."""
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

HERE = Path(__file__).resolve().parent
BASE = Path('/workspace/.cloud-setup/forge-clock-contract-release')
REPO = HERE.parents[2]
ENV = os.environ.copy()
ENV['PYTHONDONTWRITEBYTECODE'] = '1'
ENV.pop('FORGE_EXTENSION_ANCESTRAL_SEED', None)
meta = json.loads((HERE / 'SOURCE-PROVENANCE.json').read_text())
report = {'status': 'RUNNING', 'steps': [], 'cases': {},
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'scope': 'Synthetic ancestral-state coverage, not a natural-root overflow, full-engine validation, speed or Elo claim.',
          'runtime_budget_seconds': 60, 'runtime_used_seconds': 0,
          'seed_mechanism': 'Diagnostic env seeds root parent sentinel and independent shadow. Unset env retains zero. No tuning parameter changes.'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save():
    (HERE / 'commands.json').write_text(json.dumps(report, indent=2) + '\n')

originals = [BASE / 'forge', BASE / 'libforge_core.a', BASE / 'compile_commands.json',
             BASE / 'CMakeFiles/forge.dir/src/uci.cpp.o', BASE / 'CMakeFiles/forge.dir/link.txt']
report['originals_before'] = {str(p): sha(p) for p in originals}
known = json.loads((REPO / 'validation/upstream-clock-reconcile-20261020/frozen-release-attempt1/summary.json').read_text())
assert known['status'] == 'PASS'
assert sha(BASE / 'libforge_core.a') == known['binary_sha256_after']['libforge_core.a']
assert sha(BASE / 'forge') == known['binary_sha256_after']['forge']
save()

def run(label, cmd, cwd, stdin=None, env=ENV, timeout=180):
    if stdin is not None:
        (HERE / (label + '.stdin')).write_bytes(stdin)
    start = time.monotonic()
    with (HERE / (label + '.stdout')).open('xb') as out, (HERE / (label + '.stderr')).open('xb') as err:
        r = subprocess.run(cmd, cwd=cwd, env=env, input=stdin, stdout=out, stderr=err, timeout=timeout)
    elapsed = time.monotonic() - start
    report['steps'].append({'label': label, 'command': cmd, 'cwd': str(cwd),
                            'exit_code': r.returncode, 'timeout_seconds': timeout,
                            'elapsed_seconds_diagnostic_only': elapsed,
                            'stdout_sha256': sha(HERE / (label + '.stdout')),
                            'stderr_sha256': sha(HERE / (label + '.stderr'))})
    save()
    assert r.returncode == 0, (label, r.returncode)
    return elapsed

try:
    sources = {}
    builds = {}
    for label in ['baseline', 'proposal']:
        source = Path(meta['variants'][label]['source_export'])
        assert sha(source / 'src/search.cpp') == meta['variants'][label]['boundary_search_sha256']
        sources[label] = {str(p.relative_to(source)): sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
        build = Path('/workspace/.cloud-setup/double-extension-boundary-' + label + '-build')
        build.mkdir(exist_ok=False)
        (build / 'CMakeFiles/forge.dir').mkdir(parents=True)
        builds[label] = build
        flags = json.loads((BASE / 'compile_commands.json').read_text())
        cmd = shlex.split(next(row['command'] for row in flags if row['file'].endswith('/search.cpp')))
        cmd = [('-I' + str(source / 'include')) if arg.startswith('-I') else arg for arg in cmd]
        cmd[cmd.index('-o') + 1] = str(build / 'search.cpp.o')
        cmd[cmd.index('-c') + 1] = str(source / 'src/search.cpp')
        run(label + '-compile', cmd, build)
        shutil.copyfile(BASE / 'libforge_core.a', build / 'libforge_core.a')
        run(label + '-core', ['ar', 'r', str(build / 'libforge_core.a'), str(build / 'search.cpp.o')], build)
        members = subprocess.check_output(['ar', 't', str(BASE / 'libforge_core.a')], text=True).splitlines()
        member_rows = {}
        for name in members:
            a = subprocess.check_output(['ar', 'p', str(BASE / 'libforge_core.a'), name])
            b = subprocess.check_output(['ar', 'p', str(build / 'libforge_core.a'), name])
            assert (a == b) == (name != 'search.cpp.o'), name
            member_rows[name] = {'baseline_sha256': hashlib.sha256(a).hexdigest(),
                                 'variant_sha256': hashlib.sha256(b).hexdigest(), 'identical': a == b}
        report[label + '_core_members'] = member_rows
        cmd = shlex.split((BASE / 'CMakeFiles/forge.dir/link.txt').read_text())
        cmd = [str(BASE / arg) if arg == 'CMakeFiles/forge.dir/src/uci.cpp.o' else arg for arg in cmd]
        run(label + '-link', cmd, build)
        report[label + '_binary_sha256'] = sha(build / 'forge')
        report[label + '_core_sha256'] = sha(build / 'libforge_core.a')
        print('Built ' + label + '; six unchanged core members verified', flush=True)
    fields = ['children', 'single_extensions', 'double_extensions', 'singular_attempts',
              'same_ply_before', 'same_ply_changed', 'single_parent_mismatch', 'eligibility_mismatch',
              'actual_vs_true_path_mismatch', 'null_parent_path_mismatch', 'probcut_parent_path_mismatch',
              'incoming_parent_path_mismatch', 'true_path_limit_breaches']
    for label in ['baseline', 'proposal']:
        for seed in [0, 6, 7]:
            case = f'{label}-seed{seed}'
            env = ENV.copy()
            if seed:
                env['FORGE_EXTENSION_ANCESTRAL_SEED'] = str(seed)
            remaining = report['runtime_budget_seconds'] - report['runtime_used_seconds']
            assert remaining > 0
            elapsed = run(case, [str(builds[label] / 'forge')], builds[label],
                          b'setoption name OwnBook value false\nbench 11\nquit\n', env,
                          timeout=min(20, remaining))
            report['runtime_used_seconds'] += elapsed
            stdout = (HERE / (case + '.stdout')).read_text()
            nodes = int(re.search(r'bench depth 11 nodes (\d+)', stdout).group(1))
            stderr = (HERE / (case + '.stderr')).read_text()
            traces = [json.loads(line.removeprefix('DE_TRACE ')) for line in stderr.splitlines() if line.startswith('DE_TRACE ')]
            summaries = [json.loads(line.removeprefix('DE_SUMMARY ')) for line in stderr.splitlines() if line.startswith('DE_SUMMARY ')]
            assert len(summaries) == 8
            assert all(row['ancestral_seed'] == seed for row in summaries)
            totals = {key: sum(row[key] for row in summaries) for key in fields}
            row = {'seed': seed, 'env_seed_unset': seed == 0, 'bench11_nodes': nodes,
                   'summary_totals': totals, 'max_true_path': max(s['max_true_path'] for s in summaries),
                   'max_actual_path': max(s['max_actual_path'] for s in summaries),
                   'variant': label, 'engine_exit_code': 0}
            report['cases'][case] = row
            (HERE / (case + '-traces.json')).write_text(json.dumps(traces, indent=2) + '\n')
            (HERE / (case + '-summaries.json')).write_text(json.dumps(summaries, indent=2) + '\n')
            save()
            print(json.dumps({'case': case, **row}), flush=True)
    mismatch_fields = ['same_ply_changed', 'single_parent_mismatch', 'eligibility_mismatch',
                       'actual_vs_true_path_mismatch', 'null_parent_path_mismatch',
                       'probcut_parent_path_mismatch', 'incoming_parent_path_mismatch', 'true_path_limit_breaches']
    for label in ['baseline', 'proposal']:
        assert report['cases'][label + '-seed0']['bench11_nodes'] == 419798
    for seed in [6, 7]:
        row = report['cases'][f'proposal-seed{seed}']
        assert row['max_true_path'] == 7 and row['max_actual_path'] == 7
        assert all(row['summary_totals'][key] == 0 for key in mismatch_fields)
        assert (row['summary_totals']['double_extensions'] > 0) == (seed == 6)
    assert report['cases']['baseline-seed7']['summary_totals']['true_path_limit_breaches'] > 0
    assert report['runtime_used_seconds'] <= report['runtime_budget_seconds']
    for label, before in sources.items():
        source = Path(meta['variants'][label]['source_export'])
        after = {str(p.relative_to(source)): sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
        assert before == after
        assert report[label + '_binary_sha256'] == sha(builds[label] / 'forge')
        assert report[label + '_core_sha256'] == sha(builds[label] / 'libforge_core.a')
    after = {str(p): sha(p) for p in originals}
    assert after == report['originals_before']
    report.update(status='PASS', source_hashes_before_and_after=sources,
                  originals_after=after, inputs_unchanged=True,
                  completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save()
    print('PASS synthetic6/7 boundary coverage; no natural-root or strength claim', flush=True)
except Exception as error:
    report.update(status='FAILED_OR_INCOMPLETE', error=repr(error))
    save()
    raise
