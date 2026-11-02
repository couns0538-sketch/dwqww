#!/usr/bin/env python3
"""Read-only fens12k exact-bit evidence check; no engine runs or timing.
IDEA_SOURCE: crew's exact SIMD contract and original Forge artifact discipline.
"""
import argparse, hashlib, io, json, math, os, re, sys
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

def bound_bytes(path,sha):
    # Parse the exact bytes hashed here, never a second unbound file read.
    with path.open('rb') as stream:
        before=identity(os.fstat(stream.fileno()));data=stream.read(32*1024*1024+1)
        need(len(data)<=32*1024*1024,'structured evidence file exceeds 32 MiB limit')
        if before!=identity(os.fstat(stream.fileno())) or before!=identity(path.stat()):raise Failed('artifact changed during evidence read')
    if hashlib.sha256(data).hexdigest()!=sha.lower():raise Failed('consumed evidence bytes differ from pinned SHA-256')
    return data

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

def component_encodings(encoding,components):
    if encoding!='components-v1':return [encoding]
    need(isinstance(components,list) and 1<=len(components)<=64,'component specification required')
    names=[];encodings=[]
    for item in components:
        need(isinstance(item,dict) and set(item)=={'name','encoding'},'invalid component specification')
        name=item['name'];kind=item['encoding']
        need(isinstance(name,str) and bool(name.strip()) and name not in names,'component names must be unique and nonempty')
        need(kind in ('f32-bits','f64-bits','i32-bits'),'unsupported component encoding')
        names.append(name);encodings.append(kind)
    return encodings

def values(path,fens,encoding,expected_header,trace_sha,components=None):
    result=[];encodings=component_encodings(encoding,components)
    with io.StringIO(bound_bytes(path,trace_sha).decode('utf-8')) as stream:
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
            if encoding=='components-v1':
                expected_active=0 if expected_header.get('implementation')=='scalar' else 1
                need(type(row.get('active_evaluations')) is int and row['active_evaluations']==expected_active,'trace component row activation mismatch')
            bits=row.get('eval_bits')
            parts=bits if encoding=='components-v1' else [bits]
            need(isinstance(parts,list) and len(parts)==len(encodings),'trace component count mismatch')
            for part,kind in zip(parts,encodings):
                width={'f32-bits':8,'f64-bits':16,'i32-bits':8}[kind]
                need(isinstance(part,str) and re.fullmatch('[0-9a-fA-F]{'+str(width)+'}',part),'trace requires exact raw eval bits')
                number=int(part,16)
                if kind=='f32-bits':need((number>>23)&255!=255,'nonfinite float evaluation')
                if kind=='f64-bits':need((number>>52)&2047!=2047,'nonfinite double evaluation')
            result.append(tuple(x.lower() for x in parts) if encoding=='components-v1' else bits.lower())
    need(len(result)==len(fens),'trace row count mismatch');return result

def check(filename):
    result={'status':'INVALID','parity_gate_satisfied':False,'timing_performed':False,
            'scope':'Artifact and trace consistency only; native execution/activation and weight-field identity require original probe review. No Windows, speed or Elo claim.'}
    try:
        filename=Path(filename).absolute();record=decode(filename.read_text(encoding='utf-8-sig'));root=filename.parent;refs=[]
        need(isinstance(record,dict) and type(record.get('schema')) is int and record['schema']==1,'schema must be integer 1')
        encoding=record.get('encoding');need(encoding in ('f32-bits','f64-bits','i32-bits','components-v1'),'unsupported encoding: rounded cp is not bit parity')
        components=record.get('components');component_encodings(encoding,components)
        storage=record.get('network_storage','external');need(storage in ('external','embedded'),'unsupported network_storage')
        active=record.get('candidate_path');need(isinstance(active,dict) and isinstance(active.get('name'),str) and active['name'].strip(),'candidate_path must identify native SIMD/VNNI implementation')
        count=active.get('active_evaluations');need(type(count) is int and count>=0,'invalid candidate active count')
        if count<12000:raise Failed('candidate implementation was not reported active for all 12000 FENs')
        fens_path=artifact(root,record.get('fens'),refs)
        lines=bound_bytes(fens_path,record['fens']['sha256']).decode('utf-8').splitlines();need(len(lines)==12000,'fens12k must contain exactly 12000 FEN lines')
        need(all(len(fen.split())==6 for fen in lines),'full six-field FENs required')
        fens=[hashlib.sha256(fen.encode('utf-8')).hexdigest() for fen in lines]
        for key in ('scalar_binary','candidate_binary','scalar_options','candidate_options','native_log'):artifact(root,record.get(key),refs)
        if storage=='embedded':
            for key in ('embedded_provenance','build_provenance'):artifact(root,record.get(key),refs)
        net=artifact(root,record.get('network'),refs)
        def header(binary,network,options,implementation):
            binary_ref=record[binary] if isinstance(binary,str) else binary
            fields={'binary_sha256':binary_ref['sha256'].lower(),'network_sha256':network['sha256'].lower(),'fens_sha256':record['fens']['sha256'].lower(),'options_sha256':record[options]['sha256'].lower(),'implementation':implementation,'encoding':encoding}
            if encoding=='components-v1':fields['components']=components
            return fields
        base=values(artifact(root,record.get('scalar_trace'),refs),fens,encoding,header('scalar_binary',record['network'],'scalar_options','scalar'),record['scalar_trace']['sha256'],components)
        candidate=values(artifact(root,record.get('candidate_trace'),refs),fens,encoding,header('candidate_binary',record['network'],'candidate_options',active['name']),record['candidate_trace']['sha256'],components)
        result['compared_rows']=len(base);result['mismatches']=sum(a!=b for a,b in zip(base,candidate))
        control=record.get('negative_control');need(isinstance(control,dict),'negative_control required')
        offset=control.get('offset');width=control.get('width')
        need(type(offset) is int and offset>=0 and type(width) is int and width in (1,2,4,8),'invalid single-weight byte range')
        need(isinstance(control.get('tensor'),str) and control['tensor'].strip(),'identify the changed weight tensor')
        corrupt=artifact(root,control.get('network'),refs)
        if net.stat().st_size!=corrupt.stat().st_size or offset+width>net.stat().st_size:raise Failed('negative-control network size/range mismatch')
        changed=0;position=0
        with net.open('rb') as a,corrupt.open('rb') as b:
            before_a=identity(os.fstat(a.fileno()));before_b=identity(os.fstat(b.fileno()));hash_a=hashlib.sha256();hash_b=hashlib.sha256()
            while True:
                x=a.read(1024*1024);y=b.read(len(x))
                if not x:break
                if len(x)!=len(y):raise Failed('negative control changed during comparison')
                hash_a.update(x);hash_b.update(y)
                for i,(left,right) in enumerate(zip(x,y)):
                    if left!=right:
                        if not offset<=position+i<offset+width:raise Failed('negative control changed bytes outside selected weight')
                        changed+=1
                position+=len(x)
            if b.read(1) or before_a!=identity(os.fstat(a.fileno())) or before_a!=identity(net.stat()) or before_b!=identity(os.fstat(b.fileno())) or before_b!=identity(corrupt.stat()):raise Failed('negative-control files changed during comparison')
            if hash_a.hexdigest()!=record['network']['sha256'].lower() or hash_b.hexdigest()!=control['network']['sha256'].lower():raise Failed('consumed network bytes differ from pinned SHA-256')
        if not changed:raise Failed('negative-control weight bytes are unchanged')
        negative_binary='candidate_binary'
        if storage=='embedded':
            artifact(root,control.get('binary'),refs);negative_binary=control['binary']
            if negative_binary['sha256'].lower()==record['candidate_binary']['sha256'].lower():raise Failed('embedded negative control requires a separately built changed binary')
        else:need('binary' not in control,'external-network negative control must use the candidate binary')
        negative=values(artifact(root,control.get('trace'),refs),fens,encoding,header(negative_binary,control['network'],'candidate_options',active['name']),control['trace']['sha256'],components)
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('record',type=Path);parser.add_argument('--threads',type=int,choices=[1]);args=parser.parse_args()
    result=check(args.record);print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False));return {'PASS':0,'FAIL':1,'INVALID':2}[result['status']]
if __name__=='__main__':sys.exit(main())
