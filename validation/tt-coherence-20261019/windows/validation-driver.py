from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

SOURCE=Path('/workspace/.cloud-setup/forge-windows-tt-coherent-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-tt-coherent')
BASE=Path('/workspace/.cloud-setup/forge-windows-tt-coherent-evidence')
OUT=BASE/'runtime-attempt1'
REPO=Path('/workspace/dwqww')
WINE=Path('/workspace/.cloud-setup/wine/usr/lib/wine/wine64')
TOOLCHAIN=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64')
WRAPPER=Path('/workspace/.cloud-setup/forge-tt-coherent-wine')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')
OUT.mkdir(exist_ok=False)
environment=os.environ.copy();environment.update(WINEPREFIX='/workspace/.cloud-setup/wine-prefix-ready',
 WINEDEBUG='-all',XDG_CACHE_HOME='/workspace/.cloud-setup/font-cache',PYTHONDONTWRITEBYTECODE='1')
WRAPPER.write_text('#!/usr/bin/env bash\nexport WINEPREFIX=/workspace/.cloud-setup/wine-prefix-ready\nexport WINEDEBUG=-all\nexport XDG_CACHE_HOME=/workspace/.cloud-setup/font-cache\nexec /workspace/.cloud-setup/wine/usr/lib/wine/wine64 /workspace/.cloud-setup/forge-windows-tt-coherent/forge.exe "$@"\n')
WRAPPER.chmod(0o755)
inputs={name:BUILD/name for name in ('forge.exe','forge_tests.exe','forge_tt_tests.exe','forge_bench.exe')}
inputs.update(uci_tool=SOURCE/'tools/uci_regression.py',ponder_tool=SOURCE/'tools/ponder_regression.py',wrapper=WRAPPER)
before={name:sha(path) for name,path in inputs.items()}
source_before=json.loads((BASE/'source-hashes.json').read_text())
assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==source_before
fixture_commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','77ee53b'],text=True).strip()
fixture=subprocess.check_output(['git','-C',str(REPO),'show',fixture_commit+':tests/tt_coherence_tests.cpp'])
assert hashlib.sha256(fixture).hexdigest()==sha(SOURCE/'tests/tt_coherence_tests.cpp')
commands=[('core',[str(WINE),str(BUILD/'forge_tests.exe')]),
          ('coherent-tt',[str(WINE),str(BUILD/'forge_tt_tests.exe')]),
          ('uci',[sys.executable,str(SOURCE/'tools/uci_regression.py'),str(WRAPPER),'--log',str(OUT/'uci-transcript.log')]),
          ('ponder',[sys.executable,str(SOURCE/'tools/ponder_regression.py'),str(WRAPPER)])]
write('protocol.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'production_commit':'df5d839a6a03f705310bb958601375fa9411e810','fixture_commit':fixture_commit,
 'fixture_sha256':sha(SOURCE/'tests/tt_coherence_tests.cpp'),'input_sha256':before,
 'commands':commands,'environment_subset':{k:environment[k] for k in ('WINEPREFIX','WINEDEBUG','XDG_CACHE_HOME','PYTHONDONTWRITEBYTECODE')},
 'scope':'Wine functional correctness only; no native Windows/Ryzen, speed or Elo claim',
 'concurrent_load':'Root authorized a separate -j2 6.4.4 Release build; no performance measurement'})
results=[]
try:
    for name,command in commands:
        started=time.monotonic()
        with (OUT/(name+'.log')).open('x') as log:
            completed=subprocess.run(command,env=environment,cwd=BUILD,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        record={'name':name,'exit_code':completed.returncode,'elapsed_seconds':time.monotonic()-started}
        results.append(record);write('progress.json',results);print(json.dumps(record),flush=True)
        if completed.returncode:raise RuntimeError(name+' failed')
    disassembly=subprocess.check_output([str(TOOLCHAIN/'bin/llvm-objdump'),'-d','--no-show-raw-insn',str(BUILD/'forge.exe')],text=True)
    (OUT/'disassembly.log').write_text(disassembly)
    import re
    simd={'avx2_minmax_ymm':bool(re.search(r'v(?:max|min)ps[^\n]*ymm',disassembly)),
          'avx2_multiply_ymm':bool(re.search(r'vmulps[^\n]*ymm',disassembly)),
          'avx2_add_ymm':bool(re.search(r'vaddps[^\n]*ymm',disassembly)),
          'fused_operations':re.findall(r'\bv(?:fmadd|fmsub|fnmadd|fnmsub)\w*\b',disassembly)}
    write('simd.json',simd)
    if not all(simd[key] for key in ('avx2_minmax_ymm','avx2_multiply_ymm','avx2_add_ymm')) or simd['fused_operations']:
        raise RuntimeError('SIMD arithmetic audit failed')
    after={name:sha(path) for name,path in inputs.items()}
    if after!=before:raise RuntimeError('runtime binary/tool inputs changed')
    if {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}!=source_before:
        raise RuntimeError('source export changed')
    write('result.json',{'status':'passed','checks':results,'simd':simd,'input_sha256_before':before,
                       'input_sha256_after':after,'source_unchanged':True,'fixture_commit':fixture_commit,
                       'scope':'Wine functional correctness only; native hardware, performance and Elo unproven'})
except Exception as error:
    write('result.json',{'status':'failed','checks':results,'error':str(error),
                       'input_sha256_after':{name:sha(path) for name,path in inputs.items()}})
    raise
print('All Windows functional and SIMD checks passed',flush=True)
