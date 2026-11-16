"""Re-judge the gap with the correct reference: R2 is only valid when the file's searches had a DEPTH
target (so depth can be a completeness reference). Files whose searches used `go nodes`/`movetime` cannot
be judged by R2 at all -- a node-budget search legitimately stops at any depth."""
import json,os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/10/regimes')
from is_unfinished import records
ROOT='/agent/repos/dwqww'
rows=json.load(open('/agent/repos/dwqww/forge-combo29/swarm/10/regimes/scan/scan_nodepth.json'))
res={'depth_target_files':[], 'non_depth_target_files':[], 'no_go_echo_files':[]}
for r in rows:
    p=os.path.join(ROOT,r['file'])
    txt=open(p,errors='replace').read()
    kinds=set(re.findall(r"^\s*go (\w+)", txt, re.M))
    if not kinds:
        res['no_go_echo_files'].append(r)
    elif 'depth' in kinds:
        res['depth_target_files'].append(r)
    else:
        res['non_depth_target_files'].append(r)
def tot(lst,k): return sum(x[k] for x in lst)
print("GAP = files with engine output but no recoverable requested depth")
print()
print("A) files whose searches used go nodes/movetime/softnodes (R2 INVALID -- depth is not the target):")
print("   files %d, records %d, records R2 wrongly flagged %d -> reclassified UNJUDGEABLE"
      %(len(res['non_depth_target_files']),tot(res['non_depth_target_files'],'records'),
        tot(res['non_depth_target_files'],'flagged')))
print()
print("B) files with go depth echoes but no parsable depth (should be 0):")
print("   files %d, records %d, flagged %d"%(len(res['depth_target_files']),
      tot(res['depth_target_files'],'records'),tot(res['depth_target_files'],'flagged')))
for r in res['depth_target_files']: print("   ",r['file'],r['records'],r['flagged'])
print()
print("C) files with NO go echo at all (command not logged -> UNJUDGEABLE):")
print("   files %d, records %d, records R2 flagged %d"%(len(res['no_go_echo_files']),
      tot(res['no_go_echo_files'],'records'),tot(res['no_go_echo_files'],'flagged')))
for r in res['no_go_echo_files']: print("   ",r['file'][-70:],r['records'],r['flagged'])
json.dump({k:[{kk:v[kk] for kk in ('file','records','judgeable_by_R2','flagged','file_max_depth')} for v in lst]
           for k,lst in res.items()},
          open('/agent/repos/dwqww/forge-combo29/swarm/10/regimes/scan/gap_classified.json','w'),indent=1)
