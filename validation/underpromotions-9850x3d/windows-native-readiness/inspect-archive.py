"""Independent, stdlib-only inspection of the published bundle's stored bytes."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

EVIDENCE=Path(__file__).resolve().parent
REPO=EVIDENCE.parents[2]
ARTIFACT=REPO/'releases/forge-6.4.2-windows-validation-bundle.zip'
PREFIX='forge-6.4.2-windows-validation-bundle/'
EXPECTED_ZIP='27022666ef6e9eb14ce5b84109810be3f6caa1d97a25066409f915dd0029367c'
EXPECTED_MANIFEST='576cf088dda67c060934f1f533fa8a69a5d5c4642a36bb2af6b01103c45296e8'
digest=lambda data:hashlib.sha256(data).hexdigest()
assert digest(ARTIFACT.read_bytes())==EXPECTED_ZIP
with zipfile.ZipFile(ARTIFACT) as archive:
    assert archive.testzip() is None
    members=archive.namelist()
    assert len(members)==len(set(members))==2346
    assert all(name.startswith(PREFIX) and '..' not in Path(name).parts for name in members)
    data=archive.read(PREFIX+'manifest.json')
    assert digest(data)==EXPECTED_MANIFEST
    manifest=json.loads(data)
    assert len(manifest['files'])==2345
    assert set(members)=={PREFIX+name for name in manifest['files']}|{PREFIX+'manifest.json'}
    for name,expected in manifest['files'].items():
        assert digest(archive.read(PREFIX+name))==expected
    candidate=manifest['provenance']['candidate']
    for name,expected in candidate['source_files_sha256'].items():
        packed=archive.read(PREFIX+'sources/candidate-6.4.2/'+name)
        committed=subprocess.check_output(['git','-C',str(REPO),'show',candidate['engine_source_commit']+':'+name])
        assert digest(packed)==expected and packed==committed
    original=manifest['provenance']['original']
    original_zip=REPO/'chess-engine-forge-6.4.0.zip'
    assert digest(original_zip.read_bytes())==original['archive_sha256']
    with zipfile.ZipFile(original_zip) as source_archive:
        assert archive.read(PREFIX+'engine/original-6.4.exe')==source_archive.read(original['member'])
        for name in manifest['files']:
            root='sources/original-6.4.0/'
            if name.startswith(root):
                assert archive.read(PREFIX+name)==source_archive.read('chess-engine-forge-6.4.0/'+name[len(root):])
    assert digest(archive.read(PREFIX+'engine/candidate.exe'))=='7928cfbf3e5da6e508c4da5b4c6d4c2a6582a3058951ed5d5479c3098909e324'
report={'inspection_status':'passed','artifact_sha256':EXPECTED_ZIP,
        'manifest_sha256':EXPECTED_MANIFEST,'archive_regular_files':2346,
        'all_crc_membership_and_manifest_checks_passed':True,
        'candidate_source_matches_frozen_git_commit':candidate['engine_source_commit'],
        'original_source_and_release_pe_match_user_archive':True,
        'scope':'Packaged-byte/source provenance and Wine readiness only; no native or Elo claim',
        'script_sha256':digest(Path(__file__).read_bytes())}
(EVIDENCE/'archive-independent-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
