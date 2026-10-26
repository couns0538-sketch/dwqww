"""Check or apply five SHA-guarded metadata replacements; never invokes Git."""
import argparse,hashlib,json,os,stat
from pathlib import Path
BASE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--safe-build-window',action='store_true');a=p.parse_args();o=json.loads((BASE/'staging_plan.json').read_text());repo=Path(o['repo']);changes=o['changes']
 allowed={'validation/forge_sol_pack31_20261025/forge_sol_S00_checkpoint_20261025.json','releases/forge_sol_pack31_20261025/forge_sol_pack31_index_20261025.md','docs/CURRENT_BASELINE.md','docs/NEXT_EXPERIMENTS.md','docs/EXPERIMENT_LEDGER.md'}
 assert {x['target'] for x in changes}==allowed
 for x in changes:
  dst=repo/x['target'];src=BASE/x['replacement'];old=BASE/x['before_snapshot']
  assert not dst.is_symlink() and repo.resolve() in dst.resolve().parents
  assert digest(dst)==x['before_sha256'],'STALE target '+str(dst)
  assert digest(old)==x['before_sha256'] and digest(src)==x['after_sha256']
 if not a.apply:print(json.dumps({'status':'CHECK_ONLY_PASS','targets':len(changes),'note':'No writes. Root must verify safe future BUILD window before --apply --safe-build-window.'}));return
 if not a.safe_build_window:p.error('--apply requires explicit --safe-build-window; root owns actual timing clearance')
 for x in changes:
  dst=repo/x['target'];tmp=dst.with_name(dst.name+'.checkpoint-staging.tmp')
  with tmp.open('xb') as f:f.write((BASE/x['replacement']).read_bytes());f.flush();os.fsync(f.fileno())
  os.chmod(tmp,x['mode']);os.replace(tmp,dst);assert digest(dst)==x['after_sha256']
 print(json.dumps({'status':'APPLIED_METADATA_ONLY','targets':len(changes),'Git_called':False,'backups':'Original exact preimages remain under before/ in this staging folder.'}))
if __name__=='__main__':main()
