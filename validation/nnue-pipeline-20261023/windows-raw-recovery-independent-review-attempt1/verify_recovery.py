#!/usr/bin/env python3
"""Read-only source audit and exact-Git-blob Windows outer reconstruction."""
from pathlib import Path, PurePosixPath
import datetime, hashlib, json, os, stat, subprocess, sys, zipfile

OUT = Path(__file__).resolve().parent
REPO = Path('/workspace/dwqww')
SOURCE = Path('/workspace/forge-nnue-handoff-20261023/windows-final-net-trial-attempt1')
COMMIT = 'a6a3386debea08f0010cc8a1feed25d8c983f0af'
INDEX_PATH = 'validation/nnue-pipeline-20261023/windows-final-net-trial-recovery-index/RECOVERY-INDEX.json'
INPUTS = OUT / 'committed-inputs'
RESTORED = OUT / 'restored-outer'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def strict_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, 'duplicate JSON key: ' + key
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def relative(text):
    p = PurePosixPath(text)
    assert isinstance(text, str) and text and not p.is_absolute(), repr(text)
    assert not any(x in ('', '.', '..') for x in text.split('/')), repr(text)
    assert '\\' not in text and '\x00' not in text, repr(text)
    return p


def regular(path):
    s = path.lstat()
    assert stat.S_ISREG(s.st_mode), 'not regular: ' + str(path)
    return s


def inventory(root):
    result = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            assert not (Path(parent)/name).is_symlink(), 'symlink directory'
        for name in files:
            p = Path(parent)/name
            s = regular(p)
            data = p.read_bytes()
            result[p.relative_to(root).as_posix()] = {
                'sha256': sha(data), 'bytes': len(data), 'mode': stat.S_IMODE(s.st_mode)
            }
    return result


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)


def committed_input(repo_path):
    relative(repo_path)
    oid = git('rev-parse', COMMIT + ':' + repo_path).decode().strip()
    blob = git('cat-file', 'blob', oid)
    checkout = REPO/repo_path
    s = regular(checkout)
    actual = checkout.read_bytes()
    assert actual == blob, 'working copy differs from exact Git blob: ' + repo_path
    destination = INPUTS/repo_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as f:
        f.write(blob)
    report = {'repository_path': repo_path, 'git_blob_oid': oid,
              'sha256': sha(blob), 'bytes': len(blob),
              'working_copy_mode': stat.S_IMODE(s.st_mode),
              'working_copy_exact_git_blob': True}
    return blob, destination, report


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert git('rev-parse', COMMIT).decode().strip() == COMMIT
    INPUTS.mkdir()
    RESTORED.mkdir()
    before = inventory(SOURCE)
    save_json(OUT/'ORIGINAL-INVENTORY-BEFORE.json', before)
    index_blob, _, index_input = committed_input(INDEX_PATH)
    index = strict_json(index_blob)
    records = index['records']
    assert index['status'] == 'ALL_ORIGINAL_WINDOWS_OUTER_BYTES_BOUND_FOR_RECOVERY'
    assert len(records) == index['all_closed_outer_files'] == 509
    assert set(records) == set(before), 'original file set differs from index'
    package_blob, package_local, package_input = committed_input(index['package_repository_path'])
    assert sha(package_blob) == index['package_sha256']
    del package_blob
    inputs = [index_input, package_input]
    extra_root = PurePosixPath(INDEX_PATH).parent
    extra_data = {}
    for rec in records.values():
        choices = set(rec).intersection(('recover_from_zip_member', 'recover_from_repository'))
        assert len(choices) == 1, 'record must have exactly one recovery source'
        if 'recover_from_repository' in rec:
            rp = relative(rec['recover_from_repository'])
            assert str(rp).startswith('additional-originals/'), str(rp)
            if str(rp) not in extra_data:
                blob, _, report = committed_input((extra_root/rp).as_posix())
                extra_data[str(rp)] = blob
                inputs.append(report)
    actual_extra = {p.relative_to(REPO/str(extra_root)).as_posix()
                    for p in (REPO/str(extra_root)/'additional-originals').rglob('*') if p.is_file()}
    assert actual_extra == set(extra_data), 'additional-original file set mismatch'
    save_json(OUT/'COMMITTED-INPUTS.json', inputs)
    producer = strict_json((SOURCE/'FILES-SHA256.json').read_bytes())
    assert isinstance(producer, dict)
    assert len(producer) == index['original_producer_manifest_records'] == 198
    assert {name for name, rec in records.items() if rec['in_original_producer_manifest']} == set(producer)
    for name, rec in producer.items():
        assert before[name]['sha256'] == rec['sha256']
        assert before[name]['bytes'] == rec['bytes']
    rows = {}
    zip_refs = repo_refs = zip_mode_differences = 0
    chosen_members = set()
    with zipfile.ZipFile(package_local) as archive:
        infos = archive.infolist()
        assert len({i.filename for i in infos}) == len(infos), 'duplicate ZIP members'
        for info in infos:
            relative(info.filename.rstrip('/'))
            assert not stat.S_ISLNK(info.external_attr >> 16), 'ZIP symlink'
        for name, rec in sorted(records.items()):
            relative(name)
            expected = {key: rec[key] for key in ('sha256', 'bytes', 'mode')}
            assert before[name] == expected, 'original manifest mismatch: ' + name
            assert isinstance(rec['mode'], int) and 0 <= rec['mode'] <= 0o7777
            original_data = (SOURCE/name).read_bytes()
            if 'recover_from_zip_member' in rec:
                member = rec['recover_from_zip_member']
                relative(member)
                info = archive.getinfo(member)
                assert not info.is_dir()
                data = archive.read(info)
                source_mode = stat.S_IMODE(info.external_attr >> 16)
                zip_mode_differences += source_mode != rec['mode']
                chosen_members.add(member)
                recovery_source = {'kind':'zip', 'member':member, 'member_mode':source_mode,
                                   'zip_crc32':format(info.CRC, '08x')}
                zip_refs += 1
            else:
                rp = rec['recover_from_repository']
                data = extra_data[rp]
                recovery_source = {'kind':'additional-original', 'repository_relative':rp}
                repo_refs += 1
            assert len(data) == rec['bytes'], 'recovery size mismatch: ' + name
            assert sha(data) == rec['sha256'], 'recovery hash mismatch: ' + name
            assert data == original_data, 'recovered bytes mismatch: ' + name
            dest = RESTORED/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as f:
                f.write(data)
            dest.chmod(rec['mode'])
            restored_stat = regular(dest)
            assert stat.S_IMODE(restored_stat.st_mode) == rec['mode'], 'restored mode mismatch: ' + name
            assert dest.read_bytes() == original_data, 'restored byte comparison mismatch: ' + name
            rows[name] = {**expected, 'recovery_source':recovery_source,
                          'original_matches_index':True, 'recovery_bytes_equal_original':True,
                          'restored_bytes_equal_original':True, 'restored_mode_equal_original':True,
                          'in_original_producer_manifest':rec['in_original_producer_manifest']}
    restored = inventory(RESTORED)
    save_json(OUT/'RESTORED-INVENTORY.json', restored)
    after = inventory(SOURCE)
    save_json(OUT/'ORIGINAL-INVENTORY-AFTER.json', after)
    assert restored == before, 'restored full inventory differs'
    assert before == after, 'original source changed during independent verification'
    assert zip_refs == 501 and repo_refs == 8 and len(extra_data) == 8
    save_json(OUT/'PER-FILE-RECOVERY-VERIFICATION.json', rows)
    result = {
      'status':'PASS', 'commit':COMMIT, 'started_utc':started,
      'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'index_sha256':sha(index_blob), 'package_sha256':index['package_sha256'],
      'committed_input_blobs_verified':len(inputs), 'original_files':len(before),
      'restored_files':len(restored), 'total_original_bytes':sum(r['bytes'] for r in before.values()),
      'zip_recovery_references':zip_refs, 'distinct_zip_recovery_members':len(chosen_members),
      'additional_original_references':repo_refs, 'additional_original_blobs':len(extra_data),
      'original_producer_manifest_records_verified':len(producer),
      'restored_mode_matches':len(restored), 'zip_member_mode_differs_from_original_count':zip_mode_differences,
      'original_source_inventory_unchanged':True, 'unresolved_recovery_gaps':[],
      'scope':'All 509 closed outer originals reconstructed without execution from exact a6a3386 Git blobs and compared byte/hash/size/mode to the closed local source. No build/test/benchmark or external publication verification.'
    }
    save_json(OUT/'RESULT.json', result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
