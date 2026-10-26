"""Capture the unchanged native S09 parity helper, preserving gzip stdout.

Corpus decode/sealing reuses the frozen tested memfd function; importing that
module never loads Torch. Only exact integer helper records are parsed here.
"""
from pathlib import Path
import argparse, gzip, hashlib, importlib.util, json, os, re, selectors, signal, subprocess, time

PROBE=Path('/workspace/forge-pack24-20261026/S09_TORCHRAM_20261026/forge_sol_S09_torchram_probe_v2_20261026.py')
PROBE_SHA='e43b6ec82a611e9fd03a1b44b70487189b7df1ed32cfe5734de9e139b055d7bb'
SUMMARY=re.compile(r'lines (\d+) available=1 residual=1 hidden=256 acc_mismatch=0\n')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def row(line,previous,plies):
    if re.fullmatch(rb'-?\d+(?: -?\d+){6}\n',line) is None:raise ValueError('malformed/BAD/ILLEGAL/truncated native parity record')
    v=tuple(map(int,line.split()));n,p,pieces,head,net,hce,same=v
    if same!=1:raise ValueError('incremental accumulator differs from refresh')
    if not 2<=pieces<=32 or head!=min(7,max(0,(pieces-1)//4)):raise ValueError('piece-count/head mapping differs')
    if not 0<=p<=plies:raise ValueError('ply outside requested bound')
    if previous is None:
        if (n,p)!=(0,0):raise ValueError('first native root/ply is not zero')
    elif not ((n==previous[0] and p==previous[1]+1) or (n==previous[0]+1 and p==0)):
        raise ValueError('duplicate/skipped/reordered root or ply')
    return v


def capture(exe,fd,plies,out,seconds,roots):
    out=Path(out);exe=Path(exe);before=sha(exe);start=time.monotonic();proc=None
    result={'command':[str(exe),f'/proc/self/fd/{fd}',str(plies)],'exe_sha256':before,'rows':0,'roots':0,'head_counts':[0]*8}
    try:
        with out.with_suffix('.stderr').open('xb') as err, out.with_suffix('.stdout.gz').open('xb') as raw:
            with gzip.GzipFile(fileobj=raw,filename='',mode='wb',mtime=0,compresslevel=6) as saved:
                proc=subprocess.Popen(result['command'],stdout=subprocess.PIPE,stderr=err,pass_fds=(fd,),start_new_session=True)
                sel=selectors.DefaultSelector();sel.register(proc.stdout,selectors.EVENT_READ);tail=b'';previous=None;digest=hashlib.sha256();raw_bytes=0
                try:
                    while sel.get_map():
                        if time.monotonic()-start>=seconds:raise TimeoutError('owned native parity deadline')
                        for key,_ in sel.select(.1):
                            chunk=os.read(key.fd,65536)
                            if not chunk:sel.unregister(key.fileobj);continue
                            saved.write(chunk);digest.update(chunk);raw_bytes+=len(chunk);tail+=chunk
                            if len(tail)>1048576:raise ValueError('unbounded native record')
                            while b'\n' in tail:
                                line,tail=tail.split(b'\n',1);previous=row(line+b'\n',previous,plies)
                                if previous[0]>=roots:raise ValueError('more native roots than corpus')
                                result['rows']+=1;result['roots']+=previous[1]==0;result['head_counts'][previous[3]]+=1
                    if tail:raise ValueError('truncated final native record')
                    proc.wait(timeout=max(.01,seconds-(time.monotonic()-start)))
                finally:
                    sel.close();proc.stdout.close()
                result.update(returncode=proc.returncode,raw_stdout_sha256=digest.hexdigest(),raw_stdout_bytes=raw_bytes)
        if proc.returncode!=0:raise ValueError('native helper did not exit normally with rc0')
        match=SUMMARY.fullmatch(out.with_suffix('.stderr').read_text())
        if not match or int(match[1])!=roots or result['roots']!=roots:raise ValueError('missing/conflicting native summary or root count')
        if sha(exe)!=before:raise ValueError('native executable changed')
        result['stdout_gzip_sha256']=sha(out.with_suffix('.stdout.gz'));result['status']='PASS_CAPTURE'
        return result
    finally:
        if proc is not None and proc.poll() is None:
            try:os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                proc.wait()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('reference','candidate','corpus_manifest','out'):ap.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    ap.add_argument('--plies',type=int,default=0);ap.add_argument('--arm-seconds',type=float,required=True);ap.add_argument('--minimum-rows',type=int,default=1000000);a=ap.parse_args()
    if not 0<=a.plies<=256 or not 0<a.arm_seconds<=3600 or a.minimum_rows<1:ap.error('invalid finite native protocol')
    allowed=Path('/workspace/forge-pack24-20261026/S09_NATIVE_20261026')
    if not a.out.is_absolute() or a.out.resolve()!=a.out or not a.out.is_relative_to(allowed) or a.out==allowed:ap.error('output must be a new descendant of S09_NATIVE_20261026')
    a.out.mkdir(exist_ok=False);result={'status':'FAIL','scope':'exact integer CP/HCE and helper-local accumulator memcmp; cross-build float bits require separate original nnue_snapshot comparison'};fd=None
    try:
        assert sha(PROBE)==PROBE_SHA
        spec=importlib.util.spec_from_file_location('sealed_input',PROBE);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
        m=json.loads(a.corpus_manifest.read_text());fd=api.sealed_memfd_from_gzip(m['gzip'],compressed_size=m['gzip_size'],compressed_sha256=m['gzip_sha256'],raw_size=m['raw_size'],raw_sha256=m['raw_sha256'])
        result['corpus_manifest_sha256']=sha(a.corpus_manifest);result['corpus_raw_sha256']=m['raw_sha256'];result['corpus_count']=m['count'];result['memfd_seals']=api.fcntl.fcntl(fd,api.F_GET_SEALS)
        result['reference']=capture(a.reference,fd,a.plies,a.out/'reference',a.arm_seconds,m['count'])
        result['candidate']=capture(a.candidate,fd,a.plies,a.out/'candidate',a.arm_seconds,m['count'])
        with gzip.open(a.out/'reference.stdout.gz','rb') as left,gzip.open(a.out/'candidate.stdout.gz','rb') as right:
            while True:
                x,y=left.read(65536),right.read(65536)
                if x!=y:raise ValueError('native parity bytes differ')
                if not x:break
        if result['reference']['rows']<a.minimum_rows:raise ValueError('actual compared rows below declared minimum')
        result['status']='PASS_NATIVE_CP_PARITY';result['actual_compared_rows']=result['reference']['rows'];result['byte_comparison']='all decompressed bytes compared equal'
    except Exception as error:result['error']=type(error).__name__+': '+str(error)
    finally:
        if fd is not None:os.close(fd)
        (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True));return 0 if result['status']=='PASS_NATIVE_CP_PARITY' else 1


if __name__=='__main__':raise SystemExit(main())
