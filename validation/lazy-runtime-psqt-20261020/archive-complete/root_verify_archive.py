"""Independent root preservation check; never imports the archive producer."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import stat
import zipfile

base = Path(__file__).resolve().parent
sha = lambda data: hashlib.sha256(data).hexdigest()
manifest_path = base / 'forge-runtime-psqt-61f5980-20261020-complete.manifest.json'
manifest = json.loads(manifest_path.read_text())
assert sha(manifest_path.read_bytes()) == '905893a4d808c904e5189540a945e38b3d000e0891a62e88b1f707027394e37d'
blocks = []
for part in manifest['parts']:
    data = (base / part['file']).read_bytes()
    assert len(data) == part['size'] and sha(data) == part['sha256']
    blocks.append(data)
combined = b''.join(blocks)
assert len(combined) == manifest['archive']['size'] == 112207796
assert sha(combined) == manifest['archive']['sha256'] == 'd90110e326c6d24c3045c8601ed4dd37ba7b9fbfc35c1bffcabddab6cf733f31'
files = manifest['files']
assert len(files) == 1774
with zipfile.ZipFile(io.BytesIO(combined)) as archive:
    expected = {'files/' + row['path'] for row in files} | {manifest['manifest_member']}
    assert len(archive.namelist()) == len(set(archive.namelist())) == len(expected)
    assert set(archive.namelist()) == expected
    for row in files:
        data = archive.read('files/' + row['path'])
        assert len(data) == row['size'] and sha(data) == row['sha256']
    modes = json.loads(archive.read('files/archive-provenance/LIVE-FILES-AND-MODES.json'))
    assert len(modes['files']) == 1762
    total = 0
    for row in modes['files']:
        original = Path(row['original'])
        data = original.read_bytes()
        assert len(data) == row['size'] and sha(data) == row['sha256']
        assert stat.S_IMODE(original.stat().st_mode) == row['mode']
        assert archive.read('files/' + row['payload_path']) == data
        total += len(data)
    assert total == 298643155
audit = json.loads((base / 'INDEPENDENT-ARCHIVE-AUDIT.json').read_text())
assert audit['status'] == 'PASS_INDEPENDENT_COMPLETE_19_ARCHIVE_AUDIT'
assert not audit['failures']
result = {
    'status': 'PASS_ROOT_COMPLETE19_PARTS_PAYLOADS_AND_LIVE_ORIGINALS',
    'utc': datetime.now(timezone.utc).isoformat(),
    'source_commit': '61f598056572dfade6994af8ad2e38817cd28aa3',
    'parts': len(blocks), 'combined_bytes': len(combined),
    'combined_sha256': sha(combined),
    'archive_payload_files_byte_verified': len(files),
    'live_original_files_byte_and_mode_verified': len(modes['files']),
    'live_original_bytes': total,
    'original_file_and_directory_modes_recorded': True,
    'zip_mode_qualification': 'Trusted ZIP records generic0600; restoration must apply embedded original mode map. Unzip alone does not restore executable access.',
    'independent_audit_sha256': sha((base / 'INDEPENDENT-ARCHIVE-AUDIT.json').read_bytes()),
    'engine_compile_or_test_executions': 0,
    'calibrated_speed_or_elo_acceptance': False,
}
(base / 'ROOT-VERIFY.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
