#!/usr/bin/env python3
"""A1 exact-node matrix: fixed crew pins plus the committed R5A single-option pins.
IDEA_SOURCE: supplied Forge round-three qualification contract and same-repo R5A gate specs.
This is identity testing, never an Elo or speed estimate. Every run uses a fresh engine.
"""
import argparse, datetime, hashlib, json, pathlib, re, subprocess
from zoneinfo import ZoneInfo
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('engine',type=pathlib.Path); p.add_argument('out',type=pathlib.Path)
p.add_argument('--gate-specs',type=pathlib.Path,required=True)
p.add_argument('--source',required=True); a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
exe=a.engine.resolve(); digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
binary_hash=digest(exe); depths=[11,13,16,20,22]; off=[312866,862329,3024920,12389307,34048354]
spec=json.loads(a.gate_specs.read_text())
cases=[('OFF',[],off),('SingularV2',['SingularV2=1'],[404121,1005954,4120585,11497954,34264955]),
       ('N1',['BundlePreset=N1'],[277579,814055,2651984,18648191,40304213]),
       ('N1_then_OFF',['BundlePreset=N1','BundlePreset=OFF'],off),
       ('SmpV2_T1',['SmpV2=true'],off),('TmSoftHardClamp',['TmSoftHardClamp=true'],off),
       ('CorrMargins_OFF_Scale100',['CorrMargins=0','CorrMarginsScale=100'],off)]
for gate in spec['gates']:
    opts=[x.removeprefix('option.') for x in gate['cand']['options']]
    if gate['name']=='CorrMargins=1': opts.append('CorrMarginsScale=100')
    assert gate['prebench_depths']==depths and gate['prebench']['cand_off']==off
    cases.append((gate['id'],opts,gate['prebench']['cand_on']))
assert len({x[0] for x in cases})==len(cases)
record={'kind':'fixed-reference identity only; timings are not speed evidence','source_commit':a.source,
        'binary':str(exe),'binary_sha256':binary_hash,'gate_specs_sha256':digest(a.gate_specs),
        'started_pt':datetime.datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),
        'cases':[{'name':n,'options':o,'pins':v} for n,o,v in cases],'runs':[],'status':'RUNNING'}
def save(): (a.out/'results.json').write_text(json.dumps(record,indent=2)+'\n')
save()
for name,opts,pins in cases:
    assert len(pins)==len(depths)
    for depth,pin in zip(depths,pins):
        assert digest(exe)==binary_hash,'Executable changed during matrix'
        settings=['setoption name '+x.split('=',1)[0]+' value '+x.split('=',1)[1] for x in opts]
        commands='\n'.join(['uci','setoption name Threads value 1','setoption name Hash value 16',
                          'setoption name OwnBook value false',*settings,'isready',f'bench {depth}','quit',''])
        stem=a.out/f'{name}_d{depth}'; stem.with_suffix('.stdin').write_text(commands)
        started=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).isoformat()
        try:
            r=subprocess.run([str(exe)],input=commands.encode(),capture_output=True,timeout=300)
        except subprocess.TimeoutExpired as exc:
            stem.with_suffix('.stdout').write_bytes(exc.stdout or b''); stem.with_suffix('.stderr').write_bytes(exc.stderr or b'')
            record['status']='FAIL_TIMEOUT';save();raise
        stem.with_suffix('.stdout').write_bytes(r.stdout); stem.with_suffix('.stderr').write_bytes(r.stderr)
        found=re.findall(rb'^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)\s*$',r.stdout,re.M)
        bad=bool(re.search(rb'^info string (?:unknown option|invalid value|.*refused)',r.stdout,re.M))
        row={'case':name,'depth':depth,'expected_nodes':pin,'returncode':r.returncode,'started_pt':started,
             'matches':[list(map(int,x)) for x in found],'invalid_or_refused_option':bad}
        row['pass']=r.returncode==0 and len(found)==1 and int(found[0][0])==depth and int(found[0][1])==pin and not bad and digest(exe)==binary_hash
        record['runs'].append(row); save();print(json.dumps(row),flush=True)
        if not row['pass']:
            record['status']='FAIL';save();raise SystemExit(1)
record['status']='PASS';record['finished_pt']=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).isoformat();save()
