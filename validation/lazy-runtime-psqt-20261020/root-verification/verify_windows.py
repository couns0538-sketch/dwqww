"""Read-only checks of the closed Windows19 originals and shipped artifact."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[3]
base = root / 'validation/lazy-runtime-psqt-windows-20261020'
out = Path(__file__).with_name('WINDOWS.json')
digest = lambda b: hashlib.sha256(b).hexdigest()
load = lambda name: json.loads((base / name).read_text())
final = load('FINAL-STATUS.json')
audit = load('independent-audit.json')
assert final['source_commit'] == '61f598056572dfade6994af8ad2e38817cd28aa3'
assert audit['status'] == 'passed'
assert audit['check_count'] == len(audit['checks']) == 1184
assert all(c['passed'] is True for c in audit['checks'])
raws = load('windows-originals-SHA256.json')
assert len(raws) == 205
raw_path = base / 'windows-originals.zip'
assert digest(raw_path.read_bytes()) == final['raw_archive_sha256']
with zipfile.ZipFile(raw_path) as raw:
    assert len(raw.namelist()) == len(set(raw.namelist())) == 206
    assert set(raw.namelist()) == set(raws) | {'windows-originals-SHA256.json'}
    assert raw.read('windows-originals-SHA256.json') == (base / 'windows-originals-SHA256.json').read_bytes()
    for name, record in raws.items():
        original = (base / name).read_bytes()
        assert len(original) == record['bytes']
        assert digest(original) == record['sha256']
        assert raw.read(name) == original
protected = load('parent6418-preservation-before.json')
assert len(protected) == 219
for name, sha in protected.items():
    assert digest(Path(name).read_bytes()) == sha
source = load('source-hashes.json')
assert len(source) == 71
for name, sha in source.items():
    assert digest((base / 'originals/frozen-source' / name).read_bytes()) == sha
artifact = root / final['artifact']
assert artifact.stat().st_size == final['artifact_bytes'] == 13577092
assert digest(artifact.read_bytes()) == final['artifact_sha256']
prefix = 'forge-6.4.19-candidate-windows-zen5/'
with zipfile.ZipFile(artifact) as release:
    assert len(release.namelist()) == len(set(release.namelist())) == 20
    records = release.read(prefix + 'SHA256SUMS').decode().splitlines()
    assert len(records) == 19
    names = set()
    for line in records:
        sha, name = line.split('  ', 1)
        assert name not in names
        names.add(name)
        data = release.read(prefix + name)
        assert digest(data) == sha
        assert data == (root / 'releases' / prefix / name).read_bytes()
    assert names == {n[len(prefix):] for n in release.namelist()} - {'SHA256SUMS'}
    engine = release.read(prefix + 'forge-6.4.19-ryzen-9850x3d.exe')
    assert engine == (base / 'originals/binaries/forge.exe').read_bytes()
    assert digest(engine) == final['engine_sha256']
    assert release.read(prefix + 'windows-originals.zip') == raw_path.read_bytes()
build = load('result.json')
for name, record in build['binaries'].items():
    assert digest(Path(record['path']).read_bytes()) == record['sha256']
    assert digest((base / 'originals/binaries' / name).read_bytes()) == record['sha256']
assert final['wine_checks_passed'] == 10
assert final['runtime_psqt_checks'] == 347 and final['runtime_psqt_failures'] == 0
assert final['bench11_nodes'] == 352313
proof = {
    'status': 'PASS_ROOT_WINDOWS19_ORIGINALS_AND_ARTIFACT_REVIEW',
    'utc': datetime.now(timezone.utc).isoformat(),
    'source_commit': final['source_commit'],
    'audit_checks_verified': len(audit['checks']),
    'raw_originals_byte_verified': len(raws),
    'source_files_rehashed': len(source),
    'protected_parent_files_rehashed': len(protected),
    'original_built_pe_files_rehashed': len(build['binaries']),
    'release_members': 20, 'release_checksum_entries': 19,
    'wine_checks_passed': 10, 'runtime_psqt_checks': 347,
    'bench11_nodes': 352313,
    'artifact': final['artifact'], 'artifact_sha256': final['artifact_sha256'],
    'artifact_bytes': final['artifact_bytes'], 'engine_sha256': final['engine_sha256'],
    'raw_archive_sha256': final['raw_archive_sha256'],
    'engine_or_build_execution_by_this_review': 0,
    'native_windows_or_physical_ryzen_tested': False,
    'nps_difference': None, 'elo_gain': None,
}
out.write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof))
