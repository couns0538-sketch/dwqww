#!/usr/bin/env python3
"""Read-only re-audit of frozen A1 receipts, transcripts and manifests.
IDEA_SOURCE: user evidence-preservation and fixed-reference qualification rules.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, subprocess
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('matrix',root/'tools/qualify_option_matrix.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
depths=[11,13,16,20,22];pins=[312866,862329,3024920,12389307,34048354]
records=[];errors=[];hash_records=[];historical_changes=[]
correction=json.loads((root/"final_review/historical_manifest_correction.json").read_text())
for name in ['M1','M2','M3','M4','F1','M5','asan_ubsan']:
 folder=root/name;q=json.loads((folder/'qualification.json').read_text())
 assert sha(folder/'forge_release_linux')==q['binary_sha256'],name
 rows=q['off_records'];assert len(rows)==5,name
 for row,depth,pin in zip(rows,depths,pins):
  assert row['depth']==depth and row['mode']=='OFF'
  stem=folder/'pins'/f'OFF_d{depth}'
  parsed=module.parse_bench_result(stem.with_suffix('.stdout').read_bytes(),stem.with_suffix('.stderr').read_bytes(),row['returncode'],depth,pin)
  if not parsed['pass']: errors.append({'case':name,'depth':depth,'errors':parsed['errors']})
 assert q['perft5']==4865609 and q['kiwipete5']==193690690 and q['whole_binary_fma']==0
 assert re.findall(rb'^nodes (\d+)$',(folder/'pins/perft.stdout').read_bytes(),re.M)==[b'4865609']
 assert re.findall(rb'^nodes (\d+)$',(folder/'kiwipete.stdout').read_bytes(),re.M)==[b'193690690']
 records.append({'case':name,'strict_off_transcripts':5,'binary_sha256':q['binary_sha256'],'ctest_exit':q['ctest_exit'],'ctest_failed':q['ctest_failed']})
matrix=json.loads((root/'final_matrix/results.json').read_text());assert matrix['status']=='PASS' and len(matrix['runs'])==75
for row in matrix['runs']:
 stem=root/'final_matrix'/f"{row['case']}_d{row['depth']}"
 parsed=module.parse_bench_result(stem.with_suffix('.stdout').read_bytes(),stem.with_suffix('.stderr').read_bytes(),row['returncode'],row['depth'],row['expected_nodes'])
 if not parsed['pass']:errors.append({'case':row['case'],'depth':row['depth'],'errors':parsed['errors']})
for manifest in sorted(root.rglob('*')):
 if manifest.name not in ('SHA256SUMS.txt','MANIFEST.sha256','FROZEN_MANIFEST.sha256','CURRENT_MANIFEST_20261029.sha256'):continue
 if 'final_review' in manifest.parts:continue
 base=root if manifest.parent.name in ('timeout_parser_checks','matrix_parser_checks') else manifest.parent
 count=0
 for line in manifest.read_text().splitlines():
  if not line.strip():continue
  match=re.fullmatch(r'([0-9a-fA-F]{64})  (.+)',line);assert match,(str(manifest),line)
  path=base/match[2];count+=1
  if not path.is_file() or sha(path)!=match[1].lower():
   if str(manifest.relative_to(root))==correction['original_manifest'] and match[2]==correction['historical_entry']:
    assert match[1].lower()==correction['historical_sha256']==sha(root/correction['recovered_original'])
    assert sha(path)==correction['current_readme_sha256']
    historical_changes.append(correction)
   else:errors.append({'manifest':str(manifest.relative_to(root)),'file':match[2],'issue':'missing or hash mismatch'})
 hash_records.append({'manifest':str(manifest.relative_to(root)),'entries':count})
repo=root.parents[1]
assert subprocess.run(['git','diff','--quiet','926c55f33227bc4a030d7ce5b1140528aeba75af','--','src','include','CMakeLists.txt'],cwd=repo).returncode==0
result={'status':('PASS_WITH_DOCUMENTED_HISTORICAL_DOC_CHANGE' if historical_changes else 'PASS') if not errors else 'FAIL','historical_changes':historical_changes,'engine_source_unchanged':'926c55f33227bc4a030d7ce5b1140528aeba75af','frozen_off_transcripts':35,'matrix_transcripts':75,'receipts':records,'manifests':hash_records,'manifest_entries':sum(x['entries'] for x in hash_records),'errors':errors,'scope':'Re-audit of existing original evidence, not rerun engines. TSan live pins excluded.'}
print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
