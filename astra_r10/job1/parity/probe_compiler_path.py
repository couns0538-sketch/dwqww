"""Bounded compiler-startup diagnosis only; no Forge compilation."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ap=argparse.ArgumentParser();ap.add_argument('--threads',type=int,choices=[1],required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
root=Path(a.out)
if '..' in root.parts or not root.is_absolute() or not root.is_relative_to(Path('D:/a10')): raise ValueError('D:/a10 output required')
root.mkdir()
gpp=Path('C:/msys64/ucrt64/bin/g++.exe')
cc1=Path('C:/msys64/ucrt64/lib/gcc/x86_64-w64-mingw32/15.2.0/cc1plus.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if sha(gpp)!='08c11faa4f15a460af8d90a2fd90f658658938c94051bde8babfbecce3304c6c':raise ValueError('compiler hash mismatch')
tiny=root/'probe.cpp';tiny.write_text('int main() { return 0; }\n',encoding='ascii')
report={'scope':'compiler startup control; no native Forge proof','compiler_sha256':sha(gpp),'cc1plus_sha256':sha(cc1),'runs':[]}
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
previous=kernel.SetErrorMode(0x0001|0x0002|0x8000)
try:
    for mode in ('inherited','kit-path'):
        env=os.environ.copy()
        if mode=='kit-path':env['PATH']='C:\\msys64\\ucrt64\\bin;'+env.get('PATH','')
        for label,argv in [('driver-version',[str(gpp),'--version']),('cc1plus-version',[str(cc1),'--version']),('syntax-probe',[str(gpp),'-fsyntax-only',str(tiny)])]:
            prefix=root/(mode+'-'+label);started=time.monotonic()
            with prefix.with_suffix('.stdout.log').open('xb') as out,prefix.with_suffix('.stderr.log').open('xb') as err:
                child=subprocess.run(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
            report['runs'].append({'mode':mode,'probe':label,'argv':argv,'PATH':env.get('PATH',''),'exit_code':child.returncode,'exit_hex':hex(child.returncode&0xffffffff),'wall_seconds':time.monotonic()-started})
finally:kernel.SetErrorMode(previous)
(root/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
for row in report['runs']:print(row['mode'],row['probe'],row['exit_code'],row['exit_hex'])
bad=next(r for r in report['runs'] if r['mode']=='inherited' and r['probe']=='syntax-probe')
good=[r for r in report['runs'] if r['mode']=='kit-path']
if bad['exit_code']==0 or any(r['exit_code']!=0 for r in good):raise SystemExit('PATH hypothesis NOT confirmed')
print('CONFIRMED: only process-local kit PATH changes startup/syntax-probe failure to success')
