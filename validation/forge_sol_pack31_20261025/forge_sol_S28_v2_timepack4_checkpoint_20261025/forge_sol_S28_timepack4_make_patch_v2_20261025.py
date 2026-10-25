from pathlib import Path
import base64,hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent;R=ROOT/'forge_sol_S28_timepack4_patchwork_20261025';P=ROOT.parent/'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files'
BASES={'L':P/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src','Lp':P/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src','B':P/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
OLD=Path('/workspace/dwqww/releases/forge_sol_pack31_20261025/S28/forge_sol_S28_rebase_e48f006_timepack4_20261025.patch');NAMES=['CMakeLists.txt','IDEA_SOURCE.md','include/forge/search.hpp','src/search.cpp'];NEWFILE='tests/timepack4_tests.cpp';PARA='timepack4: TmDecisiveWinStable = timepack3 TmDecisiveWin (own; DR P25A spec 450 cp / depth 8) + CR F3 skip on falling eval or best-move change; own code, no engine code copied'
WORK=R/'forge_sol_S28_timepack4_git_scratch_v2_20261025';WORK.mkdir(exist_ok=False);rows=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(b):return {'encoding':'base64','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
def run(label,argv,cwd):
 p=subprocess.run(argv,cwd=cwd,capture_output=True);rows.append({'label':label,'argv':argv,'cwd':str(cwd),'exit':p.returncode,'stdout':raw(p.stdout),'stderr':raw(p.stderr),'child_waited':True,'stream_capture_complete':True});assert p.returncode==0,(label,p.stderr);return p
for name in NAMES:
 p=WORK/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASES['Lp']/name,p)
(WORK/'tests').mkdir();run('private_git_init',['git','init','-q'],WORK);run('baseline_index',['git','add','--',*NAMES],WORK);run('reuse_v1_body',['patch','--batch','-p1','-F0','--input',str(OLD)],WORK)
entry='\n\n## S28 v2 timepack4 idea source — 20261025\n\n'+PARA+'\n';p=WORK/'IDEA_SOURCE.md';s=p.read_text();at=s.index('\n');p.write_text(s[:at]+entry+s[at:])
run('intent_to_add',['git','add','-N','--',NEWFILE],WORK);run('diff_whitespace',['git','diff','--check'],WORK)
patch=run('git_diff',['git','diff','--full-index','--unified=5','--src-prefix=a/','--dst-prefix=b/','--',*NAMES,NEWFILE],WORK).stdout
assert b'new file mode 100644' in patch and b'diff --git a/tests/timepack4_tests.cpp b/tests/timepack4_tests.cpp' in patch
out=R/'forge_sol_S28_v2_timepack4_20261025.patch';out.write_bytes(patch)
def operations(data):
 result={};current=None
 for line in data.decode().splitlines():
  if line.startswith('+++ b/'):current=line[6:];result[current]=[]
  elif current and line[:1] in ('+','-') and not line.startswith(('+++ ','--- ')):result[current].append(line)
 return result
oldops=operations(OLD.read_bytes());newops=operations(patch);equivalence=[]
for name in ('include/forge/search.hpp','src/search.cpp',NEWFILE):
 assert oldops[name]==newops[name];equivalence.append({'file':name,'decoded_add_delete_operations_identical':True,'operations_sha256':hashlib.sha256(json.dumps(oldops[name],separators=(',',':')).encode()).hexdigest()})
assert oldops['CMakeLists.txt']==newops['CMakeLists.txt']
source_rows=[]
for base,source in BASES.items():
 target=R/f'forge_sol_S28_{base}_new_apply_v2_20261025';target.mkdir()
 for name in NAMES:
  p=target/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
 (target/'tests').mkdir()
 for tag,argv in [('git_check',['git','apply','--check',str(out)]),('GNU_dryrun',['patch','--batch','-p1','-F0','--dry-run','--input',str(out)]),('GNU_apply',['patch','--batch','-p1','-F0','--input',str(out)])]:run(base+'_'+tag,argv,target)
 run(base+'_required_format_and_IDEA_GREEN',[sys.executable,'-B','-c','from pathlib import Path; p=Path('+repr(str(out))+').read_bytes(); assert b"new file mode 100644" in p; assert '+repr(PARA)+' in Path("IDEA_SOURCE.md").read_text()'],target)
 assert (target/'IDEA_SOURCE.md').read_text().replace(entry,'',1)==(source/'IDEA_SOURCE.md').read_text()
 oldtree=R/f'forge_sol_S28_{base}_old_control_v2_20261025'
 for name in ('CMakeLists.txt','include/forge/search.hpp','src/search.cpp',NEWFILE):
  assert (target/name).read_bytes()==(oldtree/name).read_bytes();source_rows.append({'base':base,'file':name,'old_applied_sha256':sha(oldtree/name),'new_applied_sha256':sha(target/name),'byte_identical':True})
for line in patch.splitlines():
 if line.startswith(b'+'):assert bytes.fromhex('4f70656e4149') not in line
record={'status':'PASS_DOC_FORMAT_ONLY_ALL_THREE_BASES','patch_path':str(out),'patch_sha256':sha(out),'old_patch_path':str(OLD),'old_patch_sha256':sha(OLD),'required_IDEA_paragraph':PARA,'records':rows,'decoded_non_IDEA_non_CMake_operations':equivalence,'CMake_add_delete_operations_identical':True,'applied_source_equivalence':source_rows,'optional_S28_4':'DEFERRED: no min/ponder/include changes','native_build_or_engine_executed':False,'source_notes_preserved_all_bases':True,'legacy_Git_control':'Observed PASS; explicit header/IDEA requirement was RED, not Git rejection.'}
(R/'forge_sol_S28_timepack4_v2_patch_receipt_20261025.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'status':record['status'],'patch':str(out),'sha256':sha(out),'cpp_equivalence':True,'optional4':'DEFERRED'},indent=2))
