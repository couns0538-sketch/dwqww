"""Actual frozen source correspondence only; no compiler/engine/Git."""
from pathlib import Path
import importlib.util,json,difflib
H=Path(__file__).resolve().parent;V=H.parent;R=V.parents[1];C=V/'capture-preparation'
spec=importlib.util.spec_from_file_location('scope23capture',C/'capture_actual_five.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.require_full_native();plans={k:m.inspect_plan(k,p) for k,p in m.PLANS.items()};a,b=(plans[k]['source_sha256_before'] for k in ('baseline','candidate'))
assert len(a)==len(b)==77 and set(a)==set(b)
changed=sorted(n for n in a if a[n]!=b[n]);assert changed==['CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/tt_coherence_tests.cpp']
paths=[]
for p in m.PLANS.values():paths += [p['source']/n for n in a]+[m.manifest_path(p),m.receipt_path(p),p['root_proof'],p['native']/'FINAL-RECEIPT.json']
frozen=m.common.snapshot(paths);assert m.common.rehash(frozen)['status']=='passed'
for name in changed:
 x=m.PLANS['baseline']['source']/name;y=m.PLANS['candidate']['source']/name
 (H/(name.replace('/','-')+'.diff')).write_text(''.join(difflib.unified_diff(x.read_text().splitlines(True),y.read_text().splitlines(True),fromfile='frozen22/'+name,tofile='frozen23/'+name)))
result={'status':'PASS_ACTUAL22_23_SOURCE_SCOPE_NATIVE_ONLY','sources':{'baseline':m.BASELINE,'candidate':m.CANDIDATE},'source_counts':{'baseline':77,'candidate':77},'changed_paths':changed,'unchanged_paths':sorted(n for n in a if a[n]==b[n]),'unchanged_count':73,'source_maps':{'baseline':a,'candidate':b},'consumed_inputs':frozen,'consumed_count':len(frozen),'final_rehash_status':'passed','policy':'Intentional coupled TT generation-refresh replacement/admission/hashfull change, not a known bug or speed claim. Exact search parity not required.','windows23_required':False,'engine_build_git_executions':0}
m.save(H/'SOURCE-GATE.json',result);print(json.dumps({'status':result['status'],'changed':changed,'unchanged':73,'inputs':len(frozen)}))
