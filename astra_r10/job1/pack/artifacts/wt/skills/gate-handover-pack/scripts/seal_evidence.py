#!/usr/bin/env python3
"""Seal explicit R10 evidence. Never grants gate or training clearance.

IDEA_SOURCE: Couns's R10 handover and preservation contract; original code.
The existing strict make_gate_pack.py remains unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys

WORKSPACE = Path('D:/a10')
CAP = 15_000_000_000
FAULTS = ('before_publish', 'after_publish_before_checkpoint', 'after_checkpoint')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        need(key not in result, 'duplicate JSON key: '+key)
        result[key] = value
    return result


def decode(raw):
    need(len(raw) <= 8*1024*1024, 'JSON exceeds 8 MiB')
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def json_bytes(path):
    with path.open('rb') as stream:
        raw=stream.read(8*1024*1024+1)
    need(len(raw)<=8*1024*1024,'JSON exceeds 8 MiB')
    return raw


def reparse(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def checked_path(value):
    raw = str(value)
    need(re.match(r'^[dD]:[\\/]', raw) is not None, 'absolute D:/a10 path required')
    need(not any(part in ('.', '..') for part in re.split(r'[\\/]',raw)), 'dot path components refused')
    need(':' not in raw[2:] and not any(c in raw for c in '*?\x00'), 'invalid path syntax')
    path = Path(raw)
    need(path.is_relative_to(WORKSPACE), 'all pack I/O must stay beneath D:/a10')
    for node in reversed((path, *path.parents)):
        if node.exists() or node.is_symlink():
            need(not reparse(node), 'reparse/symlink path refused: '+str(node))
    return path


def relative_name(value):
    need(isinstance(value,str) and value and not any(c in value for c in '\\:*?\x00\r\n\x85\u2028\u2029')
         and not any(ord(c)<32 for c in value), 'invalid relative artifact path')
    parts=value.split('/')
    need(all(p not in ('','.','..') and not p.endswith((' ','.')) for p in parts), 'invalid relative artifact path')
    devices={'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}
    need(all(p.split('.')[0].lower() not in devices for p in parts), 'reserved artifact filename')
    return value


def digests(path):
    sh=hashlib.sha256(); md=hashlib.md5()
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno())
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            sh.update(chunk);md.update(chunk)
        after=os.fstat(stream.fileno())
    current=path.stat()
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    need(identity(before)==identity(after)==identity(current), 'input changed while hashing')
    return sh.hexdigest(),md.hexdigest(),current.st_size


def workspace_bytes():
    total=0; pending=[checked_path(WORKSPACE)]
    while pending:
        folder=pending.pop()
        with os.scandir(folder) as entries:
            for entry in entries:
                path=Path(entry.path)
                need(not reparse(path), 'workspace reparse/symlink refused')
                if entry.is_dir(follow_symlinks=False):pending.append(path)
                else:total+=entry.stat(follow_symlinks=False).st_size
    return total


def disk_budget(required):
    need(shutil.disk_usage('C:/').free >= 30*1024**3, 'C: 30 GiB floor')
    need(shutil.disk_usage('D:/').free >= 50*1024**3+required, 'D: floor plus write reservation')


def evidence_refs(report, entries):
    refs=report.get('evidence')
    need(isinstance(refs,list) and refs, 'actual report evidence references required')
    for ref in refs:
        need(isinstance(ref,dict), 'invalid evidence reference')
        name=relative_name(ref.get('path'))
        need(name in entries and ref.get('sha256')==entries[name]['sha256'], 'report evidence must be shipped with matching hash')


def validate_data(entries, roles):
    for role in ('tool','sample','training_command','audit_report','replay_report'):
        need(role in roles and len(roles[role])==1, 'data-tool requires one '+role)
    reports={}
    for role in ('audit_report','replay_report'):
        entry=roles[role][0]
        raw=json_bytes(entry['source'])
        need(hashlib.sha256(raw).hexdigest()==entry['sha256'],'report changed after hash check')
        report=decode(raw)
        need(isinstance(report,dict) and type(report.get('schema')) is int and report['schema']==1
             and report.get('status')=='PASS' and report.get('evidence_scope')=='actual-adapter',
             role+' must PASS with actual-adapter scope')
        evidence_refs(report,entries);reports[role]=report
    audit=reports['audit_report']
    for name in ('source_rows','training_rows'):
        need(type(audit.get(name)) is int and audit[name]>0, 'audit requires positive '+name)
    for name in ('position_overlap_rows','game_overlap_rows','state_mismatch_rows','unknown_game_id_rows'):
        need(type(audit.get(name)) is int and audit[name]==0, 'audit requires zero '+name)
    holdouts=audit.get('holdouts')
    need(isinstance(holdouts,dict) and set(holdouts)=={'013','014'}, 'both complete holdouts required')
    for item in holdouts.values():
        need(isinstance(item,dict) and type(item.get('rows')) is int and item['rows']>0
             and item.get('trusted_complete') is True and isinstance(item.get('sha256'),str)
             and re.fullmatch('[a-f0-9]{64}',item['sha256']), 'complete holdout identity missing')
    replay=reports['replay_report']; faults=replay.get('faults'); output_roles=replay.get('output_roles')
    need(isinstance(faults,dict) and set(faults)==set(FAULTS), 'all three real-adapter fault points required')
    need(isinstance(output_roles,list) and output_roles and all(isinstance(x,str) and x for x in output_roles)
         and len(set(output_roles))==len(output_roles), 'all adapter output_roles required')
    resumed_sources=set()
    for name, fault in faults.items():
        need(isinstance(fault,dict) and fault.get('status')=='PASS', 'fault must PASS: '+name)
        outputs=fault.get('outputs')
        need(isinstance(outputs,list) and all(isinstance(x,dict) for x in outputs)
             and len(outputs)==len(output_roles) and {x.get('role') for x in outputs}==set(output_roles), 'fault output roles differ')
        for output in outputs:
            hashes=[]
            for side in ('uninterrupted','resumed'):
                ref=output.get(side);need(isinstance(ref,dict), 'output reference required')
                key=relative_name(ref.get('path'));need(key in entries, 'replay output must be shipped')
                entry=entries[key]
                need(ref.get('sha256')==entry['sha256'], 'replay output SHA256 mismatch')
                need(ref.get('md5')==entry['md5'], 'replay output MD5 mismatch')
                hashes.append((entry['sha256'],entry['md5']))
            baseline=entries[output['uninterrupted']['path']]['source']
            resumed=entries[output['resumed']['path']]['source']
            need(not os.path.samefile(baseline,resumed), 'uninterrupted/resumed outputs must be independent files')
            need(not any(os.path.samefile(resumed,p) for p in resumed_sources), 'each fault requires independent resumed outputs')
            resumed_sources.add(resumed)
            need(hashes[0]==hashes[1], 'resumed bytes differ')


def write_new(path, data):
    with path.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())


def seal(manifest, out, purpose):
    need(purpose in ('incomplete-engine','data-tool'), 'explicit supported purpose required')
    manifest=checked_path(manifest);out=checked_path(out)
    need(not out.exists(), 'output already exists; preserve every attempt')
    raw=json_bytes(manifest);request=decode(raw)
    need(isinstance(request,dict) and type(request.get('schema')) is int and request['schema']==1,'manifest schema must be 1')
    root=checked_path(request.get('source_root',''));need(root.is_dir(),'source_root directory required')
    items=request.get('artifacts');need(isinstance(items,list) and items,'explicit artifacts required')
    blockers=request.get('blockers',[])
    need(isinstance(blockers,list) and all(isinstance(x,str) and x.strip() for x in blockers),'invalid blockers')
    if purpose=='incomplete-engine':need(blockers,'incomplete-engine needs at least one blocker')
    else:need(not blockers,'data-tool qualification has unresolved blockers')
    entries={};roles={};case_names=set();payload_size=0
    for item in items:
        need(isinstance(item,dict) and isinstance(item.get('role'),str) and item['role'], 'artifact role required')
        name=relative_name(item.get('path'));folded=name.casefold()
        need(folded not in case_names,'duplicate artifact path');case_names.add(folded)
        source=checked_path(root/name);need(source.is_file(),'artifact must exist as a regular file')
        sha,md5,size=digests(source)
        need(item.get('sha256')==sha,'artifact hash mismatch: '+name)
        entry={'path':name,'role':item['role'],'sha256':sha,'md5':md5,'size':size,'source':source}
        entries[name]=entry;roles.setdefault(item['role'],[]).append(entry);payload_size+=size
    for name in case_names:
        need(not any('/'.join(name.split('/')[:i]) in case_names for i in range(1,len(name.split('/')))), 'artifact parent is another file')
    if purpose=='data-tool':validate_data(entries,roles)
    reservation=payload_size+len(raw)*3+1024*1024
    disk_budget(reservation)
    need(workspace_bytes()+reservation<=CAP,'workspace 15 GB cap including pack reservation')
    out.mkdir(parents=True,exist_ok=False)
    remaining=reservation
    for entry in entries.values():
        disk_budget(remaining);source=checked_path(entry['source']);target=checked_path(out/'artifacts'/entry['path'])
        target.parent.mkdir(parents=True,exist_ok=True)
        with source.open('rb') as incoming,target.open('xb') as outgoing:
            unread=entry['size'];since_check=0
            while unread:
                chunk=incoming.read(min(unread,1024*1024))
                need(chunk,'source truncated during copy')
                outgoing.write(chunk);unread-=len(chunk);remaining-=len(chunk);since_check+=len(chunk)
                if since_check>=64*1024*1024:
                    disk_budget(remaining);since_check=0
            need(not incoming.read(1),'source grew during copy')
            outgoing.flush();os.fsync(outgoing.fileno())
        need(digests(target)[:2]==(entry['sha256'],entry['md5']),'copied artifact changed')
        need(digests(checked_path(source))[0]==entry['sha256'],'source changed while copying')
    need(digests(manifest)[0]==hashlib.sha256(raw).hexdigest(),'manifest changed during packing')
    report={'schema':1,'purpose':purpose,'status':'SEALED_INCOMPLETE' if purpose=='incomplete-engine' else 'SEALED_DATA_TOOL',
            'strength':'UNPROVEN','blockers':blockers,'manifest_sha256':hashlib.sha256(raw).hexdigest(),
            'sealer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'artifacts':len(entries),'scope':'Artifact consistency only; native evidence requires independent review. No gate or training clearance.'}
    write_new(out/'REQUEST.json',raw)
    write_new(out/'REPORT.json',(json.dumps(report,indent=2)+'\n').encode())
    readme=('UNPROVEN — '+report['status']+'\n\n'+report['scope']+'\n\n'
            'Verify SHA256SUMS and MD5SUMS before review. No seed inventory was fabricated; no queue was touched. '
            'This sealed evidence copy does not replace the strict engine gate pack. Retain incomplete attempts.\n')
    if blockers:readme+='\nBlockers:\n'+''.join('- '+x+'\n' for x in blockers)
    write_new(out/'README.md',readme.encode())
    files=sorted(p for p in out.rglob('*') if p.is_file())
    hashes=[(p.relative_to(out).as_posix(),*digests(p)[:2]) for p in files]
    write_new(out/'SHA256SUMS',''.join(f'{sha}  {name}\n' for name,sha,md5 in hashes).encode())
    write_new(out/'MD5SUMS',''.join(f'{md5}  {name}\n' for name,sha,md5 in hashes).encode())
    disk_budget(0);need(workspace_bytes()<=CAP,'workspace cap breached during packing')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path);parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--purpose',required=True,choices=('incomplete-engine','data-tool'))
    parser.add_argument('--threads',required=True,type=int,choices=(1,))
    args=parser.parse_args()
    try:
        print(json.dumps(seal(args.manifest,args.out,args.purpose),indent=2));return 0
    except (OSError,ValueError,TypeError,KeyError) as error:
        print(json.dumps({'status':'BLOCKED','strength':'UNPROVEN','error':str(error)}));return 2


if __name__=='__main__':sys.exit(main())
