"""Check each standalone experiment against each exact source base, without builds."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

OUT=Path(__file__).resolve().parent
F=Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
BASES={'L':F/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src',
       'Lprime':F/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src',
       'B':F/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
ROOT=Path('/tmp/forge_sol_S10_patchchecks_v3_20261026')
def hashes(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
def main():
 ROOT.mkdir(exist_ok=False);before={label:hashes(base) for label,base in BASES.items()};rows=[]
 features=json.loads((OUT/'forge_sol_S10_candidate_inventory_20261026.json').read_text())
 for feature in features:
  for label,base in BASES.items():
   dst=ROOT/feature['key']/label;shutil.copytree(base,dst)
   for kind,cmd in [('gitcheck',['git','-c','gc.auto=0','apply','--check',feature['patch']]),
                    ('GNUdry',['patch','--batch','--dry-run','-p1','-F0','-i',feature['patch']]),
                    ('GNUapply',['patch','--batch','-p1','-F0','-i',feature['patch']])]:
    result=subprocess.run(cmd,cwd=dst,capture_output=True,timeout=20)
    prefix=OUT/('forge_sol_S10_'+feature['key']+'_'+label+'_'+kind+'_v2_20261026')
    prefix.with_suffix('.stdout').write_bytes(result.stdout);prefix.with_suffix('.stderr').write_bytes(result.stderr)
    rows.append({'feature':feature['key'],'base':label,'kind':kind,'returncode':result.returncode,'command':cmd,'view':str(dst)})
    if result.returncode:raise AssertionError(rows[-1])
   final=hashes(dst)
   changed={p for p in before[label] if final.get(p)!=before[label][p]}
   expected=set(feature['source_after'])
   if changed!=expected:raise AssertionError((label,changed,expected))
   backups=set(final)-set(before[label])
   if any(not p.endswith('.orig') or final[p]!=before[label].get(p[:-5]) for p in backups):
    raise AssertionError(('unexpected new file or altered GNU backup',backups))
   # B intentionally retains its extra target and repaired search buffer.
   rows.append({'feature':feature['key'],'base':label,'kind':'source_freeze','files':final,'changed_files':sorted(changed)})
 after={label:hashes(base) for label,base in BASES.items()}
 if after!=before:raise AssertionError('original input modified')
 result={'status':'PASS','native_launched':False,'rows':rows,'original_sources_unchanged':after==before,'original_source_freezes':before,
         'prior_attempt':'forge_sol_S10_first_apply_observation_20261026.json'}
 (OUT/'forge_sol_S10_patchcheck_v3_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS:12 independent patched source views;36 checks/applications; original sources unchanged; no native compile/runtime')
if __name__=='__main__':main()
