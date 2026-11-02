#!/usr/bin/env python3
"""New-file-only QA handover from frozen artifacts and fresh queue COPIES.

IDEA_SOURCE: user's Forge gate handover contract. Original code, stdlib only.
Snapshot freshness is scoped to supplied copies; this never reads a live queue.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, sys
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

REQUIRED_ROLES = ('baseline_binary','candidate_binary','net','source_manifest',
                  'build_log','bench_log','test_log','protocol','lock_contract','proof')
REQUIRED_CHECKS = ('build_a','build_b','reproducible_builds','off_pins','on_active',
                   'perft','smoke_t1','smoke_t4','asan_ubsan')
FORBIDDEN = {'npt','nnue-pytorch','queue.txt','queue_state.json','stop','pause','stop.txt','pause.txt'}


def need(ok, message):
    if not ok: raise ValueError(message)


def unique(pairs):
    result = {}
    for key,value in pairs:
        need(key not in result, 'duplicate JSON key: '+key); result[key]=value
    return result


def finite(value):
    number=float(value);need(math.isfinite(number),'nonfinite JSON');return number


def decode(data):
    return json.loads(data, object_pairs_hook=unique, parse_float=finite,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def integer(value, label):
    need(type(value) is int and 0 <= value <= 2147483647, label+' must be a nonnegative 32-bit integer')
    return value


def indirect(path):
    return path.is_symlink() or getattr(path,'is_junction',lambda:False)()


def safe_path(base, value):
    need(isinstance(value,str) and value and '\x00' not in value, 'path must be text')
    p=Path(value)
    need(not p.is_absolute() and not PureWindowsPath(value).anchor and '\\' not in value and ':' not in value,
         'paths must be relative forward-slash paths')
    need('..' not in p.parts and not any(s.casefold() in FORBIDDEN for s in p.parts), 'protected or escaping path')
    target=base/p
    need(not any(s.casefold() in FORBIDDEN for s in target.parts), 'protected input root')
    for ancestor in (target,*target.parents):
        if ancestor==base: break
        need(not indirect(ancestor), 'symlink inputs are not permitted')
    need(target.is_file(), 'missing regular input: '+value)
    return target


def identity(st):
    fields=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
    return fields+(st.st_ctime_ns,) if os.name=='posix' else fields


def digest(path, output=None):
    h=hashlib.sha256(); md5=hashlib.md5(usedforsecurity=False)
    with path.open('rb') as stream:
        before=identity(os.fstat(stream.fileno()))
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block);md5.update(block)
            if output is not None: output.write(block)
        need(before==identity(os.fstat(stream.fileno()))==identity(path.stat()), 'input changed during read')
    return h.hexdigest(),md5.hexdigest()


def reference(base, entry):
    need(isinstance(entry,dict), 'reference must be an object')
    p=safe_path(base,entry.get('path'))
    expected=entry.get('sha256')
    need(isinstance(expected,str) and re.fullmatch('[0-9a-f]{64}',expected), 'invalid SHA-256')
    need(digest(p)[0]==expected, 'input hash mismatch: '+entry['path'])
    return p


def frozen_json(path, expected):
    need(path.stat().st_size<=16*1024*1024, 'JSON input exceeds 16 MiB')
    data=path.read_bytes();need(hashlib.sha256(data).hexdigest()==expected,'JSON hash changed')
    return decode(data)


def write_new(path, text):
    data=text.encode('utf-8') if isinstance(text,str) else text
    with path.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())


def make_pack(request_path, out):
    request_path=Path(request_path).absolute(); base=request_path.parent; out=Path(out).absolute()
    for p in (request_path,*request_path.parents): need(not indirect(p), 'symlink request or ancestor')
    need(not out.exists(), 'output already exists')
    need(not any(p.casefold() in FORBIDDEN for p in out.parts), 'protected output path')
    for p in (out,*out.parents): need(not indirect(p), 'symlink output ancestor')
    need(not any(p.casefold() in FORBIDDEN for p in request_path.parts), 'protected request path')
    raw=request_path.read_bytes();request=decode(raw)
    need(type(request.get('schema')) is int and request['schema']==1, 'schema must be 1')
    for key in ('baseline_commit','candidate_commit'):
        need(isinstance(request.get(key),str) and re.fullmatch('[0-9a-f]{40}',request[key]),'invalid '+key)
    need(isinstance(request.get('build'),dict) and all(isinstance(request['build'].get(k),str) and request['build'][k].strip() for k in ('compiler','flags')), 'build compiler and flags required')
    need(isinstance(request.get('variants'),dict) and all(isinstance(request['variants'].get(k),dict) for k in ('OFF','ON')), 'OFF/ON variant maps required')
    gate=request.get('gate');need(isinstance(gate,dict), 'gate object required')
    need(isinstance(gate.get('name'),str) and re.fullmatch('[A-Za-z0-9_-]+',gate['name']), 'invalid gate name')
    for key in ('start','srand','threads','hash_mb'): integer(gate.get(key),key)
    need(gate['threads']>0 and gate['hash_mb']>0 and isinstance(gate.get('time_control'),str) and gate['time_control'], 'gate settings incomplete')
    artifacts=request.get('artifacts');need(isinstance(artifacts,list), 'artifacts required')
    roles={}; paths={}
    for item in artifacts:
        need(isinstance(item,dict) and isinstance(item.get('role'),str), 'artifact role required')
        p=reference(base,item)
        need(item['path'] not in paths, 'duplicate artifact path')
        paths[item['path']]=item
        roles.setdefault(item['role'],[]).append((item,p))
    need(set(REQUIRED_ROLES)<=roles.keys() and all(len(roles[r])==1 for r in REQUIRED_ROLES), 'required artifact roles missing or duplicated')
    proof_item,proof_path=roles['proof'][0];proof=frozen_json(proof_path,proof_item['sha256'])
    need(type(proof.get('schema')) is int and proof['schema']==1 and proof.get('status')=='PASS' and proof.get('evidence_scope')=='native', 'proof must PASS with native evidence scope')
    need(all(proof.get(k)==request[k] for k in ('baseline_commit','candidate_commit')), 'proof revision mismatch')
    need(proof.get('contract_sha256')==roles['lock_contract'][0][0]['sha256'], 'proof contract mismatch')
    for field,role in [('baseline_binary_sha256','baseline_binary'),('candidate_binary_sha256','candidate_binary'),('net_sha256','net')]:
        need(proof.get(field)==roles[role][0][0]['sha256'], 'proof subject mismatch: '+role)
    need(proof.get('tested_options')=={'off':request['variants']['OFF'],'on':request['variants']['ON']}, 'proof options mismatch')
    checks=proof.get('checks');need(isinstance(checks,list) and checks, 'proof checks required')
    seen=set()
    for check in checks:
        need(isinstance(check,dict) and isinstance(check.get('name'),str) and check['name'] not in seen and check.get('status')=='PASS', 'proof check not uniquely PASS')
        seen.add(check['name']);evidence=check.get('evidence');need(isinstance(evidence,list) and evidence,'proof evidence required')
        for entry in evidence:
            p=reference(proof_path.parent,entry)
            rel=p.relative_to(base).as_posix()
            need(rel in paths and paths[rel]['sha256']==entry['sha256'], 'proof evidence must be included as an artifact')
    need(set(REQUIRED_CHECKS)<=seen, 'required proof checks missing')
    protocol_item,protocol_path=roles['protocol'][0]
    protocol=frozen_json(protocol_path,protocol_item['sha256'])
    need(isinstance(protocol,dict) and all(protocol.get(k)==v for k,v in gate.items()), 'gate/protocol mismatch')
    snapshots=request.get('snapshots');need(isinstance(snapshots,list) and snapshots,'fresh snapshot copies required')
    now=datetime.now(timezone.utc); scan=[]; snapshot_files=[]
    for index,item in enumerate(snapshots):
        p=reference(base,item);need(item.get('trusted_copy') is True, 'trusted snapshot copy attestation required')
        need(type(item.get('mtime_ns')) is int and p.stat().st_mtime_ns==item['mtime_ns'], 'snapshot mtime mismatch')
        stamp=datetime.fromisoformat(item['captured_at_utc'].replace('Z','+00:00'))
        need(stamp.tzinfo is not None and 0<=(now-stamp).total_seconds()<=900, 'snapshot freshness must be 0..900 seconds')
        need(isinstance(item.get('source_label'),str) and item['source_label'].strip(),'snapshot coverage label required')
        data=frozen_json(p,item['sha256']);need(isinstance(data,dict) and type(data.get('schema')) is int and data['schema']==1 and isinstance(data.get('gates'),list),'snapshot must be normalized schema-1 gates')
        for row in data['gates']:
            need(isinstance(row,dict), 'invalid gate row')
            for key in ('start','srand'):
                value=integer(row.get(key),'snapshot '+key)
                need(value!=gate[key],'reused '+key+' in supplied snapshot')
        scan.append(dict(item,rows_scanned=len(data['gates']),scan_utc=now.isoformat()))
        snapshot_files.append((p,f'snapshots/{index:03}.json',item['sha256']))
    # All preflight checks precede output creation; failure during copying leaves
    # an incomplete, owned directory for investigation, never a completed receipt.
    out.mkdir(parents=False,exist_ok=False)
    copies=[(base/item['path'],'artifacts/'+item['path'],item['sha256']) for item in artifacts]+snapshot_files
    for source,name,expected in copies:
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:
            observed,_=digest(source,stream);stream.flush();os.fsync(stream.fileno())
        need(observed==expected, 'input changed during packaging')
    write_new(out/'REQUEST.json',raw)
    write_new(out/'SCAN.json',json.dumps({'scan_utc':now.isoformat(),'scope':'Supplied normalized snapshots only; not a live queue check','snapshots':scan},indent=2)+'\n')
    write_new(out/'README.md','# '+gate['name']+' QA handover\n\nVerify SHA256SUMS and MD5SUMS, then review GATE.md, REQUEST.json, SCAN.json and the original proof artifacts. No queue was modified. No test was rerun by this packager.\n')
    write_new(out/'GATE.md','# Gate '+gate['name']+'\n\n```json\n'+json.dumps(gate,indent=2)+'\n```\n\nBaseline: '+request['baseline_commit']+'\nCandidate: '+request['candidate_commit']+'\n\nSnapshot-only freshness/uniqueness check at '+now.isoformat()+'. QA must confirm live availability before enqueueing. Reported PASS tests were supplied, not independently reproduced by this packager. Source/build/net, OFF/ON options and proof are bound in REQUEST.json.\n')
    table=[]
    for path in sorted(out.rglob('*')):
        if path.is_file():
            sha,md5=digest(path);table.append((path.relative_to(out).as_posix(),sha,md5))
    for name,offset in [('MD5SUMS',2),('SHA256SUMS',1)]:
        with (out/name).open('x',encoding='utf-8',newline='\n') as stream:
            for row in table:stream.write(row[offset]+'  '+row[0]+'\n')
            stream.flush();os.fsync(stream.fileno())
    return {'status':'READY_FOR_QA_REVIEW','out':str(out),'files_hashed':len(table),'scan_utc':now.isoformat(),'scope':'Supplied snapshot scan and artifact consistency only; no live-queue or native-test claim'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('request',type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    try: result=make_pack(a.request,a.out)
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as error:
        print(json.dumps({'status':'BLOCKED','reason':str(error)}));return 2
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':sys.exit(main())
