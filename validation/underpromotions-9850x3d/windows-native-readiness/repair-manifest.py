from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path('/workspace/.cloud-setup/windows-validation-bundle with spaces')
BASE=Path('/workspace/dwqww/validation/underpromotions-9850x3d/windows-native-readiness')
PRIOR=BASE/'attempt1'
RUN=Path('/workspace/.cloud-setup/windows-native-readiness-attempt1')
OLD='ef712d7c44499ffa6137db824f0a010bb19f5e5c2795e03849ca3a09e3712349'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(ROOT/'manifest.json')==OLD
PRIOR.mkdir(parents=True,exist_ok=False)
for source,name in [
    (ROOT/'manifest.json','manifest.json'),
    (RUN.parent/'windows-validation-bundle-freeze.json','bundle-freeze.json'),
    (RUN.with_name(RUN.name+'.zip'),'original-results.zip'),
    (RUN.parent/'windows-native-readiness-audit-attempt1.json','independent-audit.json'),
    (RUN.parent/'audit-native-readiness.py','independent-audit.py'),
    (RUN.parent/'windows-native-readiness-launch-attempt1.json','launch.json'),
    (RUN/'result.json','result.json'),(RUN/'protocol.json','protocol.json'),
    (RUN/'aa/result.json','aa-result.json'),(RUN/'aa/command.json','command.json'),
    (RUN/'aa/console.txt','console.txt'),(RUN/'aa/games.pgn','games.pgn'),
    (RUN/'aa/state.json','state.json')]:shutil.copyfile(source,PRIOR/name)
manifest=json.loads((ROOT/'manifest.json').read_text())
actual={p.relative_to(ROOT).as_posix():p for p in ROOT.rglob('*') if p.is_file()}
unlisted=set(actual)-(set(manifest['files'])|{'manifest.json'})
assert unlisted=={'sources/candidate-6.4.2/tools/openings/manifest.json',
                  'sources/original-6.4.0/tools/openings/manifest.json'}
for name,digest in manifest['files'].items():assert sha(actual[name])==digest
discrepancy={
    'status':'integrity_manifest_repaired_before_release',
    'first_manifest_sha256':OLD,'first_listed_files':len(manifest['files']),
    'actual_stage_regular_files':len(actual),
    'omitted_source_only_files':{name:sha(actual[name]) for name in sorted(unlisted)},
    'cause':'Freeze helper excluded every basename manifest.json instead of only bundle-root manifest.json',
    'first_attempt_scope':'A/A normal/deterministic result and all 2344 declared input checks remain valid; whole-bundle inventory-completeness claim was invalid',
    'first_attempt_preservation':'Exact prior manifest, freeze report, original results ZIP and all readable evidence preserved in attempt1/',
    'repair_scope':'Add two unchanged source-only opening metadata manifests and revision metadata; no engine, runtime, runner or opening bytes changed',
    'next_gate':'Fresh attempt2 A/A readiness must pass against corrected complete manifest before packaging/release'}
(BASE/'manifest-discrepancy.json').write_text(json.dumps(discrepancy,indent=2)+'\n')
for name in unlisted:manifest['files'][name]=sha(actual[name])
manifest['files']=dict(sorted(manifest['files'].items()))
manifest['manifest_revision']=2
manifest['previous_manifest_sha256']=OLD
manifest['revision_note']='Includes two previously omitted unchanged source-only tools/openings/manifest.json files; no engine/runtime/runner/opening changes'
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert set(actual)==set(manifest['files'])|{'manifest.json'}
report={'status':'corrected_complete_manifest_prepared_not_yet_aa_validated',
        'manifest_sha256':sha(ROOT/'manifest.json'),'manifest_listed_files':len(manifest['files']),
        'actual_regular_files':len(actual),'previous_manifest_sha256':OLD,
        'all_previously_frozen_nonmanifest_bytes_unchanged':True,
        'omitted_files_now_listed':discrepancy['omitted_source_only_files']}
(BASE/'manifest-repair.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
