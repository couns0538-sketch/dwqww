#!/usr/bin/env python3
"""Run the unchanged supplied v3b CLI for three CPU-only smoke steps."""
import argparse,hashlib,json,math,os,pathlib,re,shutil,subprocess,sys
TRAINER='5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f'
def md5(p):return hashlib.md5(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--trainer',type=pathlib.Path,required=True);p.add_argument('--data',type=pathlib.Path,required=True);p.add_argument('--holdout',type=pathlib.Path,required=True);p.add_argument('--holdout-hce',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
 if hashlib.sha256(a.trainer.read_bytes()).hexdigest()!=TRAINER:raise RuntimeError('Unexpected trainer revision; refusing silent substitution')
 a.out.mkdir(parents=True,exist_ok=False);inputs=a.out/'forge_sol_smoke_inputs_20261025';inputs.mkdir();run=a.out/'forge_sol_cpu_steps_20261025'
 candidates=sorted(a.data.glob('*.pos'));candidates=[q for q in candidates if q.name!=a.holdout.name]
 if not candidates:raise RuntimeError('No filtered training POS files')
 originals={};copied=[]
 for pos in candidates:
  for src in [pos,pos.with_suffix('.hce')]:
   originals[str(src.resolve())]=md5(src);dst=inputs/src.name
   if dst.exists():raise RuntimeError('Ambiguous input basename')
   shutil.copyfile(src,dst)
  copied.append(inputs/pos.name)
 for src,suffix in [(a.holdout,'.pos'),(a.holdout_hce,'.hce')]:
  originals[str(src.resolve())]=md5(src);dst=inputs/('h_smoke_holdout_20261025'+suffix)
  if dst.exists():raise RuntimeError('Input collision')
  shutil.copyfile(src,dst)
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['CUDA_VISIBLE_DEVICES']='';env['OMP_NUM_THREADS']='1';env['MKL_NUM_THREADS']='1';env['TORCH_HOME']=str(a.out/'forge_sol_torch_cache_20261025');env['XDG_CACHE_HOME']=str(a.out/'forge_sol_cache_20261025')
 cmd=[sys.executable,'-B',str(a.trainer.resolve()),'--train',*[str(q.resolve()) for q in copied],'--holdout',str((inputs/'h_smoke_holdout_20261025.pos').resolve()),'--hce-dir',str(inputs.resolve()),'--device','cpu','--shape','256','--residual','--adam-impl','torch','--epochs','1','--batch-size','256','--steps-per-epoch','3','--max-train','4096','--val-positions','512','--warmup-steps','0','--seed','20261025','--init-check','--run-dir',str(run.resolve())]
 result={'status':'UNVERIFIED','trainer_sha256':TRAINER,'argv':cmd,'training_gain_claim':False,'original_input_md5':originals}
 try:
  child=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  (a.out/'forge_sol_data32_cpu_smoke_20261025.stdout').write_text(child.stdout);(a.out/'forge_sol_data32_cpu_smoke_20261025.stderr').write_text(child.stderr);print(child.stdout,end='');print(child.stderr,file=sys.stderr,end='');result['actual_exit']=child.returncode
  if child.returncode!=0:raise RuntimeError('Actual v3b CPU smoke failed; original logs retained')
  loss=re.findall(r'EPOCH 1/1 .*train_mse=([0-9.eE+-]+)',child.stdout)
  if len(loss)!=1 or not math.isfinite(float(loss[0])):raise RuntimeError('Missing finite actual trainer loss')
  if 'Finished: 768 positions' not in child.stdout:raise RuntimeError('Expected three real256-position steps')
  result['train_mse']=float(loss[0]);result['steps']=3;result['positions']=768;result['input_hashes_unchanged']=all(md5(pathlib.Path(k))==v for k,v in originals.items())
  if not result['input_hashes_unchanged']:raise RuntimeError('Input changed during smoke')
  result['status']='PASS_ACTUAL_UNCHANGED_V3B_CPU_CLI'
 finally:(a.out/'forge_sol_data32_cpu_smoke_20261025.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['argv','original_input_md5']},indent=2))
if __name__=='__main__':main()
