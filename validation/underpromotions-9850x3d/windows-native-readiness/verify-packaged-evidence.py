"""Check identity across packaged readiness reports, commands and actual output bytes."""
from pathlib import Path
import hashlib
import json
import zipfile

BASE=Path(__file__).resolve().parent
REPO=BASE.parents[2]
ATTEMPT=BASE/'attempt2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
audit=load(ATTEMPT/'independent-audit.json')
result=load(ATTEMPT/'result.json')
protocol=load(ATTEMPT/'protocol.json')
launch=load(ATTEMPT/'launch.json')
artifact=REPO/'releases/forge-6.4.2-windows-validation-bundle.zip'
with zipfile.ZipFile(artifact) as bundle:
    data=bundle.read('forge-6.4.2-windows-validation-bundle/manifest.json')
    manifest=json.loads(data)
    expected_manifest=hashlib.sha256(data).hexdigest()
assert audit['manifest_sha256']==expected_manifest, 'copied audit identifies the wrong manifest'
assert audit['run_directory'].endswith('/windows-native-readiness-attempt2'), 'copied audit identifies the wrong attempt'
assert audit['bundle_files']==len(manifest['files'])==2345
assert audit['frozen_inputs']==len(result['final_input_sha256'])==2346
assert audit['results_zip_sha256']==sha(ATTEMPT/'original-results.zip'), 'copied audit identifies the wrong results ZIP'
assert audit['final_result_sha256']==sha(ATTEMPT/'result.json'), 'copied audit identifies the wrong raw result'
assert audit['script_sha256']==sha(ATTEMPT/'independent-audit.py')
assert result['status']=='aa_passed' and audit['audit_status']=='passed'
assert protocol['input_sha256']==result['final_input_sha256']
assert protocol['input_sha256']['manifest.json']==expected_manifest
assert launch['attempt']==2 and launch['command'][launch['command'].index('--out')+1].endswith('windows-native-readiness-attempt2')
assert launch['concurrent_load_note']['activity'].startswith('Root authorized a TSan -j2 compile')
assert (ATTEMPT/'full-console.log').is_file()
assert 'windows-native-readiness-attempt2.zip' in (ATTEMPT/'full-console.log').read_text()
with zipfile.ZipFile(ATTEMPT/'original-results.zip') as outputs:
    assert outputs.testzip() is None
    for stored,readable in [('result.json','result.json'),('protocol.json','protocol.json'),
                            ('aa/result.json','aa-result.json'),('aa/command.json','command.json'),
                            ('aa/console.txt','console.txt'),('aa/games.pgn','games.pgn'),('aa/state.json','state.json')]:
        assert outputs.read(stored)==(ATTEMPT/readable).read_bytes(), f'wrong copied output: {readable}'
report={'verification_status':'passed','attempt':2,'manifest_sha256':expected_manifest,
        'results_zip_sha256':sha(ATTEMPT/'original-results.zip'),
        'audit_sha256':sha(ATTEMPT/'independent-audit.json'),'launch_sha256':sha(ATTEMPT/'launch.json'),
        'script_sha256':sha(Path(__file__))}
(BASE/'packaged-evidence-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
