#!/usr/bin/env python3
"""Validate a recorded A/A then A/B ABBA experiment and summarize block ratios.
IDEA_SOURCE: crew's paired quiet-core timing contract. Original, offline-only code.
"""
import argparse,hashlib,json,math,os,re,statistics,sys
from pathlib import Path,PureWindowsPath

class Failed(Exception):pass

def need(ok,message):
    if not ok:raise ValueError(message)

def unique(pairs):
    out={}
    for key,value in pairs:
        need(key not in out,'duplicate JSON key');out[key]=value
    return out

def finite(text):
    value=float(text);need(math.isfinite(value),'nonfinite number');return value

def decode(text):
    return json.loads(text,object_pairs_hook=unique,parse_float=finite,
                      parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def identity(s):
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)+((s.st_ctime_ns,) if os.name=='posix' else ())

def digest(path):
    with path.open('rb') as f:
        before=identity(os.fstat(f.fileno()));h=hashlib.sha256()
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        if before!=identity(os.fstat(f.fileno())) or before!=identity(path.stat()):raise Failed('artifact changed while hashing')
    return h.hexdigest()

def artifact(root,ref,refs):
    need(isinstance(ref,dict),'artifact reference required');name=ref.get('path');sha=ref.get('sha256')
    need(isinstance(name,str) and name and not Path(name).is_absolute() and not PureWindowsPath(name).anchor and '\\' not in name and ':' not in name and '\x00' not in name,'artifact path must be relative forward-slash syntax')
    need(isinstance(sha,str) and re.fullmatch('[0-9a-fA-F]{64}',sha),'invalid artifact SHA-256');path=root/name
    try:
        if digest(path)!=sha.lower():raise Failed('artifact hash mismatch: '+name)
    except OSError as exc:raise Failed('artifact missing/unreadable: '+name) from exc
    refs.append((path,sha.lower()));return path

def measure(path,nodes,cpu,identities,protocol_sha):
    with path.open('r',encoding='utf-8') as stream:rows=[decode(line) for line in stream]
    positions=list(nodes);per_block=4*len(positions)
    need(len(rows)%per_block==0 and len(rows)//per_block>=10,'require at least 10 complete ABBA blocks')
    ratios=[];last_end=-1;first_start=None;run_nps=[]
    for block in range(len(rows)//per_block):
        rates=[]
        for run,arm in enumerate('ABBA'):
            total_nodes=total_ns=0
            for index,position in enumerate(positions):
                row=rows[block*per_block+run*len(positions)+index]
                need(isinstance(row,dict),'sample row must be an object')
                need(type(row.get('block')) is int and row['block']==block and type(row.get('run')) is int and row['run']==run and row.get('arm')==arm and row.get('position')==position,'sample order must be complete sequential ABBA in declared position order')
                for key,value in dict(identities[arm],protocol_sha256=protocol_sha).items():
                    if not isinstance(row.get(key),str) or row[key].lower()!=value:raise Failed('sample identity does not bind expected arm binary/network/options/protocol')
                if type(row.get('nodes')) is not int or row['nodes']!=nodes[position]:raise Failed('node mismatch: '+position)
                if type(row.get('threads')) is not int or row['threads']!=1 or type(row.get('logical_cpu')) is not int or row['logical_cpu']!=cpu:raise Failed('sample requires T1 and the selected single CPU')
                start,end,elapsed=row.get('start_ns'),row.get('end_ns'),row.get('wall_ns')
                need(all(type(x) is int for x in (start,end,elapsed)) and start>=0 and elapsed>0 and end-start==elapsed,'invalid or inconsistent monotonic timestamps')
                if start<last_end:raise Failed('sample intervals overlap or run out of order')
                if first_start is None:first_start=start
                last_end=end;total_nodes+=row['nodes'];total_ns+=elapsed
            rates.append(total_nodes*1e9/total_ns)
        ratio=math.exp((math.log(rates[1])+math.log(rates[2])-math.log(rates[0])-math.log(rates[3]))/2)
        ratios.append(ratio);run_nps.append(rates)
    quartiles=statistics.quantiles(ratios,n=4,method='inclusive');median=statistics.median(ratios)
    return {'blocks':len(ratios),'median_ratio':median,'median_change_pct':100*(median-1),
            'min_ratio':min(ratios),'max_ratio':max(ratios),'q1_ratio':quartiles[0],
            'q3_ratio':quartiles[2],'iqr_ratio':quartiles[2]-quartiles[0],
            'range_pct':100*(max(ratios)/min(ratios)-1),'block_ratios':ratios,
            'run_nps_abba':run_nps,'first_start_ns':first_start,'last_end_ns':last_end}

def check(filename):
    out={'status':'INVALID','scope':'Statistics of supplied hash-bound records; not independent proof of native execution, measured affinity, quietness, speed or Elo. Timing helper launches nothing.', 'strength_claim':'UNVERIFIED'}
    try:
        filename=Path(filename).absolute();root=filename.parent;refs=[];record=decode(filename.read_text(encoding='utf-8-sig'))
        need(isinstance(record,dict) and type(record.get('schema')) is int and record['schema']==1,'schema must be integer 1')
        for name in ('baseline','candidate','network','baseline_options','candidate_options','native_log','host_evidence'):artifact(root,record.get(name),refs)
        plan_path=artifact(root,record.get('protocol'),refs);plan=decode(plan_path.read_text(encoding='utf-8-sig'));need(isinstance(plan,dict),'protocol must be JSON object')
        host=record.get('host');need(isinstance(host,dict),'host evidence required')
        for key in ('os','cpu_model'):need(isinstance(host.get(key),str) and host[key].strip(),'host '+key+' required')
        cpu=host.get('logical_cpu');need(type(cpu) is int and cpu>=0,'single logical CPU required')
        if host.get('quiet_confirmed') is not True or type(host.get('threads')) is not int or host['threads']!=1:raise Failed('quiet single-core T1 prerequisite not confirmed')
        nodes=record.get('nodes');need(isinstance(nodes,dict) and nodes,'nonempty expected node pins required')
        need(all(isinstance(p,str) and p.strip() and type(n) is int and n>0 for p,n in nodes.items()),'invalid position/node pins')
        gate=record.get('noise_gate');need(isinstance(gate,dict),'predeclared A/A noise gate required')
        for name in ('max_median_deviation_pct','max_range_pct'):
            value=gate.get(name);need(type(value) in (int,float) and math.isfinite(value) and value>=0,'invalid noise tolerance')
        need(plan.get('nodes')==nodes and list(plan['nodes'])==list(nodes) and plan.get('noise_gate')==gate and type(plan.get('logical_cpu')) is int and plan['logical_cpu']==cpu and type(plan.get('threads')) is int and plan['threads']==1 and plan.get('order')=='ABBA' and type(plan.get('minimum_blocks')) is int and plan['minimum_blocks']>=10,'record must match hashed protocol and minimum 10 blocks')
        for key in ('baseline','candidate','network','baseline_options','candidate_options'):
            if not isinstance(plan.get(key+'_sha256'),str) or plan[key+'_sha256'].lower()!=record[key]['sha256'].lower():raise Failed('protocol does not bind current artifacts/options')
        a_identity={'binary_sha256':record['baseline']['sha256'].lower(),'network_sha256':record['network']['sha256'].lower(),'options_sha256':record['baseline_options']['sha256'].lower()}
        b_identity={'binary_sha256':record['candidate']['sha256'].lower(),'network_sha256':record['network']['sha256'].lower(),'options_sha256':record['candidate_options']['sha256'].lower()}
        cal=record.get('calibration');need(isinstance(cal,dict),'same-binary A/A calibration required')
        if cal.get('binary_sha256','').lower()!=record['baseline']['sha256'].lower():raise Failed('A/A calibration must use baseline binary for both labels')
        aa=measure(artifact(root,cal.get('samples'),refs),nodes,cpu,{'A':a_identity,'B':a_identity},record['protocol']['sha256'].lower());out['calibration']=aa
        if aa['blocks']<plan['minimum_blocks']:raise Failed('A/A incomplete against protocol')
        if abs(aa['median_change_pct'])>gate['max_median_deviation_pct'] or aa['range_pct']>gate['max_range_pct']:raise Failed('A/A noise gate failed; comparison cannot qualify')
        comparison=record.get('comparison');need(isinstance(comparison,dict),'comparison required')
        ab=measure(artifact(root,comparison.get('samples'),refs),nodes,cpu,{'A':a_identity,'B':b_identity},record['protocol']['sha256'].lower())
        if ab['blocks']<plan['minimum_blocks']:raise Failed('A/B incomplete against protocol')
        if ab['first_start_ns']<aa['last_end_ns']:raise Failed('A/B must follow completed A/A calibration')
        out['comparison']=ab
        for path,sha in refs:
            if digest(path)!=sha:raise Failed('artifact changed during validation')
        out['status']='PASS'
    except Failed as exc:out.update(status='FAIL',error=str(exc))
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,OverflowError,AttributeError) as exc:out.update(status='INVALID',error=str(exc))
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('record',type=Path);a=p.parse_args();r=check(a.record);print(json.dumps(r,indent=2,sort_keys=True,allow_nan=False));return {'PASS':0,'FAIL':1,'INVALID':2}[r['status']]
if __name__=='__main__':sys.exit(main())
