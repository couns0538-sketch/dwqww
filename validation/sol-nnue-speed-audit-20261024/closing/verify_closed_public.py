"""Verify immutable public raw files against actual local Git blobs; no API calls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import quote

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--commit', required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
repo = '/workspace/dwqww'
base = '1ab50b2dd64d9b2f752f7f1285f6968cad2fd792'
branch = 'forge/sol-nnue-speed-audit-20261024'


def git(*args):
    return subprocess.check_output(['git', '-C', repo, *args])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


paths = git('diff', '--name-only', base, a.commit).decode().splitlines()
assert paths and len(paths) == len(set(paths))
assert not any(line.startswith('-\t') for line in
               git('diff', '--numstat', base, a.commit).decode().splitlines())
assert git('diff', '--name-only', base, a.commit, '--', 'tests', 'include', 'CMakeLists.txt') == b''
assert git('diff', '--name-only', base, a.commit, '--', 'src').decode().splitlines() == [
    'src/nnue.cpp', 'src/nnue_weights.inc', 'src/search.cpp']
remote = git('ls-remote', 'origin', 'refs/heads/' + branch)
(a.out / 'remote-before.txt').write_bytes(remote)
assert remote.decode().split()[0] == a.commit


def fetch(path):
    expected = git('show', a.commit + ':' + path)
    expected.decode('utf-8')
    dest = a.out / 'http' / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    argv = ['curl', '--silent', '--show-error', '--fail-with-body', '--location',
            '--connect-timeout', '15', '--max-time', '60', '--dump-header', str(dest) + '.headers',
            '--output', str(dest), '--write-out', '%{json}',
            'https://raw.githubusercontent.com/couns0538-sketch/dwqww/' + a.commit + '/' + quote(path, safe='/')]
    done = subprocess.run(argv, capture_output=True)
    Path(str(dest) + '.curl.json').write_bytes(done.stdout)
    Path(str(dest) + '.stderr').write_bytes(done.stderr)
    body = dest.read_bytes() if dest.exists() else b''
    try:
        status = json.loads(done.stdout).get('http_code')
    except (ValueError, AttributeError):
        status = None
    return {'path': path, 'argv': argv, 'curl_exit': done.returncode,
            'http_status': status, 'git_sha256': sha(expected), 'public_sha256': sha(body),
            'bytes': len(body), 'byte_equal': expected == body,
            'pass': done.returncode == 0 and status == 200 and expected == body}


record = {'target_commit': a.commit, 'base': base, 'branch': branch,
          'started_utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'All changed UTF8 source/evidence files; no binary or API downloads',
          'HTTP_attempts_per_file': 1, 'concurrency': 4}
with ThreadPoolExecutor(max_workers=4) as pool:
    record['files'] = list(pool.map(fetch, paths))
after = git('ls-remote', 'origin', 'refs/heads/' + branch)
(a.out / 'remote-after.txt').write_bytes(after)
record.update(closed_utc=datetime.now(timezone.utc).isoformat(), files_checked=len(paths),
              remote_unchanged=after == remote,
              status='PASS' if all(row['pass'] for row in record['files']) and after == remote else 'FAIL')
(a.out / 'RESULT.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: record[key] for key in ['status', 'target_commit', 'files_checked', 'remote_unchanged']}))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
