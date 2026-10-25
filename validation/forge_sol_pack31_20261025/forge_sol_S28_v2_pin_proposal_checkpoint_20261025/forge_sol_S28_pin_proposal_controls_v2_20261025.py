from pathlib import Path
import base64,hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parent;R=ROOT/'forge_sol_S28_pin_proposal_patchwork_20261025';R.mkdir(exist_ok=False)
P=ROOT.parent/'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files';BASES={'Lp':P/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src','B':P/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
PROPOSAL=P/'22_e48f006_transition_PROPOSED/e48f006_pin_rerecord_PROPOSED.diff';b=PROPOSAL.read_bytes();assert hashlib.sha256(b).hexdigest()=='692b164b2601cf84411a7ea8c4b7892b255a219b2a07e5bdf7167b2cad77a35e'
NAMES=['README.md','IDEA_SOURCE.md','tests/tests.cpp','tools/rerecord_pins.py'];rows=[]
def raw(b):return {'encoding':'base64','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
for base,source in BASES.items():
 out=R/f'forge_sol_S28_{base}_original_pin_control_v2_20261025';out.mkdir()
 for name in NAMES:
  q=out/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,q)
 for label,argv in [('original_git_check',['git','apply','--check',str(PROPOSAL)]),('original_GNU_dryrun',['patch','--batch','-p1','-F0','--dry-run','--input',str(PROPOSAL)])]:
  p=subprocess.run(argv,cwd=out,capture_output=True);rows.append({'base':base,'label':label,'argv':argv,'cwd':str(out),'exit':p.returncode,'stdout':raw(p.stdout),'stderr':raw(p.stderr),'child_waited':True,'stream_capture_complete':True});assert (p.returncode==0 if base=='B' else p.returncode!=0)
 if base=='B':
  argv=['patch','--batch','-p1','-F0','--input',str(PROPOSAL)];p=subprocess.run(argv,cwd=out,capture_output=True);rows.append({'base':base,'label':'original_GNU_apply','argv':argv,'cwd':str(out),'exit':p.returncode,'stdout':raw(p.stdout),'stderr':raw(p.stderr),'child_waited':True,'stream_capture_complete':True});assert p.returncode==0
(R/'forge_sol_S28_pin_original_controls_v2_20261025.json').write_text(json.dumps({'status':'PASS_OBSERVED_LP_README_RED_B_APPLIES','original_proposal_path':str(PROPOSAL),'original_sha256':hashlib.sha256(b).hexdigest(),'original_md5':hashlib.md5(b).hexdigest(),'records':rows,'scope':'Current merged Lp/B minimal target files; Lp README context failure observed, B original proposal applied; no native or accepted-tree mutation'},indent=2)+'\n');print('PASS actual original Lp README RED, original B proposal application PASS')
