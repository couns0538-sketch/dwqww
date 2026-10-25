from pathlib import Path
import base64,hashlib,json,shutil,subprocess
R=Path(__file__).resolve().parent/'forge_sol_S28_timepack4_patchwork_20261025';R.mkdir(exist_ok=False)
P=R.parents[1]/'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files'
BASES={'L':P/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src','Lp':P/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src','B':P/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
OLD=Path('/workspace/dwqww/releases/forge_sol_pack31_20261025/S28/forge_sol_S28_rebase_e48f006_timepack4_20261025.patch');assert hashlib.sha256(OLD.read_bytes()).hexdigest()=='791f432b6c82f76e478c25bee98a0439e2c91a42abb662fbeeafc24e8b6638c9'
NAMES=['CMakeLists.txt','IDEA_SOURCE.md','include/forge/search.hpp','src/search.cpp']
def raw(b):return {'encoding':'base64','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
rows=[]
for base,source in BASES.items():
 out=R/f'forge_sol_S28_{base}_old_apply_v2_20261025';out.mkdir()
 for name in NAMES:
  p=out/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
 (out/'tests').mkdir()
 for label,argv in [('old_git_check',['git','apply','--check',str(OLD)]),('old_GNU_dryrun',['patch','--batch','-p1','-F0','--dry-run','--input',str(OLD)]),('old_GNU_apply',['patch','--batch','-p1','-F0','--input',str(OLD)])]:
  p=subprocess.run(argv,cwd=out,capture_output=True);row={'base':base,'label':label,'argv':argv,'cwd':str(out),'exit':p.returncode,'stdout':raw(p.stdout),'stderr':raw(p.stderr),'child_waited':True,'stream_capture_complete':True};rows.append(row)
  assert (p.returncode!=0 if label=='old_git_check' else p.returncode==0),row
record={'status':'PASS_OLD_GIT_RED_GNU_ZERO_FUZZ_PASS_ALL_THREE','old_patch_path':str(OLD),'old_patch_sha256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'records':rows,'scope':'Only minimal patch-target files; private Git application checks; no build/native engine or benchmark; immutable v1 not modified'}
(R/'forge_sol_S28_timepack4_old_controls_v2_20261025.json').write_text(json.dumps(record,indent=2)+'\n');print(record['status'])
