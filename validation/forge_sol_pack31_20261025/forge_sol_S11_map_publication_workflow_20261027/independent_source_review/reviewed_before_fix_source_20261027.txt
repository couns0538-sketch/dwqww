"""Stage frozen S11 data through its path map, without copying original streams.

Only Git data-object compression changes representation. Source reads require
O_NOATIME and O_NOFOLLOW, and the complete recorded source metadata must match.
The index is updated once after every source has passed its frozen byte checks.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import resource
import stat
import subprocess
import time

REPO = Path('/workspace/dwqww')
STORE = Path('/tmp/forge_sol_published_data_git_objects_20261026')
MAP_SHA = 'b5ddfd06cf9a615a221972e7c7a895b6807c4d14baec84af0d9764ef580f2b0b'
PREFIX = 'validation/forge_sol_pack31_20261025/forge_sol_S11_closed_native_parity_20261027/'


def meta(s):
    return dict(bytes=s.st_size, mode=oct(stat.S_IMODE(s.st_mode)), uid=s.st_uid,
                gid=s.st_gid, dev=s.st_dev, inode=s.st_ino, nlink=s.st_nlink,
                atime_ns=s.st_atime_ns, mtime_ns=s.st_mtime_ns,
                ctime_ns=s.st_ctime_ns, blocks=s.st_blocks)


def git(argv, *, data=None, external=False):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    if external:
        env.update(GIT_OBJECT_DIRECTORY=str(STORE),
                   GIT_ALTERNATE_OBJECT_DIRECTORIES=str(REPO / '.git/objects'))
    p = subprocess.run(['git', '-c', 'gc.auto=0', '-c', 'core.compression=1', *argv],
                       cwd=REPO, env=env, input=data,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(f'Git {argv[0]} exited {p.returncode}: {p.stderr.decode(errors="replace")}')
    return p.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', type=Path, required=True)
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--execute', action='store_true')
    a = ap.parse_args()
    if not a.execute or a.receipt.exists():
        ap.error('explicit execution and a new receipt are required')
    raw = a.map.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MAP_SHA:
        ap.error('frozen map SHA mismatch')
    plan = json.loads(raw)
    rows = plan['path_map']
    if plan['status'] != 'SEALED_LOCAL_NOT_PUBLISHED' or len(rows) != 797:
        ap.error('unexpected frozen map schema/count')
    targets = set()
    for row in rows:
        rel = row['git_target_relpath']
        path = PurePosixPath(rel)
        if (not rel.startswith(PREFIX) or path.is_absolute() or '..' in path.parts
                or any(c in rel for c in '\n\r\t\x00') or rel in targets):
            ap.error('unsafe or duplicate target')
        targets.add(rel)
        if row['type'] not in ('json', 'text_data', 'gzip_original_capture'):
            ap.error('unsupported data type')
        if row['bytes'] > 524288 and path.suffix != '.gz':
            ap.error('unexpected large non-gzip input')
        if (REPO / rel).exists():
            ap.error('target exists before staging')
    if os.statvfs(STORE).f_bavail * os.statvfs(STORE).f_frsize < plan['counts']['unique_data_bytes'] + 256 * 1048576:
        ap.error('insufficient conservative data-object capacity')
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
    result = dict(schema='forge.S11.map_staging.v1', status='IN_PROGRESS',
                  map_path=str(a.map), map_sha256=MAP_SHA, started=time.time(),
                  original_read_policy='O_NOATIME|O_NOFOLLOW; no fallback',
                  representation='normal Git files; large data objects in local alternate store',
                  files=[], index_updated=False)
    seen = set()
    try:
        for number, row in enumerate(rows, 1):
            source = Path(row['source_path'])
            fd = os.open(source, os.O_RDONLY | os.O_NOATIME | os.O_NOFOLLOW)
            with os.fdopen(fd, 'rb') as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or meta(before) != row['metadata']:
                    raise ValueError('source metadata drift: ' + str(source))
                body = stream.read(row['bytes'] + 1)
                if len(body) != row['bytes'] or hashlib.sha256(body).hexdigest() != row['sha256']:
                    raise ValueError('source byte drift: ' + str(source))
                if body[:4] == b'\x7fELF' or body[:2] == b'MZ':
                    raise ValueError('compiled payload prohibited: ' + str(source))
                if meta(os.fstat(stream.fileno())) != row['metadata']:
                    raise ValueError('source changed while read: ' + str(source))
            oid = hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()
            large = len(body) > 524288
            if large:
                if oid not in seen:
                    actual = git(['hash-object', '-w', '--stdin'], data=body, external=True).decode().strip()
                    if actual != oid:
                        raise ValueError('Git blob identity mismatch')
                    seen.add(oid)
            else:
                dest = REPO / row['git_target_relpath']
                dest.parent.mkdir(parents=True, exist_ok=True)
                fs = os.statvfs(dest.parent)
                if fs.f_bavail * fs.f_frsize < len(body) + 8 * 1048576:
                    raise OSError('primary metadata reserve exhausted')
                with dest.open('xb') as target:
                    target.write(body)
                dest.chmod(0o644)
                actual = git(['hash-object', '-w', '--stdin'], data=body).decode().strip()
                if actual != oid:
                    raise ValueError('small Git blob identity mismatch')
            result['files'].append(dict(source=str(source), path=row['git_target_relpath'],
                                        bytes=len(body), sha256=row['sha256'], git_blob_oid=oid,
                                        external_data=large, metadata_unchanged=True))
            if number % 50 == 0:
                print(f'Frozen original sources verified/staged {number}/797', flush=True)
        index = ''.join(f"100644 {x['git_blob_oid']}\t{x['path']}\n" for x in result['files']).encode()
        git(['update-index', '--index-info'], data=index)
        sparse = ''.join(x['path'] + '\n' for x in result['files'] if x['external_data']).encode()
        git(['update-index', '--skip-worktree', '--stdin'], data=sparse)
        result['index_updated'] = True
        actual = {}
        for line in git(['ls-files', '--stage', '--', PREFIX.rstrip('/')]).decode().splitlines():
            head, path = line.split('\t', 1)
            mode, oid, stage = head.split()
            actual[path] = (mode, oid, stage)
        for row in result['files']:
            if actual.get(row['path']) != ('100644', row['git_blob_oid'], '0'):
                raise ValueError('final index binding mismatch: ' + row['path'])
        result.update(status='PASS_STAGED_NOT_COMMITTED', unique_large_blob_writes=len(seen),
                      source_stream_copies=0, source_links_changed=0)
    except BaseException as error:
        result.update(status='FAIL_PRESERVED_NO_AUTORETRY', error=type(error).__name__ + ': ' + str(error))
        raise
    finally:
        result['elapsed_seconds'] = time.time() - result['started']
        with a.receipt.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(result['status'], len(result['files']), 'paths;', len(seen), 'unique large data blobs', flush=True)


if __name__ == '__main__':
    main()
