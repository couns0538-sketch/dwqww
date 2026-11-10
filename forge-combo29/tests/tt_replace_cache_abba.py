#!/usr/bin/env python3
"""Finite coordinated cloud timing diagnostic, not acceptance evidence."""
import hashlib,json,os,pathlib,re,statistics,subprocess,time
root=pathlib.Path('/workspace/shared/forge-build/tt-replace-cache')
out=pathlib.Path(__file__).with_name('tt_replace_cache_abba.json')
bins={k:root/f'engine{i}' for i,k in enumerate('AB')}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={'A':'1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6','B':'7dadb780b66205a78122cc28c14201fcaf59ee883f31321a1931db43ec98d01c'}
assert {k:sha(v) for k,v in bins.items()}==expected
cpu=min(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpu})
report={'label':'DIAGNOSTIC ONLY; no acceptance/speed/Elo claim','cpu':cpu,'binaries':{k:{'path':str(v),'sha256':expected[k]} for k,v in bins.items()},'runs':[],'summary':{}}
for nnue in (True,False):
    command=f'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nsetoption name UseNNUE value {str(nnue).lower()}\nbench 16\nquit\n'
    # One unmeasured warmup per binary and evaluation mode.
    for binary in bins.values(): subprocess.run([str(binary)],input=command,text=True,stdout=subprocess.DEVNULL,check=True)
    for cycle in range(3):
        for label in 'ABBA':
            begin=time.perf_counter_ns()
            p=subprocess.run([str(bins[label])],input=command,text=True,capture_output=True,check=True)
            elapsed=(time.perf_counter_ns()-begin)/1e9
            match=re.search(r'info string bench depth 16 nodes (\d+)',p.stdout); assert match,p.stdout
            nodes=int(match[1]);assert nodes==(3024920 if nnue else 2448617)
            report['runs'].append({'nnue':nnue,'cycle':cycle,'label':label,'wall_seconds':elapsed,'nodes':nodes,'stdout':p.stdout,'stderr':p.stderr,'stdin':command})
            out.write_text(json.dumps(report,separators=(',',':'))+'\n')
    rows=[r for r in report['runs'] if r['nnue']==nnue]
    means={label:statistics.mean(r['wall_seconds'] for r in rows if r['label']==label) for label in 'AB'}
    report['summary'][str(nnue)]={'mean_seconds':means,'B_over_A':means['B']/means['A'],'cycle_B_over_A':[statistics.mean(r['wall_seconds'] for r in rows if r['cycle']==c and r['label']=='B')/statistics.mean(r['wall_seconds'] for r in rows if r['cycle']==c and r['label']=='A') for c in range(3)]}
assert {k:sha(v) for k,v in bins.items()}==expected
report['post_hash_verified']=True
out.write_text(json.dumps(report,separators=(',',':'))+'\n')
print(json.dumps(report['summary'],indent=2))
