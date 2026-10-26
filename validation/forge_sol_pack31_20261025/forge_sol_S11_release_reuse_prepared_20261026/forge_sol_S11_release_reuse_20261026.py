"""Explicit original-evidence reuse, ONLY canonical Release baseline arms.

This producer does not claim a new main build, FIRST run, full Std or JUnit.
Native oracle compilation and new light checks are separate granted actions.
"""
from pathlib import Path
import base64,copy,gzip,hashlib,importlib.util,json,re,sys
if not __debug__:raise RuntimeError('Run without -O/PYTHONOPTIMIZE')
sys.dont_write_bytecode=True
SEALED=Path('/tmp/forge_sol_S11_native_prep_20261026')
AUDIT=Path(__file__).resolve().parent/'evidence/forge_sol_S11_baseline_reuse_audit_20261026.json'
AUDIT_SHA='9b6f0d040dad08aa350132711de7b8fa08bcdc82b81340542f24103d21700bd9'
NUMERIC=Path(__file__).resolve().parent/'evidence/forge_sol_S11_baseline_numeric_reuse_addendum_20261026.json'
NUMERIC_SHA='81ac60a31846bfd49ffdf673b916ef6211ef5eed3f0c69a5cc640a2cc02baa16'
INVENTORY=Path('/workspace/forge-pack24-20261026/S11/forge_sol_S11_source_inventory_20261026.json')
INVENTORY_SHA='7c6843ac3c419c96fc7014beb84805154e4ab7ebe083ae79aa8e5e86d472ecc9'
SCHEMA='forge.S11.baseline_release_reuse.v1'
TMP=Path('/tmp/forge_sol_S11_native_20261026')
SEALED_SHAS={
 'forge_sol_S11_build_native_20261026.py':'b678bf1705e8f68797419fd17ff3b86666d16ebf9aa6d73a4636bac49910fb91',
 'forge_sol_S11_qualify_native_20261026.py':'2bc3df4dee673bd909359569f9144281389c30cd0fe51e74f10121e14696753b',
 'forge_sol_S11_scalar_parity_20261026.py':'31f475c01580d376e3f5a28debe3f37651fff7c426ca1a12d20c77832b263ae5',
 'forge_sol_S11_scalar_parity_run_20261026.py':'1bcd18849e1e2c2630b379813752d570728ee8dd93a9aa106d524da577ffcf95',
 'forge_sol_S11_native_preregister_20261026.json':'27db2879a9bd0b44e9e91ebabedaece49cb64cc363a7496a6fc1c7d992f2648e'}
RUNTIME_PINS={
 '/workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_qualify_ASAN_20261026.py':'162da3119d09a63e1152ca855dfe14940e91225feaa1f9bc420f59061d914b39',
 '/workspace/forge-pack24-20261026/S08/forge_sol_S08_v2_qualify_20261026.py':'33c92609f0b4da116625c98cb80d1b9bdd6763cfb5b3d9e3d82f06df87c4a453',
 '/workspace/forge-pack24-20261026/S08/forge_sol_S08_collect_profiles_20261026.py':'bf5d18d25bc1fb342c06092a36bfbac2b4717dc8a3f3c8f5cac34add3c3b1143',
 '/workspace/forge-pack24-20261026/S08/forge_sol_S08_release_resume_after_timing_20261026.py':'08680dce41f6b3b56b6f770ae476454b783b16d9cb61ae462540c04a2f753200',
 '/workspace/forge-pack24-20261026/S08/forge_sol_S08_release_after_timing_20261026.py':'b9890ba9c2204b474bff3bc3c1694558aa573c81faa6b2763316493409fda2ee',
 '/workspace/forge-pack24-20261026/S08/forge_sol_S08_sanitizer_build_20261026.py':'e07f60715d0fb3eff4fbbcde6c2b674ecff049167dfb9bf901b622607b036fc5',
 '/workspace/forge-pack24-20261026/S08/forge_sol_S08_build_window_subreaper_20261026.py':'85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0',
 '/workspace/dwqww/releases/forge_sol_pack31_20261025/S25_v2/forge_sol_S25_outcontract_20261025.py':'96448f9da135e610f7ebeac93a4022f69f46cfc0ecc9a203c4426f34435691a0',
 '/workspace/dwqww/releases/forge_sol_pack31_20261025/S25_v2/forge_sol_S25_options_20261025.json':'a89b184fac9696e2d97176623fdc8fa5be410dbe68c6ba8ba7876f0949de5c8e',
 '/workspace/forge-pack24-20261026/S26/forge_sol_S26_original_evidence_restore_VERIFY_20261026/provided_tools/fma/forge_sol_S05_fmacheck_v3_20261025.py':'e7ba90e5c2bdb43c490d9c992a684f7f0d311d83c7639ad852f77a4dd079d07f'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def pinned_json(path,digest):
    require(sha(path)==digest,'pinned JSON identity differs: '+str(path));return json.loads(Path(path).read_text())
def load(name,path):
    require(path.parent==SEALED and path.name in SEALED_SHAS and sha(path)==SEALED_SHAS[path.name],'sealed module path/hash differs')
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sealed_builder():
    return load('s11_reuse_sealed_builder',SEALED/'forge_sol_S11_build_native_20261026.py')
def sealed_qualifier():
    return load('s11_reuse_sealed_qualifier',SEALED/'forge_sol_S11_qualify_native_20261026.py')
def require_arm(base,role='baseline',profile='Release'):
    require(base in ('Lprime','B'),'unknown canonical base')
    require(role=='baseline','reuse requires baseline role')
    require(profile=='Release','reuse requires Release profile')
def verify_reuse_claims(data):
    require(data.get('evidence_class')=='REUSE_NOT_NEW_RUN' and all(type(data.get(k)) is int and data[k]==0 for k in ('new_main_ELFs','new_FIRST_runs','new_full_Std_runs')) and data.get('new_JUnit') is False,'reuse must not claim fresh main/FIRST/Std/JUnit')
def verify_runtime_dependencies(pins=None):
    rows=RUNTIME_PINS if pins is None else pins
    require(set(rows)==set(RUNTIME_PINS),'runtime dependency inventory differs')
    for p,want in rows.items():require(want==RUNTIME_PINS[p] and sha(p)==want,'runtime dependency changed: '+p)
    return dict(rows)
def decode(row):
    b=base64.b64decode(row['data']);require(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'original raw bytes differ');return b
def make_binding(base):
    require_arm(base);a=pinned_json(AUDIT,AUDIT_SHA);n=pinned_json(NUMERIC,NUMERIC_SHA);inv=pinned_json(INVENTORY,INVENTORY_SHA)
    arm=copy.deepcopy(next(r for r in a['Release'] if r['base']==base));source=Path(arm['source']);frozen=inv['original_source_freezes'][base]
    require(all(sha(source/p)==v for p,v in frozen.items()),'canonical source changed')
    require(sha('/usr/bin/x86_64-linux-gnu-g++-14')==a['compiler_sha256'],'compiler changed')
    old=pinned_json(arm['original_receipt'],arm['original_receipt_sha256'])
    require(old['current_tests_sha256']==arm['tests_source_sha256'] and old['engine_sha256']==arm['main_sha256'],'old source/engine binding differs')
    for r in arm['artifacts_fresh_verified']:require(sha(r['path'])==r['sha256'],'canonical reused artifact changed: '+r['name'])
    canonical_build=Path(arm['artifacts_fresh_verified'][0]['path']).parent
    require(sha(canonical_build/'forge_tests')==arm['tests_ELF_sha256'],'current tests ELF changed')
    flags=[]
    for r in arm['canonical_flags']:
        require(sha(r['path'])==r['sha256'],'canonical flags changed');flags.append(copy.deepcopy(r))
    core=arm['core_archive'];require(sha(core['compressed_path'])==core['archive_sha256'],'canonical core archive changed')
    retirement=pinned_json(core['retirement_map'],core['retirement_map_sha256'])
    original=next(r for r in retirement['files'] if r['path']==core['original_path'])
    require(original['sha256']==core['sha256'] and original['size']==core['bytes'],'canonical core restore map differs')
    core['restore_mode']=original['mode']
    raw=gzip.decompress(Path(core['compressed_path']).read_bytes());require(len(raw)==core['bytes'] and hashlib.sha256(raw).hexdigest()==core['sha256'],'canonical core bytes changed')
    first=old['commands'][0]
    require(first['label']=='first_bare_d11' and first['exit_code']==0 and decode(first['stdin'])==b'bench 11\nquit\n' and not decode(first['stderr']),'original FIRST differs')
    require(first['stdout']['sha256']==arm['raw_FIRST']['stdout_sha256'] and re.fullmatch(rb'info string bench depth 11 nodes 308972 time \d+ nps \d+\n',decode(first['stdout'])),'original FIRST stdout differs')
    std=old['complete_last_test_log'];require(std['sha256']==arm['raw_Std']['sha256'],'original full Std hash differs');text=decode(std).decode()
    names=re.findall(r'\d+/\d+ Test: ([^\n]+)',text);expected=re.findall(r'add_test\(NAME\s+(\w+)',(source/'CMakeLists.txt').read_text())
    require(sorted(names)==sorted(expected) and text.count('Test Passed.')==len(expected) and 'Test Failed.' not in text,'original full Std inventory differs')
    require(all(text.count(line)==1 for line in arm['raw_Std']['known_lines']),'original known lines differ')
    num=copy.deepcopy(next(r for r in n['arms'] if r['base']==base));pinned_json(num['original_receipt'],num['original_receipt_sha256'])
    require(num['exact_main_ELF_sha256']==arm['main_sha256'],'fixed-gate main differs')
    for r in num['fixed_gates']:
        val=pinned_json(r['raw_stdout_wrapper'],r['wrapper_sha256']);body=decode(val)
        require(val['sha256']==r['raw_stdout_sha256'],'fixed-gate raw hash differs')
        require(str(r['nodes']).encode() in body,'fixed-gate nodes absent')
    return {'schema':'forge.S11.original_evidence_binding.v1','evidence_class':'REUSE_NOT_NEW_RUN','base':base,'role':'baseline','profile':'Release','source':str(source),'source_inventory_sha256':INVENTORY_SHA,'source_before':frozen,'audit_sha256':AUDIT_SHA,'numeric_audit_sha256':NUMERIC_SHA,'original_receipt':arm['original_receipt'],'original_receipt_sha256':arm['original_receipt_sha256'],'main_sha256':arm['main_sha256'],'tests_source_sha256':arm['tests_source_sha256'],'tests_ELF_sha256':arm['tests_ELF_sha256'],'canonical_build':str(canonical_build),'artifacts':arm['artifacts_fresh_verified'],'core_archive':core,'canonical_flags':flags,'raw_FIRST':arm['raw_FIRST'],'raw_Std':arm['raw_Std'],'fixed_gates':num,'new_main_ELF':False,'new_FIRST':False,'new_full_Std':False,'new_JUnit':False,'new_light_checks':'REQUIRED_SEPARATE_GATE','new_oracle':'REQUIRED_NEW_COMPILE_AND_PARITY'}
def verify_binding(binding):
    require_arm(binding.get('base'),binding.get('role'),binding.get('profile'))
    require(binding==make_binding(binding['base']),'original evidence binding differs')
def oracle_plan(base,build):
    require_arm(base);builder=sealed_builder();source,_=builder.selected_source(base,'baseline')
    builder.verify_dependencies('Release')
    expected=next(r['source'] for r in pinned_json(AUDIT,AUDIT_SHA)['Release'] if r['base']==base)
    require(str(source)==expected,'oracle source is not the pinned canonical baseline')
    require(build.is_absolute() and build.resolve()==build and build.is_relative_to(TMP) and build!=TMP,'oracle directory outside bounded S11 root')
    return builder.oracle_command(builder.release,source,build,'baseline')
def verify_oracle_plan(base,build,argv):
    require(list(argv)==oracle_plan(base,build),'oracle flags/source/link invocation differs')
def artifact_inventory(binding,build):
    canonical=Path(binding['canonical_build']);items={}
    # Only historically qualified main/Std targets, current forge_tests and new
    # oracle/core are claimed. The unused standalone forge_bench is not borrowed.
    names=[r['name'] for r in binding['artifacts']]+['forge_tests','core_archive','forge_sol_S11_materialkey_oracle']
    for name in names:
        p=build/'libforge_core.a' if name=='core_archive' else build/name if name=='forge_sol_S11_materialkey_oracle' else canonical/name
        items[name]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'origin':'NEW_ORACLE_ONLY' if name=='forge_sol_S11_materialkey_oracle' else 'REUSED_CANONICAL_BYTES'}
    return items
def bind_reuse_arm(receipt_path,first_path,role,published_commit):
    require(role=='baseline','reuse cannot bind candidate role');data=json.loads(Path(receipt_path).read_text())
    require_arm(data.get('base'),data.get('role'),data.get('profile'))
    require(data.get('schema')==SCHEMA and data.get('status')=='PASS_ORACLE_ONLY_WITH_REUSED_STD','closed oracle-only reuse receipt required')
    require(re.fullmatch('[0-9a-f]{40}',published_commit) and data.get('S10_published_commit')==published_commit,'publication receipt differs')
    b=data['evidence'];verify_binding(b);build=Path(data.get('build','/invalid'))
    require(build==Path(receipt_path).parent/'build' and build.resolve()==build and build.is_relative_to(TMP),'oracle receipt directory differs')
    require(first_path==Path(b['original_receipt']) and sha(first_path)==b['original_receipt_sha256'],'original embedded FIRST receipt differs')
    require(data.get('source')==b['source'] and data.get('source_before')==data.get('source_after')==b['source_before'],'oracle source receipt differs')
    verify_reuse_claims(data)
    builder=sealed_builder();builder.verify_dependencies('Release');require(data.get('compiler_sha256')==builder.owned.CXX_SHA,'oracle compiler differs')
    require(data.get('reuse_verifier_sha256')==sha(__file__) and data.get('controller_sha256')==sha(Path(__file__).with_name('forge_sol_S11_reuse_oracle_build_20261026.py')),'oracle/reuse controller identity differs')
    require(data.get('source_inventory_sha256')==builder.INVENTORY_SHA and data.get('patch_sha256')==builder.PATCH_SHA,'frozen S11 receipt differs')
    require(sha(build/'libforge_core.a')==b['core_archive']['sha256'],'oracle uses another core')
    oracle=data['material_oracle_compilation'];verify_oracle_plan(data['base'],build,oracle['argv'])
    commands=data.get('commands',[]);i=oracle.get('command_index')
    require(type(i) is int and 0<=i<len(commands) and commands[i]['argv']==oracle['argv'],'oracle command not observed')
    require(all(c.get('returncode')==0 and c.get('leader_reaped') is True and c.get('all_group_members_after_reap')==[] and not c.get('stop_reason') and not c.get('error') for c in commands),'oracle command failed/open')
    proof=load('s11_reuse_oracle_checker',SEALED/'forge_sol_S11_scalar_parity_20261026.py');proof.verify_oracle_compilation(oracle,'baseline')
    require(oracle['source']==str(builder.ORACLE) and oracle['sha256']==builder.ORACLE_SHA,'oracle source changed')
    mp=build/'forge_sol_S11_materialkey_oracle.map';require(oracle['map_path']==str(mp) and sha(mp)==oracle['map_sha256'],'oracle link map changed')
    check=proof.verify_link_map(mp.read_text(),build/'libforge_core.a')
    require(data['target_artifacts']==artifact_inventory(b,build),'oracle/reused artifact inventory differs')
    return {'data':data,'source':Path(b['source']),'build':build,'build_receipt_path':str(receipt_path),'FIRST_receipt_path':str(first_path),'build_receipt_sha256':sha(receipt_path),'FIRST_receipt_sha256':sha(first_path),'link_map_audit':check,'reuse_classification':'REUSE_NOT_NEW_RUN'}
