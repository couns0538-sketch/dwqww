"""Build unchanged Forge offline probe against frozen R9 source; auxiliary only."""
import argparse, hashlib, json, os, pathlib, subprocess, sys
ROOT=pathlib.Path('D:/a10')
sys.path.insert(0,str(ROOT/'pydeps'))
import psutil
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    a=argparse.ArgumentParser();a.add_argument('--threads',type=int,choices=[1],required=True)
    a.add_argument('--out',type=pathlib.Path,required=True);args=a.parse_args()
    if not args.out.is_absolute() or not args.out.is_relative_to(ROOT/'job3') or args.out.exists():raise ValueError('new owned output required')
    me=psutil.Process()
    if me.nice()!=psutil.IDLE_PRIORITY_CLASS or not set(me.cpu_affinity())<={2,3}:raise RuntimeError('safe launcher required')
    out=args.out;out.mkdir(parents=True)
    compiler=pathlib.Path('C:/msys64/ucrt64/bin/g++.exe')
    if sha(compiler)!='08c11faa4f15a460af8d90a2fd90f658658938c94051bde8babfbecce3304c6c':raise ValueError('compiler drift')
    harness=ROOT/'job3/source/tools/data/forge_data_probe.cpp'
    sources=sorted(p for p in (ROOT/'c1/src').glob('*.cpp') if p.name not in ('main.cpp','uci.cpp'))
    inputs={str(p):sha(p) for p in [harness,compiler,*sources,*sorted((ROOT/'c1/include').rglob('*.hpp')),*sorted((ROOT/'c1/src').glob('*.inc'))]}
    exe=out/'forge_data_probe.exe'
    argv=[str(compiler),'-std=c++20','-O2','-DFORGE_NNUE_HIDDEN=256','-ffp-contract=off','-fno-fast-math','-march=znver5','-static','-pthread','-I'+str(ROOT/'c1/include'),str(harness),*map(str,sources),'-o',str(exe)]
    env=os.environ.copy();env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','');env['TEMP']=env['TMP']=str(ROOT/'tmp')
    (out/'command.json').write_text(json.dumps({'argv':argv,'cwd':str(out),'inputs':inputs,'scope':'auxiliary probe only; NOT kit candidate, NOT a new engine handover'},indent=2))
    with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
        result=subprocess.run(argv,cwd=out,env=env,stdout=stdout,stderr=stderr,timeout=300)
    report={'exit_code':result.returncode,'inputs_unchanged':all(sha(p)==h for p,h in inputs.items()),'classification':'UNPROVEN','auxiliary_only':True}
    if result.returncode==0:
        report['binary_sha256']=sha(exe)
        smoke=subprocess.run([str(exe),'--describe'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,env=env)
        (out/'describe.stdout').write_bytes(smoke.stdout);(out/'describe.stderr').write_bytes(smoke.stderr)
        report['describe_exit']=smoke.returncode
    (out/'REPORT.json').write_text(json.dumps(report,indent=2))
    return result.returncode if result.returncode else (0 if report['inputs_unchanged'] else 1)
if __name__=='__main__':raise SystemExit(main())
