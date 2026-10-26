"""Read-only original sources; separate copied views for each apply mechanism."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=Path('/tmp/forge_sol_S11_materialkey_apply_20261026')
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
def main():
 inventory=json.loads((OUT/'forge_sol_S11_source_inventory_20261026.json').read_text())
 source_module={}
 exec(compile((OUT/'forge_sol_S11_generate_materialkey_20261026.py').read_bytes(),'S11_generator','exec'),source_module)
 ROOT.mkdir(exist_ok=False);rows=[]
 for label,base in source_module['BASES'].items():
  if hashes(base)!=inventory['original_source_freezes'][label]:raise ValueError('base drift')
  view=ROOT/label;shutil.copytree(base,view)
  for kind,argv in [('Gitcheck',['git','-c','gc.auto=0','apply','--check',inventory['patch']]),('GNUdry',['patch','--batch','--dry-run','-p1','-F0','-i',inventory['patch']]),('GNUapply',['patch','--batch','-p1','-F0','-i',inventory['patch']])]:
   result=subprocess.run(argv,cwd=view,capture_output=True,timeout=20)
   prefix=OUT/('forge_sol_S11_'+label+'_'+kind+'_20261026')
   prefix.with_suffix('.stdout').write_bytes(result.stdout);prefix.with_suffix('.stderr').write_bytes(result.stderr)
   rows.append({'base':label,'kind':kind,'argv':argv,'returncode':result.returncode,'view':str(view)})
   if result.returncode:raise ValueError('apply failure: '+label+kind)
  actual=hashes(view);expected=inventory['source_freezes'][label]
  backups=set(actual)-set(expected)
  if any(not p.endswith('.orig') or actual[p]!=inventory['original_source_freezes'][label].get(p[:-5]) for p in backups):raise ValueError('unexpected extra file')
  if {p:actual[p] for p in expected}!=expected:raise ValueError('applied bytes differ from prepared source')
  if hashes(base)!=inventory['original_source_freezes'][label]:raise ValueError('original input changed')
 (OUT/'forge_sol_S11_applycheck_result_20261026.json').write_text(json.dumps({'status':'PASS','native_compiler_or_engine_runs':0,'checks_and_applications':9,'originals_unchanged':True,'rows':rows},indent=2)+'\n')
 print('PASS:9 Git/GNU checks/applications; L/Lprime/B source bytes match; originals unchanged')
if __name__=='__main__':main()
