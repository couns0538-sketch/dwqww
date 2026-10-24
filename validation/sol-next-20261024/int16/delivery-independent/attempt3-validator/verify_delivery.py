#!/usr/bin/env python3
"""Read-only Git/source-package audit; no builds, tests, index or ref writes."""
from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import os
import posixpath
import re
import stat
import subprocess
import tarfile
import zipfile

REPO = Path('/workspace/dwqww')
H = Path('/workspace/forge-sol-next-20261024')
PROOF = H / 'oracle-agent/INT16_DELIVERY_VERIFICATION'
WORK = H / 'oracle-agent/INT16_DELIVERY_WORK'
LOCK = 'f4911f2709bd5ae7e5fca7aea30aac5d87314a05'
SOURCE = '074102419c90c6b3725cd83c172e1ec22a2d8203'
ZIP = REPO / 'releases/sol-next-20261024/forge-int16-research-source.zip'
PATCH = REPO / 'releases/sol-next-20261024/int16_fix.patch'
NET = '74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b'
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')
commands = []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(label, argv, cwd=REPO, stdin=None, binary=False):
    p = subprocess.run(argv, cwd=cwd, input=stdin, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, env=ENV, timeout=60)
    stdout = (WORK if binary else PROOF) / (label + '.stdout')
    stderr = PROOF / (label + '.stderr')
    stdout.write_bytes(p.stdout)
    stderr.write_bytes(p.stderr)
    record = {'argv': argv, 'cwd': str(cwd), 'actual_exit': p.returncode,
              'stdin_sha256': digest(stdin) if stdin is not None else None,
              'stdout': str(stdout), 'stdout_bytes': len(p.stdout), 'stdout_sha256': digest(p.stdout),
              'stderr': str(stderr), 'stderr_bytes': len(p.stderr), 'stderr_sha256': digest(p.stderr)}
    commands.append(record)
    (PROOF / (label + '.command.json')).write_text(json.dumps(record, indent=2) + '\n')
    assert p.returncode == 0, (label, p.stderr.decode(errors='replace'))
    return p.stdout


def tree(label, commit, paths):
    raw = run(label, ['git', 'ls-tree', '-rlz', '--full-tree', commit, '--', *sorted(paths)])
    result = {}
    for row in raw.split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        mode, kind, oid, size = meta.decode().split()
        assert kind == 'blob' and mode in ('100644', '100755'), (name, mode, kind)
        result[name.decode()] = {'mode': mode, 'oid': oid, 'bytes': int(size)}
    return result


def main():
    zbytes = ZIP.read_bytes()
    pbytes = PATCH.read_bytes()
    assert digest(zbytes) == 'f7a145738b36cf4ebb7ec460cf93e480453535084db572b14ffdd0385302d103'
    assert digest(pbytes) == '0a9be1a59c500619b52f458015ebaedcbdf00235fba6bb5e21d9272ed2553f73'
    assert len(zbytes) == 1310139 and len(pbytes) == 236353
    with zipfile.ZipFile(io.BytesIO(zbytes)) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        assert len(names) == len(set(names)) and archive.testzip() is None
        for info in infos:
            path = PurePosixPath(info.filename)
            assert not path.is_absolute() and '..' not in path.parts and '\\' not in info.filename
            assert not info.is_dir()
            if info.filename == 'SOURCE_MANIFEST.json':
                assert stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG)
            else:
                assert stat.S_IFMT(info.external_attr >> 16) == stat.S_IFREG
        manifest = json.loads(archive.read('SOURCE_MANIFEST.json'))
        assert manifest['source_commit'] == SOURCE and manifest['lock'] == LOCK
        files = manifest['files']
        expected = {row['path']: row for row in files}
        assert len(expected) == len(files) == 105
        assert set(names) == set(expected) | {'SOURCE_MANIFEST.json'}
        source_tree = tree('source-tree', SOURCE, set(expected))
        assert set(source_tree) == set(expected)
        requests = ''.join(SOURCE + ':' + path + '\n' for path in sorted(expected)).encode()
        raw = run('source-blobs', ['git', 'cat-file', '--batch'], stdin=requests, binary=True)
        cursor = 0
        comparisons = []
        for path in sorted(expected):
            end = raw.index(b'\n', cursor)
            oid, kind, size = raw[cursor:end].decode().split()
            size = int(size)
            assert kind == 'blob' and oid == source_tree[path]['oid']
            content = raw[end + 1:end + 1 + size]
            assert raw[end + 1 + size:end + 2 + size] == b'\n'
            cursor = end + 2 + size
            info = archive.getinfo(path)
            payload = archive.read(path)
            row = expected[path]
            assert payload == content and len(payload) == row['bytes'] == source_tree[path]['bytes']
            assert digest(payload) == row['sha256']
            assert row['mode'] == source_tree[path]['mode']
            assert stat.S_IMODE(info.external_attr >> 16) == int(row['mode'], 8) & 0o777
            comparisons.append({'path': path, 'bytes': len(payload), 'sha256': digest(payload),
                                'git_mode': row['mode'], 'zip_mode': oct(info.external_attr >> 16),
                                'git_zip_manifest_bytes_equal': True, 'mode_equal': True})
        assert cursor == len(raw)
        patch_paths = set()
        for line in pbytes.decode().splitlines():
            if line.startswith('diff --git '):
                _, _, a, b = line.split()
                assert a.startswith('a/') and b.startswith('b/') and a[2:] == b[2:]
                patch_paths.add(a[2:])
        assert patch_paths <= set(expected)
        baseline = tree('lock-tree', LOCK, set(expected) | patch_paths)
        export = run('lock-archive', ['git', 'archive', '--format=tar', LOCK, '--', *sorted(baseline)], binary=True)
        applied = WORK / 'lock-applied-final'
        applied.mkdir()
        with tarfile.open(fileobj=io.BytesIO(export)) as tar:
            for member in tar:
                path = PurePosixPath(member.name)
                assert not path.is_absolute() and '..' not in path.parts
                target = applied.joinpath(*path.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    assert member.isfile()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(member).read())
                    target.chmod(member.mode)
        (PROOF / 'delivered-int16_fix.patch').write_bytes(pbytes)
        for label, extra in [('patch-dry-run', ['--dry-run']), ('patch-apply', [])]:
            output = run(label, ['/usr/bin/patch', '--batch', '--forward', '--fuzz=0', '-p1', *extra],
                         cwd=applied, stdin=pbytes)
            assert not re.search(rb'offset|fuzz|FAILED|reject|Reversed|previously applied', output, re.I), label
            assert not (PROOF / (label + '.stderr')).read_bytes(), label
        assert not list(applied.rglob('*.rej')) and not list(applied.rglob('*.orig'))
        for row in comparisons:
            path = row['path']
            content = (applied / path).read_bytes()
            assert content == archive.read(path), path
            actual_mode = (applied / path).stat().st_mode
            assert stat.S_ISREG(actual_mode), path
            canonical_git_mode = '100755' if actual_mode & stat.S_IXUSR else '100644'
            assert canonical_git_mode == row['git_mode'], path
            row['applied_permission_bits'] = oct(stat.S_IMODE(actual_mode))
            row['applied_canonical_git_mode'] = canonical_git_mode
            row['applied_patch_zip_bytes_equal'] = True
            row['applied_git_mode_equal'] = True
        required = tree('tracked-build-inputs', SOURCE,
                        {'CMakeLists.txt', 'LICENSE', 'bench', 'include', 'src', 'tests', 'tools'})
        assert set(required) <= set(expected)
        includes = []
        for path in expected:
            if Path(path).suffix not in ('.cpp', '.hpp', '.h', '.inc'):
                continue
            for quoted in re.findall(r'^\s*#\s*include\s*"([^"\n]+)"', archive.read(path).decode(), re.M):
                candidates = [posixpath.normpath(posixpath.join(str(PurePosixPath(path).parent), quoted)),
                              posixpath.normpath('include/' + quoted)]
                resolved = next((item for item in candidates if item in expected), None)
                assert resolved is not None, (path, quoted)
                includes.append({'from': path, 'include': quoted, 'resolved': resolved})
        cmake_inputs = sorted(set(re.findall(r'(?:bench|src|include|tests|tools)/[A-Za-z0-9_./-]+\.(?:cpp|hpp|h|py|tsv|epd)',
                                            archive.read('CMakeLists.txt').decode())))
        assert set(cmake_inputs) <= set(expected)
        legacy_inc = ['book_data.inc', 'eval_params_table.inc', 'nnue_weights.inc', 'polyglot_keys.inc']
        for name in legacy_inc + ['nnue_int16.inc']:
            assert 'src/' + name in expected
        assert digest(archive.read('src/nnue_weights.inc')) == NET
        result = {'status': 'PASS', 'baseline': LOCK, 'source_commit': SOURCE,
                  'new_builds_or_engine_runs': 0,
                  'zip': {'path': str(ZIP), 'bytes': len(zbytes), 'sha256': digest(zbytes),
                          'members': len(names), 'source_files': len(files), 'generated_manifest': 'SOURCE_MANIFEST.json',
                          'crc_safe_unique_paths_pass': True, 'all_source_bytes_and_modes_equal_git': True,
                          'embedded_manifest_sha256': digest(archive.read('SOURCE_MANIFEST.json'))},
                  'patch': {'path': str(PATCH), 'bytes': len(pbytes), 'sha256': digest(pbytes),
                            'changed_paths': sorted(patch_paths), 'clean_p1_no_offset_fuzz_rejection': True,
                            'all_105_applied_files_equal_zip': True},
                  'tracked_build_input_count': len(required), 'all_tracked_build_inputs_present': True,
                  'legacy_four_inc_files': legacy_inc, 'new_integer_inc_present': True,
                  'network_sha256': NET, 'cmake_input_files_present': cmake_inputs,
                  'quoted_local_includes_resolve': includes, 'comparisons': comparisons,
                  'commands': commands,
                  'limits': ['No fresh rebuild or runtime requalification.',
                             '105 Git source files plus one generated manifest make 106 ZIP members.',
                             'Original read-only Git blob/archive stdout is retained under INT16_DELIVERY_WORK.',
                             'ZIP Unix permission modes exactly match Git; patched filesystem modes compare canonical Git regular/executable bits because archive/patch permission bits are subject to umask.']}
        (PROOF / 'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'status': 'PASS', 'zip_sources': len(files), 'zip_members': len(names),
                          'applied_files_equal': len(comparisons), 'tracked_build_inputs': len(required),
                          'clean_p1': True, 'bytes_and_modes_equal': True}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        (PROOF / 'FAILURE.json').write_text(json.dumps({'status': 'FAIL', 'error': str(error),
                                                      'commands': commands}, indent=2) + '\n')
        raise
