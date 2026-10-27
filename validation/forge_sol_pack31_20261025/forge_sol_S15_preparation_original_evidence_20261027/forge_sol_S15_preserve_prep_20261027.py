#!/usr/bin/env python3
"""Preserve the exact closed S15 prep evidence; never mutate the input tree."""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tarfile
import time

if not __debug__:
    raise RuntimeError('Run without -O/PYTHONOPTIMIZE')

SOURCE = Path('/tmp/forge_sol_S15_prep_20261027')
DEST = Path('/tmp/forge_sol_S15_prep_evidence_preservation_20261027')
PREFIX = 'forge_sol_S15_prep_evidence_20261027'
ARCHIVE = DEST / (PREFIX + '.tar.gz')
EXPECTED_COUNT = 121
EXPECTED_BYTES = 801556

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write_json(name, value):
    path = DEST / name
    data = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    with path.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    return path

def safe_relative(name):
    p = PurePosixPath(name)
    require(bool(name) and not p.is_absolute(), 'empty/absolute archive path')
    require(all(x not in ('', '.', '..') for x in p.parts), 'unsafe archive path')
    require(p.as_posix() == name, 'noncanonical archive path')
    return name

def read_regular(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, 'O_NOATIME', 0))
    with os.fdopen(fd, 'rb') as f:
        s = os.fstat(f.fileno())
        require(stat.S_ISREG(s.st_mode), 'nonregular source')
        data = f.read()
        require(os.fstat(f.fileno()) == s, 'source stat changed while reading')
    return s, data

def inventory(root, source=False):
    require(root.is_dir() and not root.is_symlink(), 'unsafe inventory root')
    files = []
    dirs = []
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        for name in sorted(dirnames + filenames):
            p = Path(current) / name
            s = p.lstat()
            relative = safe_relative(p.relative_to(root).as_posix())
            require(not stat.S_ISLNK(s.st_mode), 'symlink input')
            if stat.S_ISDIR(s.st_mode):
                dirs.append({'relative': relative, 'mode': stat.S_IMODE(s.st_mode),
                             'mtime_ns': s.st_mtime_ns, 'ctime_ns': s.st_ctime_ns,
                             'inode': s.st_ino, 'device': s.st_dev})
            else:
                require(stat.S_ISREG(s.st_mode), 'special input file')
                s, data = read_regular(p)
                if source:
                    require(not data.startswith((b'\x7fELF', b'MZ', b'!<arch>\n')),
                            'native binary/archive payload')
                    require(p.suffix.lower() not in ('.o', '.a', '.so', '.exe', '.dll', '.obj', '.lib'),
                            'native payload suffix')
                files.append({'absolute': str(p), 'relative': relative,
                              'sha256': digest(data), 'bytes': len(data),
                              'mode': stat.S_IMODE(s.st_mode),
                              'mode_octal': format(stat.S_IMODE(s.st_mode), '04o'),
                              'mtime_ns': s.st_mtime_ns, 'ctime_ns': s.st_ctime_ns,
                              'inode': s.st_ino, 'device': s.st_dev, 'nlink': s.st_nlink})
    return {'root': str(root), 'files': sorted(files, key=lambda x: x['relative']),
            'directories': sorted(dirs, key=lambda x: x['relative'])}

def content_map(inv):
    return {f['relative']: (f['sha256'], f['bytes'], f['mode']) for f in inv['files']}

def canonical_tar(inv):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.GNU_FORMAT) as tf:
        for entry in inv['files']:
            s, data = read_regular(SOURCE / entry['relative'])
            require(digest(data) == entry['sha256'] and len(data) == entry['bytes']
                    and stat.S_IMODE(s.st_mode) == entry['mode'], 'input drift before tar')
            member = tarfile.TarInfo(entry['relative'])
            member.size = len(data)
            member.mode = entry['mode']
            member.mtime = 0
            member.uid = member.gid = 0
            member.uname = member.gname = ''
            tf.addfile(member, io.BytesIO(data))
    return output.getvalue()

def gzip6(data):
    output = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=output, compresslevel=6, mtime=0) as f:
        f.write(data)
    return output.getvalue()

def verify_members(tf, inv):
    members = tf.getmembers()
    require(len(members) == EXPECTED_COUNT, 'wrong tar member count')
    require(len({m.name for m in members}) == len(members), 'duplicate tar member')
    expected = content_map(inv)
    require({safe_relative(m.name) for m in members} == set(expected), 'tar path set mismatch')
    for member in members:
        require(member.isreg() and not member.issym() and not member.islnk(), 'nonregular tar member')
        data = tf.extractfile(member).read()
        require((digest(data), member.size, member.mode) == expected[member.name], 'member mismatch')
        require(member.uid == member.gid == member.mtime == 0, 'nondeterministic metadata')
    return members

def run_gnu(argv, tag):
    stdout = DEST / (PREFIX + '_' + tag + '.stdout')
    stderr = DEST / (PREFIX + '_' + tag + '.stderr')
    start = time.time_ns()
    def clean_umask():
        os.umask(0)
    with stdout.open('xb') as out, stderr.open('xb') as err:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                start_new_session=True, preexec_fn=clean_umask)
        rc = proc.wait(timeout=30)
    commands.append({'argv': argv, 'pid': proc.pid, 'returncode': rc,
                     'started_ns': start, 'closed_ns': time.time_ns(),
                     'stdout': str(stdout), 'stderr': str(stderr), 'umask': '0000'})
    require(rc == 0, 'GNU command failed')

require(os.sched_getaffinity(0) == {4}, 'must use CPU 4 only')
require(os.getpriority(os.PRIO_PROCESS, 0) == 19, 'must use nice19')
started = time.time_ns()
commands = []
before = inventory(SOURCE, source=True)
require(len(before['files']) == EXPECTED_COUNT, 'source count is not exactly121')
require(sum(f['bytes'] for f in before['files']) == EXPECTED_BYTES, 'source size changed')
original_map = write_json(PREFIX + '_original_file_map.json', before)
tar_bytes = canonical_tar(before)
archive_bytes = gzip6(tar_bytes)
require(archive_bytes == gzip6(canonical_tar(before)), 'deterministic rebuild differs')
with ARCHIVE.open('xb') as f:
    f.write(archive_bytes)
    f.flush()
    os.fsync(f.fileno())

# Python decoder: independent archive read, validate every member before extracting.
python_out = DEST / (PREFIX + '_python_roundtrip')
python_out.mkdir(mode=0o700)
with tarfile.open(ARCHIVE, mode='r:gz') as tf:
    members = verify_members(tf, before)
    for member in members:
        target = python_out / member.name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(tf.extractfile(member).read())
        target.chmod(member.mode)
require(content_map(inventory(python_out)) == content_map(before), 'Python roundtrip mismatch')
write_json(PREFIX + '_python_roundtrip_file_map.json', inventory(python_out))
write_json(PREFIX + '_python_roundtrip.json', {'status': 'PASS', 'regular_files': EXPECTED_COUNT,
           'sha256_size_mode_all_match': True, 'safe_unique_regular_members': True,
           'deterministic_rebuild_byte_identical': True, 'archive_sha256': digest(archive_bytes)})

# GNU tar decoder: separate newly owned extraction root, --same-permissions and umask0000.
gnu_out = DEST / (PREFIX + '_gnu_roundtrip')
gnu_out.mkdir(mode=0o700)
run_gnu(['/usr/bin/tar', '--version'], 'gnu_tar_version')
run_gnu(['/usr/bin/gzip', '--test', str(ARCHIVE)], 'gnu_gzip_test')
run_gnu(['/usr/bin/tar', '--list', '--gzip', '--file', str(ARCHIVE)], 'gnu_tar_list')
run_gnu(['/usr/bin/tar', '--extract', '--gzip', '--file', str(ARCHIVE),
         '--directory', str(gnu_out), '--same-permissions', '--no-same-owner',
         '--keep-old-files'], 'gnu_tar_extract')
require(content_map(inventory(gnu_out)) == content_map(before), 'GNU roundtrip mismatch')
write_json(PREFIX + '_gnu_roundtrip_file_map.json', inventory(gnu_out))
write_json(PREFIX + '_gnu_roundtrip.json', {'status': 'PASS', 'regular_files': EXPECTED_COUNT,
           'sha256_size_mode_all_match': True, 'safe_unique_regular_members': True,
           'GNU_tar_same_permissions': True, 'umask': '0000', 'archive_sha256': digest(archive_bytes)})
after = inventory(SOURCE, source=True)
require(before == after, 'original input tree changed')
# Remove only this script's redundant, successfully verified extraction copies.
# The archive, original inputs, per-file decoded maps and raw decoder logs remain.
for owned in (python_out, gnu_out):
    verified = inventory(owned)
    require(content_map(verified) == content_map(before), 'owned extraction drift before cleanup')
    for entry in verified['files']:
        (owned / entry['relative']).unlink()
    for entry in sorted(verified['directories'], key=lambda x: len(Path(x['relative']).parts), reverse=True):
        (owned / entry['relative']).rmdir()
    owned.rmdir()
write_json(PREFIX + '_commands.json', {'status': 'CLOSED', 'commands': commands,
           'launcher': ['taskset', '-c', '4', 'nice', '-n', '19', 'python3', '-B', str(Path(__file__))]})
receipt = write_json(PREFIX + '_receipt.json', {
    'status': 'PASS_CLOSED', 'started_ns': started, 'closed_ns': time.time_ns(),
    'scope': 'data-only preservation of exact original S15 prep evidence',
    'original_files': EXPECTED_COUNT, 'original_bytes': EXPECTED_BYTES,
    'original_directories': len(before['directories']),
    'original_map_sha256': digest(original_map.read_bytes()),
    'archive': str(ARCHIVE), 'archive_sha256': digest(archive_bytes),
    'archive_bytes': len(archive_bytes), 'archive_members': EXPECTED_COUNT,
    'gzip_level': 6, 'gzip_mtime': 0, 'tar_mtime': 0, 'tar_format': 'GNU',
    'input_before_after_exact': True, 'input_bytes_size_modes_mtime_ctime_inode_nlink_unchanged': True,
    'links_or_special_members': 0, 'native_payloads': 0,
    'python_roundtrip_all_files_bytes_size_mode': 'PASS',
    'GNU_tar_roundtrip_all_files_bytes_size_mode': 'PASS',
    'deterministic_rebuild': 'PASS', 'cpu_affinity': [4], 'nice': 19,
    'verified_own_temporary_extractions_removed': True,
    'engine_compiler_Git_network_actions': False,
    'publication': 'NOT_PERFORMED', 'semantics': 'identity proof only; no engine acceptance or Elo claim'})
print(json.dumps({'status': 'PASS_CLOSED', 'archive_sha256': digest(archive_bytes),
                  'archive_bytes': len(archive_bytes), 'receipt': str(receipt),
                  'receipt_sha256': digest(receipt.read_bytes()),
                  'original_file_map_sha256': digest(original_map.read_bytes())}, sort_keys=True))
