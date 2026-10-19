from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time

COMMIT='816423b1ddac23a00244449deef59dba736055a9'
SOURCE=Path('/workspace/.cloud-setup/forge-windows-rule50-context-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-rule50-context')
BASE=Path('/workspace/.cloud-setup/forge-windows-rule50-context-evidence')
OUT=BASE/'runtime-attempt1'
WINE=Path('/workspace/.cloud-setup/wine/usr/lib/wine/wine64')
TOOLS=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64/bin')
WRAPPER=Path('/workspace/.cloud-setup/forge-rule50-context-wine')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')
OUT.mkdir(exist_ok=False)
environment=os.environ.copy();environment.update(WINEPREFIX='/workspace/.cloud-setup/wine-prefix-ready',
 WINEDEBUG='-all',XDG_CACHE_HOME='/workspace/.cloud-setup/font-cache',PYTHONDONTWRITEBYTECODE='1')
WRAPPER.write_text('#!/usr/bin/env bash\nexport WINEPREFIX=/workspace/.cloud-setup/wine-prefix-ready\nexport WINEDEBUG=-all\nexport XDG_CACHE_HOME=/workspace/.cloud-setup/font-cache\nexec /workspace/.cloud-setup/wine/usr/lib/wine/wine64 /workspace/.cloud-setup/forge-windows-rule50-context/forge.exe "$@"\n')
WRAPPER.chmod(0o755)
inputs={p.name:p for p in BUILD.glob('*.exe')}
inputs.update(uci_tool=SOURCE/'tools/uci_regression.py',ponder_tool=SOURCE/'tools/ponder_regression.py',
 wrapper=WRAPPER,wine_loader=WINE,disassembler=TOOLS/'llvm-objdump')
before={name:sha(path) for name,path in inputs.items()}
source_before=json.loads((BASE/'source-hashes.json').read_text())
assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==source_before
commands=[('core',[str(WINE),str(BUILD/'forge_tests.exe')]),
 ('coherent-tt',[str(WINE),str(BUILD/'forge_tt_tests.exe')]),
 ('rule50',[str(WINE),str(BUILD/'forge_rule50_tests.exe')]),
 ('uci',[sys.executable,str(SOURCE/'tools/uci_regression.py'),str(WRAPPER),'--log',str(OUT/'uci-transcript.log')]),
 ('ponder',[sys.executable,str(SOURCE/'tools/ponder_regression.py'),str(WRAPPER)])]
simd_command=[str(TOOLS/'llvm-objdump'),'-d','--no-show-raw-insn',str(BUILD/'forge.exe')]
write('protocol.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_and_tests_commit':COMMIT,'input_sha256':before,'commands':commands,'simd_command':simd_command,
 'environment_subset':{k:environment[k] for k in ('WINEPREFIX','WINEDEBUG','XDG_CACHE_HOME','PYTHONDONTWRITEBYTECODE')},
 'scope':'Wine functional correctness only; no native hardware, speed or Elo result'})
checks=[]
try:
    for name,command in commands:
        started=time.monotonic()
        with (OUT/(name+'.log')).open('x') as log:
            completed=subprocess.run(command,env=environment,cwd=BUILD,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        item={'name':name,'exit_code':completed.returncode,'elapsed_seconds':time.monotonic()-started}
        checks.append(item);write('progress.json',checks);print(json.dumps(item),flush=True)
        if completed.returncode:raise RuntimeError(name+' failed')
    assert 'All8 TT coherence/regression groups passed' in (OUT/'coherent-tt.log').read_text()
    rule50=(OUT/'rule50.log').read_text()
    assert all(marker in rule50 for marker in ('targeted_regression_failures=0','reverse_q_direct','reverse_q_score_as_eval'))
    disassembly=subprocess.check_output(simd_command,text=True)
    (OUT/'disassembly.log').write_text(disassembly)
    simd={'avx2_minmax_ymm':bool(re.search(r'v(?:max|min)ps[^\n]*ymm',disassembly)),
          'avx2_multiply_ymm':bool(re.search(r'vmulps[^\n]*ymm',disassembly)),
          'avx2_add_ymm':bool(re.search(r'vaddps[^\n]*ymm',disassembly)),
          'fused_operations':re.findall(r'\bv(?:fmadd|fmsub|fnmadd|fnmsub)\w*\b',disassembly)}
    write('simd.json',simd)
    assert all(simd[key] for key in ('avx2_minmax_ymm','avx2_multiply_ymm','avx2_add_ymm')) and not simd['fused_operations']
    after={name:sha(path) for name,path in inputs.items()};assert after==before
    assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==source_before
    write('result.json',{'status':'passed','source_and_tests_commit':COMMIT,'checks':checks,'tt_groups':8,
     'rule50_targeted_failures':0,'simd':simd,'input_sha256_before':before,'input_sha256_after':after,
     'source_unchanged':True,'scope':'Wine functional correctness only; native, speed and Elo claims unproven'})
except Exception as error:
    write('result.json',{'status':'failed','source_and_tests_commit':COMMIT,'checks':checks,'error':str(error),
                         'input_sha256_after':{name:sha(path) for name,path in inputs.items()}})
    raise
print('All frozen6.4.4 Windows functional and SIMD checks passed',flush=True)
