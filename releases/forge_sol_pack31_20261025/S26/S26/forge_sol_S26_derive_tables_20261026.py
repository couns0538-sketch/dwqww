"""Derive S26 tables from exact original JSON/XML; never run an engine."""
import argparse,csv,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
LOGICAL=Path('/workspace/forge-pack24-20261026')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--evidence-root',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 root=a.evidence_root.resolve();base=root/'S26';refpath=base/'forge_sol_S26_bench_refs_20261026.json';refs=json.loads(refpath.read_text())['nets'];rows=[];inputs={str(refpath):digest(refpath)}
 for case in ['B_lock','f019','f020','f021','f022','f023']:
  native=base/('forge_sol_S26_NATIVE_B_lock_control_20261026' if case=='B_lock' else 'forge_sol_S26_NATIVE_'+case+'_once_20261026')/'result.json'
  outside=base/('forge_sol_S26_NATIVE_B_lock_OUTSIDE_20261026' if case=='B_lock' else 'forge_sol_S26_NATIVE_'+case+'_OUTSIDE_once_20261026')/'result.json'
  n=json.loads(native.read_text());o=json.loads(outside.read_text());items=n['nets']+n['failed_nets'];assert len(items)==1;v=items[0]
  assert n['status'] in ('PASS','FAIL') and v['net_sha256'] in refs
  ref=refs[v['net_sha256']];assert v['bench']==ref['bench']
  units=v['recipe_before']['translation_units'];assert type(units)is int and units==19
  assert v['fma']['status']=='PASS' and v['fma']['fma_count']==0 and len(v['fma']['artifacts'])==2
  w=v['wac'];assert type(w['solved'])is int and w['evaluated']==300
  job=root/Path(v['job']).relative_to(LOGICAL);junit=job/'ctest.xml';cases=list(ET.parse(junit).getroot().iter('testcase'));assert len(cases)==15 and len({x.get('name') for x in cases})==15
  failed=sum(bool(x.findall('failure')+x.findall('error')) for x in cases)
  c=o['CTest'];diag=c.get('diagnostics',c.get('known_diagnostics',[]));assert isinstance(diag,list)
  record={'id':case,'net_md5':v['net_md5'],'net_sha256':v['net_sha256'],'engine_sha256':o['engine_sha256'],**{'d'+d:v['bench'][d] for d in ['11','13','16','20','22']},'bench_reference':'PASS','NNUE_FMA_executable':0,'NNUE_FMA_object':0,'configured_translation_units':units,'WAC_solved':w['solved'],'WAC_positions':300,'WAC_reference':ref.get('wac1000'),'WAC_reference_status':w['reference_status'],'WAC_reference_scope':ref.get('wac_evidence'),'CTest_passed':15-failed,'CTest_cases':15,'CTest_returncode':c['returncode'],'CTest_default_gate':c['status'],'KNOWN_lines':sum(s.startswith('KNOWN_FAILURE:') for s in diag),'FAIL_lines':sum(s.startswith('FAIL:') for s in diag),'PIN_MISMATCH_lines':sum(s.startswith('PIN_MISMATCH:') for s in diag),'native_tool_status':n['status'],'native_result_sha256':digest(native),'outside_result_sha256':digest(outside),'junit_sha256':digest(junit)}
  rows.append(record);inputs.update({str(x):digest(x) for x in (native,outside,junit)})
 assert [r['WAC_solved'] for r in rows]==[268,260,238,242,226,238]
 assert [r['CTest_passed'] for r in rows]==[15,15,15,15,15,14]
 assert rows[-1]['PIN_MISMATCH_lines']==1 and rows[-1]['FAIL_lines']==2
 if a.out.exists():raise FileExistsError('NEW output directory required')
 a.out.mkdir(parents=True);out=a.out
 proof={'schema':'S26_original_results_derived_v1','source_mapping':{'rows':'native.(nets+failed_nets)[0]','units':'row.recipe_before.translation_units:int (not list)','junit_resolution':'original absolute job path mapped relative to explicit LOGICAL root; original JSON never rewritten','outside_control':'B_lock producer differs; diagnostics or known_diagnostics are the two explicit field paths'},'inputs_sha256':inputs,'rows':rows,'games':0,'Elo':'NOT_MEASURED','NPS_comparison':'NOT_MEASURED','per_net_ASAN':'UNVERIFIED_NOT_RUN','candidate_adoption':'NONE','interpretation':'Reference WAC FAIL and UNKNOWN stay distinct; f023 original default pin guard FAIL remains. Native v3 results are not relabeled as execution of delivered v4.'}
 (out/'forge_sol_S26_results_20261026.json').write_text(json.dumps(proof,indent=2)+'\n')
 with (out/'forge_sol_S26_results_20261026.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 lines=['# S26 original native results — 2026-10-26','','All six separate first attempts completed: one B+lock control and five supplied nets. No engine or test expectation was edited. All five benchmark references and NNUE-scoped FMA checks pass. No speed/Elo/adoption claim.','','| Net | d11 / d13 / d16 / d20 / d22 | FMA exe/object | WAC/300 | Reference | CTest | Recorded v3 status |','| --- | --- | --- | --- | --- | --- | --- |']
 for r in rows:
  counts=' / '.join(str(r['d'+d]) for d in ['11','13','16','20','22']);ref='UNKNOWN' if r['WAC_reference'] is None else str(r['WAC_reference'])+' '+r['WAC_reference_status'];lines.append(f"| {r['id']} | {counts} | 0/0 | {r['WAC_solved']} | {ref} | {r['CTest_passed']}/15 | {r['native_tool_status']} |")
 lines+=['','f020 reference279 is supplied INFO/unconfirmed; its comparison FAIL is not a confirmed CR strength verdict. f022/f023 have no measured historical WAC reference. f023 preserves one PIN_MISMATCH (documented661 vs actual620), two WAC FAIL diagnostics and two KNOWN promotion diagnostics; its proposal remains UNREVIEWED/unapplied.','','All configured builds contain19 translation units. Games0; Elo and NPS difference not measured. Per-net ASan/UBSan was not run. The v4 standalone completeness successor has separate42-test and original-JUnit replay evidence; original native processes executed v3. The old controller zombie false positive and its f023-only successor lineage remain in original/additive records.']
 (out/'forge_sol_S26_results_20261026.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'status':'PASS_DERIVATION','rows':len(rows),'checks':'all assertions passed','out':str(out)}))
if __name__=='__main__':main()
