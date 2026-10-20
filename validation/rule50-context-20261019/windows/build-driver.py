from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import datetime

COMMIT='816423b1ddac23a00244449deef59dba736055a9'
REPO=Path('/workspace/dwqww')
SOURCE=Path('/workspace/.cloud-setup/forge-windows-rule50-context-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-rule50-context')
OUT=Path('/workspace/.cloud-setup/forge-windows-rule50-context-evidence')
TOOLCHAIN=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64')
CMAKE='/workspace/.cloud-setup/venv/bin/cmake'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')
assert not any(p.exists() for p in (SOURCE,BUILD,OUT))
SOURCE.mkdir();OUT.mkdir()
names=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','--name-only',COMMIT,'--',
                              'CMakeLists.txt','LICENSE','include','src','bench','tests','tools'],text=True).splitlines()
for name in names:
    if name.endswith('.pyc'):continue
    p=SOURCE/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(subprocess.check_output(['git','-C',str(REPO),'show',COMMIT+':'+name]))
source_hashes={p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}
write('source-hashes.json',source_hashes)
write('production-hashes.json',{name:digest for name,digest in source_hashes.items()
                              if name=='CMakeLists.txt' or name.startswith(('src/','include/'))})
write('test-hashes.json',{name:digest for name,digest in source_hashes.items() if name.startswith('tests/')})
environment=os.environ.copy();environment.update(LLVM_MINGW_ROOT=str(TOOLCHAIN),PYTHONDONTWRITEBYTECODE='1')
commands=[[CMAKE,'-S',str(SOURCE),'-B',str(BUILD),'-DCMAKE_BUILD_TYPE=Release',
           '-DCMAKE_TOOLCHAIN_FILE='+str(SOURCE/'tools/windows-zen5.cmake')],
          [CMAKE,'--build',str(BUILD),'--parallel','1']]
write('commands.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_commit':COMMIT,'commands':commands,'source_directory':str(SOURCE),'build_directory':str(BUILD),
 'environment_subset':{'LLVM_MINGW_ROOT':str(TOOLCHAIN),'PYTHONDONTWRITEBYTECODE':'1'},
 'configuration':'Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
 'parallel_jobs':1,'scope':'Functional candidate; no performance or strength measurement'})
for command,name in zip(commands,('configure.log','build.log')):
    with (OUT/name).open('x') as log:result=subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        write('result.json',{'status':'build_failed','phase':name,'exit_code':result.returncode});raise SystemExit(result.returncode)
    print(name+' passed',flush=True)
for name in ('CMakeCache.txt','CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge.dir/link.txt'):
    shutil.copyfile(BUILD/name,OUT/name.replace('/','_'))
compiler=subprocess.check_output([str(TOOLCHAIN/'bin/x86_64-w64-mingw32-clang++'),'--version'],text=True)
(OUT/'compiler-version.txt').write_text(compiler)
binaries={p.name:{'sha256':sha(p),'bytes':p.stat().st_size,'path':str(p)} for p in BUILD.glob('*.exe')}
assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==source_hashes
write('result.json',{'status':'build_passed','source_commit':COMMIT,'binaries':binaries,
 'source_inputs_unchanged':True,'compiler':compiler.strip(),'runtime_validation':'pending',
 'script_sha256':sha(Path(__file__))})
print(json.dumps({'status':'build_passed','source_commit':COMMIT,'binaries':binaries},indent=2))
