"""Rerun reviewed R9 native checks on frozen R10 copies; no training or strength match."""
import argparse, hashlib, json, os, pathlib, subprocess, sys
sys.path.insert(0,'D:/a10/pydeps')
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
import psutil
from lane_guard import check_lane  # CR crfix abcbb9c9

def need(ok,what=''):
    if not ok: raise RuntimeError('CHECK FAILED: '+repr(what))  # CR crfix: no assert-as-check

def digest(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--threads',type=int,choices=[1],required=True)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    ap.add_argument('--exe',type=pathlib.Path,required=True)
    ap.add_argument('--kind',choices=['smoke','sanitizer'],required=True)
    a=ap.parse_args()
    need(psutil.Process().nice()==psutil.IDLE_PRIORITY_CLASS,'Idle')
    need(set(psutil.Process().cpu_affinity())<={2,3},'CPUs 2-3')
    lane=check_lane()
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'lane_check.json').write_text(json.dumps(lane,indent=2))
    expected=('a56762278935af93344680ba147a9076f63b52504e2495a686d7fe5f28a4a2aa' if a.kind=='sanitizer'
              else '775edea1d476a3a18c64af63f53c55d6e29a4571556aad2666e87f18a6ef4284')
    need(digest(a.exe)==expected,'binary hash')
    env=os.environ.copy(); env.update(ASAN_OPTIONS='halt_on_error=1:detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',
        TEMP='D:/a10/tmp',TMP='D:/a10/tmp',PYTHONDONTWRITEBYTECODE='1')
    evidence={'status':'RUNNING','kind':a.kind,'binary':str(a.exe),'binary_sha256':expected,
        'scope':'Native rerun. Sanitizer binary recovered unchanged from R9 with source manifest binding; auxiliary only.',
        't4':'UNVERIFIED: host loaded; no T4 launched','runs':[]}
    bound=[pathlib.Path(__file__),pathlib.Path(__file__).with_name('validate_uci.py'),
        pathlib.Path('D:/a10/inputs/fens_12k.txt'),pathlib.Path('D:/a10/wt/astra_r9/evidence/c1-source.json'),
        pathlib.Path('D:/a10/wt/astra_r9/evidence/auxiliary-build-provenance.json')]
    evidence['inputs_sha256']={str(p):digest(p) for p in bound}
    try:
        for on in [False,True]:
            mode='selfplay' if a.kind=='sanitizer' else 'smoke'
            label='on' if on else 'off'
            cmd=[sys.executable,'-B',str(pathlib.Path(__file__).with_name('validate_uci.py')),mode,str(a.exe),str(a.out/label),'--threads','1']
            if on:cmd.append('--on')
            with (a.out/(label+'.stdout')).open('xb') as stdout,(a.out/(label+'.stderr')).open('xb') as stderr:
                p=subprocess.run(cmd,stdout=stdout,stderr=stderr,env=env,timeout=1800,creationflags=subprocess.IDLE_PRIORITY_CLASS)
            evidence['runs'].append({'argv':cmd,'exit_code':p.returncode})
            need(p.returncode==0,(label,p.returncode))
            need(json.loads((a.out/label/'result.json').read_text())['status']=='PASS',label)
        if a.kind=='sanitizer':
            control=pathlib.Path('D:/a10/inputs/sanitizer_control.exe')
            evidence['control_sha256']=digest(control)
            for label,args,marker in [('ubsan',[],b'runtime error:'),('asan',['bounds'],b'AddressSanitizer')]:
                cmd=[str(control)]+args
                with (a.out/(label+'.log')).open('xb') as log:
                    p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=30,creationflags=subprocess.IDLE_PRIORITY_CLASS)
                need(p.returncode!=0 and marker in (a.out/(label+'.log')).read_bytes(),label)
                evidence['runs'].append({'argv':cmd,'exit_code':p.returncode,'expected_failure_detected':True})
        need(digest(a.exe)==expected,'binary hash after')
        need(all(digest(p)==h for p,h in evidence['inputs_sha256'].items()),'inputs after')
        evidence['status']='PASS'
    except BaseException as error:
        evidence['status']='FAIL'; evidence['error']=repr(error); raise
    finally:
        (a.out/'REPORT.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence,indent=2))

if __name__=='__main__':main()
