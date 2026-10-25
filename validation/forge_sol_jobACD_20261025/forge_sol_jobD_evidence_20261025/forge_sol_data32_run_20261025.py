from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,time
h=Path('/workspace/forge-jobACD-D-20261025');p=Path('/workspace/forge-jobACD-20261025/forge_sol_jobACD_pack_20261025/06_jobD/data32_sample/data32_sample_50k');ap=argparse.ArgumentParser();ap.add_argument('--threshold',type=int);a=ap.parse_args();tag='off' if a.threshold is None else 'threshold'+str(a.threshold);tool=h/'forge_sol_datafilter_20261025.py';out=h/('forge_sol_data32_filtered_'+tag+'_20261025')
command=['python3','-B',str(tool),'--train',*[str(q) for q in sorted(p.glob('t*.pos'))],'--holdout-pos',str(p/'h000.pos'),'--hce-dir',str(p),'--out',str(out),'--seed','20261025']
if a.threshold is not None:command+=['--disagreement-threshold',str(a.threshold)]
started=datetime.datetime.now(datetime.timezone.utc).isoformat();source=hashlib.sha256(tool.read_bytes()).hexdigest();t=time.monotonic();r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE);elapsed=time.monotonic()-t
(h/('forge_sol_data32_'+tag+'_20261025.stdout')).write_bytes(r.stdout);(h/('forge_sol_data32_'+tag+'_20261025.stderr')).write_bytes(r.stderr)
receipt={'utc_start':started,'argv':command,'tool_sha256':source,'tool_unchanged':hashlib.sha256(tool.read_bytes()).hexdigest()==source,'actual_exit':r.returncode,'elapsed_seconds':elapsed,'out':str(out),'real_013_014':'UNVERIFIED_ABSENT','source_sample':'supplied synthetic data32; h000 is stand-in holdout only'}
(h/('forge_sol_data32_'+tag+'_receipt_20261025.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));raise SystemExit(r.returncode)
