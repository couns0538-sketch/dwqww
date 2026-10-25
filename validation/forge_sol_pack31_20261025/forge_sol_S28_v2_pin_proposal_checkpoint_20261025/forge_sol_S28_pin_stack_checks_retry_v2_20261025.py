from pathlib import Path
import base64,hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parent;R=ROOT/'forge_sol_S28_pin_proposal_patchwork_20261025';P=ROOT.parent/'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files'
BASES={'L':P/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src','Lp':P/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src','B':P/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
PIN=R/'forge_sol_S28_v2_e48f006_pin_proposal_20261025.patch';TIME=ROOT/'forge_sol_S28_timepack4_patchwork_20261025/forge_sol_S28_v2_timepack4_20261025.patch';NAMES=['README.md','IDEA_SOURCE.md','tests/tests.cpp','tools/rerecord_pins.py','CMakeLists.txt','include/forge/search.hpp','src/search.cpp'];rows=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(b):return {'encoding':'base64','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
def clone(source,out):
 out.mkdir()
 for name in NAMES:
  p=source/name
  if p.is_file():q=out/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 (out/'tests').mkdir(exist_ok=True)
def run(label,argv,cwd,ok=True):
 p=subprocess.run(argv,cwd=cwd,capture_output=True);rows.append({'label':label,'argv':argv,'cwd':str(cwd),'exit':p.returncode,'stdout':raw(p.stdout),'stderr':raw(p.stderr),'child_waited':True,'stream_capture_complete':True});assert (p.returncode==0 if ok else p.returncode!=0),(label,p.stdout,p.stderr)
plain=R/'forge_sol_S28_plainL_pin_reject_retry_v2_20261025';clone(BASES['L'],plain);run('plainL_expected_reject',['git','apply','--check',str(PIN)],plain,ok=False)
results={}
for base in ('Lp','B'):
 final=[]
 for order,patches in [('timepack_then_pin',[TIME,PIN]),('pin_then_timepack',[PIN,TIME])]:
  out=R/f'forge_sol_S28_{base}_{order}_retry_v2_20261025';clone(BASES[base],out)
  for index,patch in enumerate(patches):
   for tag,argv in [('git_check',['git','apply','--check',str(patch)]),('GNU_dryrun',['patch','--batch','--no-backup-if-mismatch','-p1','-F0','--dry-run','--input',str(patch)]),('GNU_apply',['patch','--batch','--no-backup-if-mismatch','-p1','-F0','--input',str(patch)])]:run(base+'_'+order+'_'+str(index)+'_'+tag,argv,out)
  final.append({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
 assert final[0]==final[1];results[base]={'both_order_file_hashes_identical':True,'files':final[0]}
(R/'forge_sol_S28_pin_stack_receipt_v2_20261025.json').write_text(json.dumps({'status':'PASS_BOTH_ORDERS_CURRENT_LP_B_PLAINL_EXCLUDED','pin_patch_sha256':sha(PIN),'timepack_patch_sha256':sha(TIME),'records':rows,'results':results,'native_executed':False,'scope':'Minimal union patch targets, both orders independently dual-checked. No accepted tree/core/network/CMake changes from the pin proposal; plain L intentionally lacks required Job C/S01 tests/helper.'},indent=2)+'\n');print('PASS both patch orders Lp/B; expected plainL pin rejection')
