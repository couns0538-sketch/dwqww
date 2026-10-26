from pathlib import Path
import hashlib,json,tarfile,xml.etree.ElementTree as ET
H=lambda b:hashlib.sha256(b).hexdigest()
r=Path('/tmp/forge_sol_S10_native_20261026');a=Path('/tmp/forge_sol_S10_capture_history_lmp_evidence_20261026');v=Path('/workspace/dwqww/validation/forge_sol_pack31_20261025')
refs={'11':308972,'13':745494,'16':2460422,'20':11901452,'22':31111774};on={'11':304755,'13':813494,'16':2591604,'20':8234313,'22':23665760};summaries=[]
for arm,n in [('Lprime',14),('B',15)]:
 p=r/f'capture_history_lmp_{arm}_once/forge_sol_S10_native_result_20261026.json';d=json.loads(p.read_text());assert d['status']=='REJECTED_SEARCH_SCREEN' and d['source_unchanged']
 for prof in ['release','asan_ubsan']:
  z=d[prof];assert z['status']=='PASS' and z['runtime_artifacts_unchanged'];ct=z['ctest'];assert ct['status']=='PASS' and len(ct['test_cases'])==n
  cases=ET.parse(ct['junit']).getroot().findall('.//testcase');assert len(cases)==n and not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
  assert sum(len(c['known_diagnostics']) for c in ct['test_cases'])==4 and all(c['status']=='PASS' for c in ct['test_cases'])
  assert all(x['status']=='PASS' and x['fma_count']==0 for x in z['fma'])
  assert z['bench']['first_bare11']==308972
  if prof=='release':
   assert z['bench']['off']==refs and z['bench']['on']==on and [x['actual'] for x in z['perft5']]==[4865609,193690690]
   assert z['node_screen']['guard_status']=='FAIL' and z['node_screen']['guard_depths']==[20,22]
   assert len(z['compile_OFF_proof'])==8 and all(x['status'].startswith('PASS') for x in z['compile_OFF_proof'])
  else:assert z['bench']['off']=={'11':308972} and z['bench']['on']=={'11':304755}
 if arm=='Lprime':assert d['wac']['evaluated']==300 and d['wac']['solved']==258
 t=r/f'capture_history_lmp_{arm}_T2_ON_once/forge_sol_S10_ON_T2_asan_v2_result_20261026.json';td=json.loads(t.read_text());assert td['status']=='PASS' and td['source_unchanged'] and td['runtime_artifacts_unchanged'] and td['original_job_result_sha256']==H(p.read_bytes())
 summaries.append({'base':arm,'main_result_sha256':H(p.read_bytes()),'T2_result_sha256':H(t.read_bytes()),'full_Release_and_ASAN_tests_each':n})
mp=a/'forge_sol_S10_capture_history_lmp_mapping_20261026.json';m=json.loads(mp.read_text());ar=a/'forge_sol_S10_capture_history_lmp_evidence_20261026.tar.gz';assert H(ar.read_bytes())=='59f0436d68caa260f2eb11a1d738a799248016f85e3f4c80e7f0b63db1714ee0'
gnu=a/'forge_sol_S10_capture_history_lmp_GNU_roundtrip_20261026'
with tarfile.open(ar,'r:gz') as tf:
 assert len(tf.getmembers())==len(m['files'])+1
 for row in m['files']:
  data=tf.extractfile(row['member']).read();assert len(data)==row['bytes'] and H(data)==row['sha256']
  assert Path(row['original']).read_bytes()==data and (gnu/row['member']).read_bytes()==data
out=v/'forge_sol_S10_capture_independent_outcome_audit_20261026.json';assert not out.exists();out.write_text(json.dumps({'status':'PASS_ORIGINAL_EVIDENCE_VERIFIED','feature':'capture_history_lmp','native_reruns':0,'decision':'REJECTED_SEARCH_SCREEN_NOT_ADOPTED','bases':summaries,'archive_sha256':H(ar.read_bytes()),'originals_and_two_decoders_matched':len(m['files'])},indent=2)+'\n');print('PASS: both full Std/T2 originals;397 archive/original/GNU bytes identical; no native rerun')
