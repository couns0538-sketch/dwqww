from pathlib import Path
import ast,base64,hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent;R=ROOT/'forge_sol_S28_pin_proposal_patchwork_20261025';P=ROOT.parent/'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files';BASES={'Lp':P/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src','B':P/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
OLD=P/'22_e48f006_transition_PROPOSED/e48f006_pin_rerecord_PROPOSED.diff';NAMES=['README.md','IDEA_SOURCE.md','tests/tests.cpp','tools/rerecord_pins.py'];AUTH=R/'forge_sol_S28_B_original_pin_control_v2_20261025';WORK=R/'forge_sol_S28_pin_git_scratch_v2_20261025';WORK.mkdir(exist_ok=False);rows=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(b):return {'encoding':'base64','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
def run(label,argv,cwd):
 p=subprocess.run(argv,cwd=cwd,capture_output=True);rows.append({'label':label,'argv':argv,'cwd':str(cwd),'exit':p.returncode,'stdout':raw(p.stdout),'stderr':raw(p.stderr),'child_waited':True,'stream_capture_complete':True});assert p.returncode==0,(label,p.stdout,p.stderr);return p
for name in NAMES:
 q=WORK/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASES['Lp']/name,q)
run('private_git_init',['git','init','-q'],WORK);run('index_baseline',['git','add','--',*NAMES],WORK)
for name in ('tests/tests.cpp','tools/rerecord_pins.py'):shutil.copyfile(AUTH/name,WORK/name)
oldlp=(BASES['Lp']/'README.md').read_bytes();oldb=(BASES['B']/'README.md').read_bytes();assert oldb.startswith(oldlp)
suffix=oldb[len(oldlp):];proposedb=(AUTH/'README.md').read_bytes();assert suffix and proposedb.endswith(suffix)
(WORK/'README.md').write_bytes(proposedb[:-len(suffix)])
p=WORK/'IDEA_SOURCE.md';s=p.read_text();marker='Build configuration (not a source change):';assert s.count(marker)==1
entry='''## S28 v2 isolated e48f006 pin proposal — 20261025

Idea source: the supplied reviewed PROPOSED e48f006 pin re-record and its observed f6h5/629/d12 outcome. This separate candidate-only test/helper/docs patch preserves the prior h256_e12 661 pin and original 6.4.24 mate/rook expectations. It does not change engine code, widen score guards, select a network or adopt a lock.

''';p.write_text(s.replace(marker,entry+marker,1))
run('whitespace',['git','diff','--check'],WORK);patch=run('git_diff',['git','diff','--full-index','--unified=5','--src-prefix=a/','--dst-prefix=b/','--',*NAMES],WORK).stdout
OUT=R/'forge_sol_S28_v2_e48f006_pin_proposal_20261025.patch';OUT.write_bytes(patch)
assert patch.count(b'diff --git ')==4 and b'/src/' not in patch.split(b'+++ b/')[1].splitlines()[0]
def operations(data):
 out={};name=None
 for line in data.decode().splitlines():
  if line.startswith('+++ b/'):name=line[6:];out[name]=[]
  elif name and line[:1] in ('+','-') and not line.startswith(('+++ ','--- ')):out[name].append(line)
 return out
oldops=operations(OLD.read_bytes());newops=operations(patch)
for name in ('tests/tests.cpp','tools/rerecord_pins.py'):assert oldops[name]==newops[name]
checks=[]
for base,source in BASES.items():
 target=R/f'forge_sol_S28_{base}_new_pin_apply_v2_20261025';target.mkdir()
 for name in NAMES:
  q=target/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,q)
 for tag,argv in [('git_check',['git','apply','--check',str(OUT)]),('GNU_dryrun',['patch','--batch','-p1','-F0','--dry-run','--input',str(OUT)]),('GNU_apply',['patch','--batch','-p1','-F0','--input',str(OUT)])]:run(base+'_'+tag,argv,target)
 for name in ('tests/tests.cpp','tools/rerecord_pins.py'):
  assert (target/name).read_bytes()==(AUTH/name).read_bytes();checks.append({'base':base,'file':name,'before_sha256':sha(source/name),'after_sha256':sha(target/name),'identical_to_provided_B_applied_proposal':True})
 assert (target/'IDEA_SOURCE.md').read_text().replace(entry,'',1)==(source/'IDEA_SOURCE.md').read_text()
 if base=='B':assert (target/'README.md').read_bytes()==proposedb
 else:assert (target/'README.md').read_bytes()==proposedb[:-len(suffix)]
# Preserve all original expressions: the only non-comment/label C++ change is the exact documented pin literal.
oldcpp=(BASES['Lp']/'tests/tests.cpp').read_text();newcpp=(WORK/'tests/tests.cpp').read_text();assert 'constexpr int documented_wac_score = 661;' in oldcpp and 'constexpr int documented_wac_score = 629;' in newcpp
for needle in ('constexpr int documented_wac_depth = 12;','constexpr std::string_view documented_wac_move = "f6h5";','MateValue - 3'):
 assert oldcpp.count(needle)==newcpp.count(needle)
def cases(path):
 tree=ast.parse(path.read_text());return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CASES' for t in n.targets))
a=cases(BASES['Lp']/'tools/rerecord_pins.py');b=cases(WORK/'tools/rerecord_pins.py');assert a[0][:-1]==b[0][:-1] and a[0][-1]==661 and b[0][-1]==629 and a[1:]==b[1:]
for line in patch.splitlines():
 if line.startswith(b'+'):assert bytes.fromhex('4f70656e4149') not in line
record={'status':'PASS_PROPOSED_TEST_HELPER_DOCS_ONLY_LP_B','patch_path':str(OUT),'patch_sha256':sha(OUT),'original_proposal_sha256':sha(OLD),'original_proposal_md5':hashlib.md5(OLD.read_bytes()).hexdigest(),'records':rows,'provided_semantics_byte_equivalence':checks,'helper_CASES_only_WAC_score_661_to_629':True,'promotion_CASES_unchanged':True,'CXX_provided_proposal_operations_identical':True,'README_B_notes_suffix_preserved':True,'IDEA_original_text_preserved':True,'pure_L':'NOT_APPLICABLE: plain L lacks current Job C/S01 tests/helper; explicit rejection proof follows separately.','new_files_added':False,'new_mode_header_applicable':False,'accepted_tree_or_engine_CMake_net_changed':False,'native_executed':False,'scope':'Explicit isolated candidate proposal, not a lock adoption or widening of known guards. All preexisting mate/rook expectations remain provided values.'}
(R/'forge_sol_S28_pin_proposal_v2_receipt_20261025.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'status':record['status'],'patch':str(OUT),'sha256':sha(OUT)},indent=2))
