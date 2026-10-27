"""Independent frozen-source AST audit only; no consumer main/native execution."""
from pathlib import Path
import ast,copy,hashlib,json,re
R=Path(__file__).resolve().parent
P=Path('/tmp/forge_sol_S11_resource_guard_v3_prep_20261027')
S18=Path('/tmp/forge_sol_S18_rss_scope_v3_checkpoint_20261027/prep/forge_sol_S18_train_selected_v3_20261027.py')
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
D=lambda x:ast.dump(x,include_attributes=False)
old=P/'forge_sol_S11_resource_guard_v3_20261027.py';new=P/'forge_sol_S11_resource_guard_v3_reviewv3_20261027.py'
co=P/'forge_sol_S11_scalar_parity_resource_guard_v3_run_20261027.py';cn=P/'forge_sol_S11_scalar_parity_resource_guard_v3_reviewv3_run_20261027.py'
expected={old:'6eb98832363e901eff8afd966c972fc758ee8ff1838a04bb40c634a2b30578aa',new:'1f963425a0c1deeb13f740d4de4b37a4bc7e48d6364ecd21caa95149469f38cd',co:'22de66422f0f4cb6662200885a31351f4a40d77a445932ea63ee4a18505aff26',cn:'3a63b3a0788f659954986a1780df455f3a78b5c90a371f4e4d0c2fa31b1c6cb7'}
for p,h in expected.items():assert H(p)==h
at=ast.parse(old.read_text());bt=ast.parse(new.read_text());ac=next(n for n in at.body if isinstance(n,ast.ClassDef));bc=next(n for n in bt.body if isinstance(n,ast.ClassDef))
am={n.name:n for n in ac.body if isinstance(n,ast.FunctionDef)};bm={n.name:n for n in bc.body if isinstance(n,ast.FunctionDef)}
assert am.keys()==bm.keys();changed={name for name in am if D(am[name])!=D(bm[name])};assert changed=={'__init__','_read_rss','snapshot'}
normalized_class=copy.deepcopy(bc)
normalized_class.body=[copy.deepcopy(am[n.name]) if isinstance(n,ast.FunctionDef) and n.name in changed else n for n in normalized_class.body]
assert D(normalized_class)==D(ac)
helpers={n.name:n for n in bt.body if isinstance(n,ast.FunctionDef)}
assert set(helpers)=={'read_proc_status','owned_task_ids','_owned_task_identity','read_owned_rss_bytes'}
normalized=copy.deepcopy(bt)
normalized.body=[copy.deepcopy(ac) if isinstance(n,ast.ClassDef) else n for n in normalized.body if not isinstance(n,ast.FunctionDef)]
assert D(normalized)==D(at)
s18={n.name:n for n in ast.parse(S18.read_text()).body if isinstance(n,ast.FunctionDef)}
for name in ('read_proc_status','owned_task_ids'):assert D(helpers[name])==D(s18[name])
ca=ast.parse(co.read_text());cb=ast.parse(cn.read_text());assert len(ca.body)==len(cb.body);norm=copy.deepcopy(cb);metadata=[]
for i,(a,b) in enumerate(zip(ca.body,cb.body)):
 if D(a)==D(b):continue
 if isinstance(a,ast.Assign) and isinstance(b,ast.Assign) and len(a.targets)==len(b.targets)==1 and isinstance(a.targets[0],ast.Name) and a.targets[0].id==b.targets[0].id:
  name=a.targets[0].id;assert name in ('RESOURCE_PATH','RESOURCE_SHA','resource_observer')
  if name=='resource_observer':
   c=copy.deepcopy(b);assert isinstance(c.value,ast.Call) and isinstance(c.value.func,ast.Name) and c.value.func.id=='load';assert len(c.value.args)==2 and not c.value.keywords
   assert isinstance(c.value.args[0],ast.Constant) and c.value.args[0].value=='s11_resource_observer_v3_reviewv3'
   c.value.args[0]=copy.deepcopy(a.value.args[0]);assert D(c)==D(a)
  metadata.append(name);norm.body[i]=copy.deepcopy(a)
 elif isinstance(a,ast.FunctionDef) and a.name=='main' and isinstance(b,ast.FunctionDef) and b.name=='main':
  c=copy.deepcopy(b);removed=0
  for node in ast.walk(c):
   if isinstance(node,ast.Call):
    keys=[k for k in node.keywords if k.arg=='resource_observer_review_revision']
    if keys:
     assert len(keys)==1 and isinstance(keys[0].value,ast.Constant) and keys[0].value.value==3
     assert isinstance(node.func,ast.Attribute) and node.func.attr=='update' and isinstance(node.func.value,ast.Name) and node.func.value.id=='result'
     assert any(k.arg=='schema' and isinstance(k.value,ast.Constant) and k.value.value=='forge.S11.three_arm_parity.resource_guard_v3' for k in node.keywords)
     node.keywords=[k for k in node.keywords if k.arg!='resource_observer_review_revision'];removed+=1
  assert removed==1 and D(c)==D(a);norm.body[i]=c;metadata.append('main.result.update.resource_observer_review_revision=3')
 else:raise AssertionError('Unreviewed consumer AST change')
assert len(metadata)==4 and D(norm)==D(ca)
constants={n.targets[0].id:ast.literal_eval(n.value) if isinstance(n.value,ast.Constant) else eval(compile(ast.Expression(n.value),'','eval'),{'__builtins__':{}},{}) for n in bt.body if isinstance(n,ast.Assign)}
assert constants=={'CAP':4294967296,'RSS_INTERVAL':.05,'GROUP_INTERVAL':1.,'DISK_FLOOR':67108864}
for name in am:
 if name not in changed:assert D(am[name])==D(bm[name])
logs={}
for p in sorted(R.glob('*.stderr')):
 text=p.read_text();match=re.search(r'Ran (\d+) tests? in ([0-9.]+)s',text)
 assert match and '\nOK\n' in text
 logs[p.name]={'sha256':H(p),'tests':int(match[1]),'seconds':float(match[2])}
assert sum(v['tests'] for v in logs.values())==37
for p,h in expected.items():assert H(p)==h
record={'independent_audit_source_sha256':H(__file__),'status':'PASS_BOUNDED_SOURCE_AND_PURE_REVIEW','scope':'No native/compiler/match retry or execution grant; root retains publication and fresh-native-grant authority','reviewed_sources':[{'path':str(p),'sha256':h} for p,h in expected.items()],'original_blocked_review':{'path':str(R.parent/'forge_sol_S11_guard_v3_independent_source_review_20261027.json'),'sha256':H(R.parent/'forge_sol_S11_guard_v3_independent_source_review_20261027.json'),'false_zero_RED_controls_retained':True},'guard_AST':{'added_top_level_reader_helpers':sorted(helpers),'changed_existing_methods':sorted(changed),'all_other_class_methods_imports_constants_and_module_AST_unchanged':True,'own_S18_read_proc_status_and_owned_task_ids_AST_identical':True},'consumer_AST':{'exactly_four_version_pin_metadata_locations':metadata,'all_other_module_AST_identical_to_prior_consumer':True,'prior_consumer_resource_only_comparison_vs_original_v2_bound_in_original_review':True},'constants':constants,'fresh_pure_tests':logs,'total_fresh_pure_tests':37,'independent_actual_Guard_reason_cases':['Captured12,572KiB shared-MM fallback counted once at4GiB-1KiB/exact4GiB/4GiB+1KiB aggregate thresholds','Verified all-dead zombie drain/reap/finalize normal','Unknown non-Z missingRSS stops','Deadline arriving during RSS fallback stops after bounded scan','Leader disappearance after taskRSS read closes normally'],'RSS_review':'Bounded8KiB reads/64tasks; Pid/Tgid/group/birth/stable-inventory validation; max shared-MM once; explicit0 remains known; only verified all-dead permits0 substitution for unavailable leader RSS. Unknown/malformed/non-Z missingRSS fail closed.','scope_limits':['Aggregate RSS is sampled, not continuous. New descendants may await1s membership refresh plus loop/scan work.','Pure fixtures/read-only bindings do not establish native parity, actual performance or complete Linux-runtime behavior.','Original native failures remain FAIL; no historical root cause is inferred.','No engine/producer/flags/corpus/numerical proof/retention/deadline/RSS cap change.'],'other_must_fix_findings':[],'native_runs':0}
p=R/'forge_sol_S11_guard_corrected_independent_review_20261027.json';p.write_text(json.dumps(record,indent=2)+'\n');print('review_json',H(p))
