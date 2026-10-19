from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess

COMMIT='2c0c7efa49023d8e3f49de3f5596f333a3f01202'
REPO=Path('/workspace/dwqww')
SOURCE=Path('/workspace/.cloud-setup/forge-windows-lazy-movepicker-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-lazy-movepicker')
OUT=Path('/workspace/.cloud-setup/forge-windows-lazy-movepicker-evidence')
TOOLCHAIN=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64')
CMAKE='/workspace/.cloud-setup/venv/bin/cmake'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
assert not any(p.exists() for p in (SOURCE,BUILD,OUT))
SOURCE.mkdir();OUT.mkdir()
names=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','--name-only',COMMIT,'--',
 'CMakeLists.txt','LICENSE','include','src','bench','tests','tools'],text=True).splitlines()
for name in names:
    if name.endswith('.pyc'):continue
    target=SOURCE/name;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(subprocess.check_output(['git','-C',str(REPO),'show',COMMIT+':'+name]))
all_hashes={p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}
write('source-hashes.json',all_hashes)
write('production-hashes.json',{name:value for name,value in all_hashes.items()
                              if name=='CMakeLists.txt' or name.startswith(('src/','include/'))})
write('test-hashes.json',{name:value for name,value in all_hashes.items() if name.startswith('tests/')})
environment=os.environ.copy();environment.update(LLVM_MINGW_ROOT=str(TOOLCHAIN),PYTHONDONTWRITEBYTECODE='1')
commands=[[CMAKE,'-S',str(SOURCE),'-B',str(BUILD),'-DCMAKE_BUILD_TYPE=Release',
           '-DCMAKE_TOOLCHAIN_FILE='+str(SOURCE/'tools/windows-zen5.cmake')],
          [CMAKE,'--build',str(BUILD),'--parallel','2']]
write('commands.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_and_tests_commit':COMMIT,'source_directory':str(SOURCE),'build_directory':str(BUILD),
 'commands':commands,'environment_subset':{'LLVM_MINGW_ROOT':str(TOOLCHAIN),'PYTHONDONTWRITEBYTECODE':'1'},
 'configuration':'Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
 'parallel_jobs':2,'runtime_checks':'pending','scope':'Build only; no performance/strength result'})
for command,name in zip(commands,('configure.log','build.log')):
    with (OUT/name).open('x') as log:result=subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        write('result.json',{'status':'build_failed','phase':name,'exit_code':result.returncode});raise SystemExit(result.returncode)
    print(name+' passed',flush=True)
for name in ('CMakeCache.txt','CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge.dir/link.txt'):
    shutil.copyfile(BUILD/name,OUT/name.replace('/','_'))
compiler=subprocess.check_output([str(TOOLCHAIN/'bin/x86_64-w64-mingw32-clang++'),'--version'],text=True)
(OUT/'compiler-version.txt').write_text(compiler)
assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==all_hashes
result={'status':'build_passed','source_and_tests_commit':COMMIT,'source_inputs_unchanged':True,
 'binaries':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size,'path':str(p)} for p in BUILD.glob('*.exe')},
 'compiler':compiler.strip(),'runtime_validation':'pending','script_sha256':sha(Path(__file__))}
write('result.json',result);print(json.dumps(result,indent=2))
