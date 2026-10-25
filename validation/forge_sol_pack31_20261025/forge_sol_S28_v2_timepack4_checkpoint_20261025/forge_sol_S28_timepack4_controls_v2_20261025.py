from pathlib import Path
import base64,hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent;R=ROOT/'forge_sol_S28_timepack4_patchwork_20261025'
P=ROOT.parent/'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files'
BASES={'L':P/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src','Lp':P/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src','B':P/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
OLD=Path('/workspace/dwqww/releases/forge_sol_pack31_20261025/S28/forge_sol_S28_rebase_e48f006_timepack4_20261025.patch');NAMES=['CMakeLists.txt','IDEA_SOURCE.md','include/forge/search.hpp','src/search.cpp'];PARA='timepack4: TmDecisiveWinStable = timepack3 TmDecisiveWin (own; DR P25A spec 450 cp / depth 8) + CR F3 skip on falling eval or best-move change; own code, no engine code copied'
def raw(b):return {'encoding':'base64','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
def run(label,argv,cwd):
 p=subprocess.run(argv,cwd=cwd,capture_output=True);rows.append({'base':base,'label':label,'argv':argv,'cwd':str(cwd),'exit':p.returncode,'stdout':raw(p.stdout),'stderr':raw(p.stderr),'child_waited':True,'stream_capture_complete':True});return p
rows=[]
for base,source in BASES.items():
 out=R/f'forge_sol_S28_{base}_old_control_v2_20261025';out.mkdir(exist_ok=False)
 for name in NAMES:
  p=out/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
 (out/'tests').mkdir()
 if base=='L':
  assert run('private_git_init',['git','init','-q'],out).returncode==0
  assert run('private_git_index',['git','add','--',*NAMES],out).returncode==0
 p=run('old_git_check',['git','apply','--check',str(OLD)],out);assert p.returncode==0
 for tag,args in [('old_GNU_dryrun',['--dry-run']),('old_GNU_apply',[])]:assert run(tag,['patch','--batch','-p1','-F0','--input',str(OLD),*args],out).returncode==0
 p=run('old_required_git_headers_RED',[sys.executable,'-B','-c','from pathlib import Path; p=Path('+repr(str(OLD))+').read_bytes(); assert b"diff --git a/tests/timepack4_tests.cpp b/tests/timepack4_tests.cpp" in p and b"new file mode 100644" in p, "required Git new-file headers absent"'],out);assert p.returncode==1
 p=run('old_required_IDEA_RED',[sys.executable,'-B','-c','from pathlib import Path; assert '+repr(PARA)+' in Path("IDEA_SOURCE.md").read_text(), "requested timepack4 paragraph absent"'],out);assert p.returncode==1
record={'status':'OBSERVED_OLD_GIT_GNU_PASS_REQUIRED_FORMAT_IDEA_RED','old_patch_sha256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'records':rows,'old_Git_rejection_claim':False,'scope':'Only minimal patch-target files. Git accepts the legacy conventional unified patch; required explicit new-file format and IDEA paragraph fail independently. No build/native execution.'}
(R/'forge_sol_S28_timepack4_old_controls_v2_20261025.json').write_text(json.dumps(record,indent=2)+'\n');print(record['status'])
