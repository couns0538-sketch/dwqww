#!/usr/bin/env python3
"""Read-only fens12k exact-bit evidence check; no engine runs or timing.
IDEA_SOURCE: crew's exact SIMD contract and original Forge artifact discipline.
"""
import argparse, hashlib, json, math, os, re, sys
from pathlib import Path, PureWindowsPath

class Failed(Exception): pass

def need(ok, message):
    if not ok: raise ValueError(message)

def unique(pairs):
    value={}
    for key,item in pairs:
        need(key not in value,'duplicate JSON key: '+key);value[key]=item
    return value

def finite(text):
    value=float(text);need(math.isfinite(value),'nonfinite JSON');return value

def decode(text):
    return json.loads(text,object_pairs_hook=unique,parse_float=finite,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))

def identity(s):
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)+( (s.st_ctime_ns,) if os.name=='posix' else () )

def digest(path):
    with path.open('rb') as stream:
        before=identity(os.fstat(stream.fileno()));h=hashlib.sha256()
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
        if before!=identity(os.fstat(stream.fileno())) or before!=identity(path.stat()):raise Failed('artifact changed during hash')
    return h.hexdigest()

def artifact(root,ref,refs):
    need(isinstance(ref,dict),'artifact reference must be an object')
    name=ref.get('path');sha=ref.get('sha256')
    need(isinstance(name,str) and name and '\x00' not in name and '\\' not in name and ':' not in name and not Path(name).is_absolute() and not PureWindowsPath(name).anchor,'artifact path must use relative forward-slash syntax')
    need(isinstance(sha,str) and re.fullmatch('[0-9a-fA-F]{64}',sha),'invalid SHA-256')
    path=root/name
    try:
        if digest(path)!=sha.lower():raise Failed('artifact hash mismatch: '+name)
    except OSError as exc:raise Failed('artifact unavailable: '+name+': '+str(exc)) from exc
    refs.append((path,sha.lower()));return path

def values(path,fens,encoding,expected_header):
    result=[];width={'f32-bits':8,'f64-bits':16,'i32-bits':8}[encoding]
    with path.open('r',encoding='utf-8') as stream:
        header=decode(stream.readline());need(isinstance(header,dict) and type(header.get('schema')) is int and header['schema']==1 and header.get('kind')=='eval-trace','trace must begin with an eval-trace schema-1 header')
        for key,value in expected_header.items():
            observed=header.get(key)
            if key.endswith('_sha256') and isinstance(observed,str):observed=observed.lower()
            if observed!=value:raise Failed('trace header does not bind the expected executable/network/FEN/options/implementation')
        for i,line in enumerate(stream):
            need(i<len(fens),'trace contains extra rows')
            row=decode(line);need(isinstance(row,dict),'trace row must be an object')
            need(type(row.get('row')) is int and row['row']==i,'trace row index/order mismatch')
            need(row.get('fen_sha256')==fens[i],'trace FEN hash mismatch')
            bits=row.get('eval_bits');need(isinstance(bits,str) and re.fullmatch('[0-9a-fA-F]{'+str(width)+'}',bits),'trace requires exact raw eval bits')
            number=int(bits,16)
            if encoding=='f32-bits':need((number>>23)&255!=255,'nonfinite float evaluation')
            if encoding=='f64-bits':need((number>>52)&2047!=2047,'nonfinite double evaluation')
            result.append(bits.lower())
    need(len(result)==len(fens),'trace row count mismatch');return result

def check(filename):
    result={'status':'INVALID','parity_gate_satisfied':False,'timing_performed':False,
            'scope':'Artifact and trace consistency only; native execution/activation and weight-field identity require original probe review. No Windows, speed or Elo claim.'}
    try:
        filename=Path(filename).absolute();record=decode(filename.read_text(encoding='utf-8-sig'));root=filename.parent;refs=[]
        need(isinstance(record,dict) and type(record.get('schema')) is int and record['schema']==1,'schema must be integer 1')
        encoding=record.get('encoding');need(encoding in ('f32-bits','f64-bits','i32-bits'),'unsupported encoding: rounded cp is not bit parity')
        active=record.get('candidate_path');need(isinstance(active,dict) and isinstance(active.get('name'),str) and active['name'].strip(),'candidate_path must identify native SIMD/VNNI implementation')
        count=active.get('active_evaluations');need(type(count) is int and count>=0,'invalid candidate active count')
        if count<12000:raise Failed('candidate implementation was not reported active for all 12000 FENs')
        fens_path=artifact(root,record.get('fens'),refs)
        lines=fens_path.read_text(encoding='utf-8').splitlines();need(len(lines)==12000,'fens12k must contain exactly 12000 FEN lines')
        need(all(len(fen.split())==6 for fen in lines),'full six-field FENs required')
        fens=[hashlib.sha256(fen.encode('utf-8')).hexdigest() for fen in lines]
        for key in ('scalar_binary','candidate_binary','scalar_options','candidate_options','native_log'):artifact(root,record.get(key),refs)
        net=artifact(root,record.get('network'),refs)
        def header(binary,network,options,implementation):
            return {'binary_sha256':record[binary]['sha256'].lower(),'network_sha256':network['sha256'].lower(),'fens_sha256':record['fens']['sha256'].lower(),'options_sha256':record[options]['sha256'].lower(),'implementation':implementation,'encoding':encoding}
        base=values(artifact(root,record.get('scalar_trace'),refs),fens,encoding,header('scalar_binary',record['network'],'scalar_options','scalar'))
        candidate=values(artifact(root,record.get('candidate_trace'),refs),fens,encoding,header('candidate_binary',record['network'],'candidate_options',active['name']))
        result['compared_rows']=len(base);result['mismatches']=sum(a!=b for a,b in zip(base,candidate))
        control=record.get('negative_control');need(isinstance(control,dict),'negative_control required')
        offset=control.get('offset');width=control.get('width')
        need(type(offset) is int and offset>=0 and type(width) is int and width in (1,2,4,8),'invalid single-weight byte range')
        need(isinstance(control.get('tensor'),str) and control['tensor'].strip(),'identify the changed weight tensor')
        corrupt=artifact(root,control.get('network'),refs)
        if net.stat().st_size!=corrupt.stat().st_size or offset+width>net.stat().st_size:raise Failed('negative-control network size/range mismatch')
        changed=0;position=0
        with net.open('rb') as a,corrupt.open('rb') as b:
            while True:
                x=a.read(1024*1024);y=b.read(len(x))
                if not x:break
                for i,(left,right) in enumerate(zip(x,y)):
                    if left!=right:
                        if not offset<=position+i<offset+width:raise Failed('negative control changed bytes outside selected weight')
                        changed+=1
                position+=len(x)
        if not changed:raise Failed('negative-control weight bytes are unchanged')
        negative=values(artifact(root,control.get('trace'),refs),fens,encoding,header('candidate_binary',control['network'],'candidate_options',active['name']))
        result['negative_control_mismatches']=sum(a!=b for a,b in zip(base,negative))
        if not result['negative_control_mismatches']:raise Failed('corrupt-weight negative control did not change evaluation')
        for path,sha in refs:
            if digest(path)!=sha:raise Failed('artifact changed during validation')
        if result['mismatches']:raise Failed('candidate raw evaluation mismatch')
        result.update(status='PASS',parity_gate_satisfied=True)
    except Failed as exc:result.update(status='FAIL',error=str(exc))
    except (OSError,ValueError,TypeError,KeyError,RuntimeError) as exc:result.update(status='INVALID',error=str(exc))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('record',type=Path);args=parser.parse_args()
    result=check(args.record);print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False));return {'PASS':0,'FAIL':1,'INVALID':2}[result['status']]
if __name__=='__main__':sys.exit(main())
