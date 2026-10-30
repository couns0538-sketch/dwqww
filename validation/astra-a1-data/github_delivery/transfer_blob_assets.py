#!/usr/bin/env python3
"""Transfer original artifact bytes through GitHub's authenticated Git-blob API.
Objects are transport only, never a substitute for verified release assets.
No refs, existing assets, source files or credentials are modified.
IDEA_SOURCE: user-authorized original-evidence delivery; standard Git blob framing.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import hashlib
import json
from pathlib import Path
import subprocess
import time

REPO='couns0538-sketch/dwqww'
CHUNK=8*1024*1024

def require(ok,message):
    if not ok: raise ValueError(message)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(CHUNK),b''):h.update(block)
    return h.hexdigest()

def signature(path):
    s=path.stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]

def save(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')

def transfer(job,folder):
    path=Path(job['local_path']);require(signature(path)==job['source_stat'],'source changed before transfer')
    with path.open('rb') as f:f.seek(job['offset']);data=f.read(job['bytes'])
    require(len(data)==job['bytes'],'source chunk short')
    sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    payload=json.dumps({'content':base64.b64encode(data).decode('ascii'),'encoding':'base64'}).encode()
    record={**job,'sha':sha,'sha256':hashlib.sha256(data).hexdigest(),
            'request_bytes':len(payload),'request_sha256':hashlib.sha256(payload).hexdigest()}
    argv=['gh','api','--method','POST','repos/'+REPO+'/git/blobs','--input','-']
    started=time.monotonic();result=subprocess.run(argv,input=payload,capture_output=True,timeout=180)
    record.update(argv=argv,returncode=result.returncode,wall_seconds=time.monotonic()-started)
    stem=f"{job['asset_index']:02d}-{job['chunk_index']:06d}"
    (folder/(stem+'.stdout')).write_bytes(result.stdout)
    (folder/(stem+'.stderr')).write_bytes(result.stderr)
    save(folder/(stem+'.json'),record)
    require(result.returncode==0,'Git blob API failed; original response retained: '+stem)
    require(json.loads(result.stdout)['sha']==sha,'Git server content hash mismatch')
    require(signature(path)==job['source_stat'],'source changed during transfer')
    return record

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--workers',type=int,default=3)
    a=p.parse_args();require(1<=a.workers<=3,'workers must be 1..3')
    a.out.mkdir(parents=True,exist_ok=False);logs=a.out/'chunks';logs.mkdir()
    plan=json.loads(a.plan.read_text());require(plan['release_tag']=='astra-a1-data-results-20261030','wrong release')
    jobs=[];stats={}
    for index,asset in enumerate(plan['assets']):
        path=Path(asset['local_path']);require(path.name==asset['name'] and not path.is_symlink(),'source filename mismatch')
        stats[index]=signature(path)
        require(stats[index][2]==asset['bytes'] and digest(path)==asset['sha256'],'local asset hash/size mismatch')
        for chunk,offset in enumerate(range(0,asset['bytes'],CHUNK)):
            jobs.append({'asset_index':index,'chunk_index':chunk,'name':asset['name'],'local_path':str(path),
                         'offset':offset,'bytes':min(CHUNK,asset['bytes']-offset),'source_stat':stats[index]})
    save(a.out/'source_plan.json',plan);save(a.out/'jobs.json',jobs)
    completed=[];failures=[];iterator=iter(jobs);started=time.monotonic()
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        pending={}
        for _ in range(a.workers):
            job=next(iterator,None)
            if job is not None:pending[pool.submit(transfer,job,logs)]=job
        while pending:
            ready,_=wait(pending,return_when=FIRST_COMPLETED)
            for future in ready:
                job=pending.pop(future)
                try:completed.append(future.result())
                except Exception as error:failures.append({'job':job,'error_type':type(error).__name__,'error':str(error)})
                if not failures:
                    nxt=next(iterator,None)
                    if nxt is not None:pending[pool.submit(transfer,nxt,logs)]=nxt
            print(json.dumps({'completed_chunks':len(completed),'total_chunks':len(jobs),'failures':len(failures),'elapsed_seconds':time.monotonic()-started}),flush=True)
    save(a.out/'transfer_result.json',{'completed':len(completed),'total':len(jobs),'failures':failures,'wall_seconds':time.monotonic()-started})
    require(not failures and len(completed)==len(jobs),'partial transfer only; do not trigger complete delivery')
    manifest={'format':'forge-github-blob-delivery-v1','repository':REPO,'release_id':428684041,
              'release_tag':'astra-a1-data-results-20261030','assets':[]}
    for index,asset in enumerate(plan['assets']):
        path=Path(asset['local_path']);require(signature(path)==stats[index] and digest(path)==asset['sha256'],'source changed after transfer')
        chunks=sorted((x for x in completed if x['asset_index']==index),key=lambda r:r['offset'])
        expected=0
        for chunk in chunks:require(chunk['offset']==expected,'chunk gap');expected+=chunk['bytes']
        require(expected==asset['bytes'],'chunk sum mismatch')
        manifest['assets'].append({**{k:asset[k] for k in ('name','bytes','sha256')},
                                  'chunks':[{k:c[k] for k in ('sha','offset','bytes','sha256')} for c in chunks]})
    save(a.out/'blob_assets.json',manifest)
    print(json.dumps({'status':'ALL_GIT_BLOBS_ACKNOWLEDGED','manifest':str(a.out/'blob_assets.json'),
                      'release_publication':'NOT_YET_VERIFIED','source_unchanged':True}),flush=True)

if __name__=='__main__':main()
