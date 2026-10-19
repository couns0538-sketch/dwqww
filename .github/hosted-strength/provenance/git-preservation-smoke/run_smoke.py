#!/usr/bin/env python3
"""Local-only reproduction of the workflow's orphan-branch index cleanup."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / 'commands'
LOGS.mkdir(exist_ok=True)
REAL_GIT = shutil.which('git', path='/usr/bin:/bin')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(argv, cwd, env=None):
    ident = str(uuid.uuid4())
    started = time.time_ns()
    result = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True)
    record = {'argv': argv, 'cwd': str(cwd), 'started_wall_ns': started,
              'finished_wall_ns': time.time_ns(), 'exit_code': result.returncode,
              'stdout': result.stdout, 'stderr': result.stderr}
    (LOGS / (ident + '.json')).write_text(json.dumps(record, indent=2) + '\n')
    (LOGS / (ident + '.stdout')).write_text(result.stdout)
    (LOGS / (ident + '.stderr')).write_text(result.stderr)
    return result


if len(sys.argv) > 1 and sys.argv[1] == '--record-git':
    completed = run([REAL_GIT, *sys.argv[2:]], Path.cwd())
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    raise SystemExit(completed.returncode)

workflow = ROOT.parent.parent / 'forge-hosted-strength.yml'
wrapper = ROOT.parent.parent / 'run_hosted.py'
inputs = {str(path): digest(path) for path in (Path(__file__), workflow, wrapper)}
repo = ROOT / 'throwaway-repo'
repo.mkdir()
git = lambda *args: run([REAL_GIT, *args], repo)
assert git('init', '-b', 'main').returncode == 0
(repo / 'source-marker.txt').write_text('Seed source marker; never an engine source.\n')
assert git('add', 'source-marker.txt').returncode == 0
assert git('-c', 'user.name=Preservation smoke', '-c', 'user.email=smoke@example.invalid',
           'commit', '-m', 'Seed throwaway source branch').returncode == 0
source_head = git('rev-parse', 'main').stdout.strip()
source_tree = git('ls-tree', '-r', '--name-only', 'main').stdout
source_marker = git('show', 'main:source-marker.txt').stdout
fixture = repo / 'hosted-results'
fixture.mkdir()
(fixture / 'games.pgn').write_text('[Event "Dummy preservation fixture"]\n[Result "*"]\n\n*\n')
(fixture / 'fastchess.log').write_text('Dummy preservation fixture; no engines executed.\n')
(fixture / 'summary.json').write_text('{"fixture": true, "engine_execution": false}\n')
fixture_hashes = {p.name: digest(p) for p in fixture.iterdir()}
shimdir = ROOT / 'bin'
shimdir.mkdir()
shim = shimdir / 'git'
shim.write_text('#!/bin/sh\nexec "$SMOKE_PYTHON" "$SMOKE_DRIVER" --record-git "$@"\n')
shim.chmod(0o700)
env = dict(os.environ, PATH=str(shimdir) + os.pathsep + os.environ['PATH'],
           SMOKE_PYTHON=sys.executable, SMOKE_DRIVER=str(Path(__file__).resolve()),
           PYTHONDONTWRITEBYTECODE='1')
original = ('set -euo pipefail\n'
            'git switch --orphan results/original\n'
            'git rm -rf --cached .\n'
            'git add -f hosted-results\n'
            'git -c user.name="Preservation smoke" -c user.email=smoke@example.invalid commit -m original\n')
failed = run(['bash', '-c', original], repo, env)
assert failed.returncode != 0
assert "pathspec '.' did not match any files" in failed.stderr
assert git('ls-files').stdout == ''
assert git('rev-parse', '--verify', 'refs/heads/results/original').returncode != 0
assert git('switch', 'main').returncode == 0
fixed = ('set -euo pipefail\n'
         'git switch --orphan results/fixed\n'
         'git rm -rf --cached --ignore-unmatch .\n'
         'git add -f hosted-results\n'
         'git -c user.name="Preservation smoke" -c user.email=smoke@example.invalid commit -m fixed\n')
passed = run(['bash', '-c', fixed], repo, env)
assert passed.returncode == 0
fixed_head = git('rev-parse', 'HEAD').stdout.strip()
fixed_tree = git('ls-tree', '-r', '--name-only', 'HEAD').stdout.splitlines()
expected = sorted('hosted-results/' + name for name in fixture_hashes)
assert sorted(fixed_tree) == expected
assert git('rev-parse', 'main').stdout.strip() == source_head
assert git('ls-tree', '-r', '--name-only', 'main').stdout == source_tree
assert git('show', 'main:source-marker.txt').stdout == source_marker
assert {p.name: digest(p) for p in fixture.iterdir()} == fixture_hashes
assert all(digest(path) == value for path, value in inputs.items())
records = sorted((json.loads(p.read_text()) for p in LOGS.glob('*.json')),
                 key=lambda value: value['started_wall_ns'])
(ROOT / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
result = {'status': 'passed', 'network_used': False, 'engine_execution': False,
          'scope': 'Throwaway repository only; user repository and workflow unchanged',
          'source_sha256': inputs[str(Path(__file__))], 'input_sha256': inputs,
          'original_step_exit_code': failed.returncode, 'original_index_empty': True,
          'original_step_stopped_before_add_commit': True,
          'fixed_step_exit_code': passed.returncode, 'source_branch_unchanged': True,
          'source_branch_commit': source_head, 'results_commit': fixed_head,
          'results_tree': fixed_tree, 'fixture_sha256': fixture_hashes,
          'command_count': len(records), 'commands_sha256': digest(ROOT / 'commands.json')}
(ROOT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
