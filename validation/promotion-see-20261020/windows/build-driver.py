from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess

COMMIT='47f0560221d986e41a309853e1295c557fcf5bf6'
REPO=Path('/workspace/dwqww')
SOURCE=Path('/workspace/.cloud-setup/forge-promotion-windows-source')
BUILD=Path('/workspace/.cloud-setup/forge-promotion-windows-build')
OUT=Path('/workspace/dwqww/validation/promotion-see-20261020/windows')
TOOLCHAIN=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64')
CMAKE='/workspace/.cloud-setup/venv/bin/cmake'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
assert json.loads((OUT/'WINDOWS-BUILD-CLEAR.json').read_text())['authorization']=='17 WINDOWS BUILD CLEAR'
assert not BUILD.exists() and SOURCE.is_dir()
all_hashes=json.loads((OUT/'source-hashes.json').read_text())
assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==all_hashes
pinned=json.loads((OUT/'PINNED-TOOLS.json').read_text())['tools']
for name in ['compiler','compiler_config','cmake','toolchain_source']:
    assert sha(Path(pinned[name]['path']))==pinned[name]['sha256'], 'Pinned tool changed: '+name
environment=os.environ.copy();environment.update(LLVM_MINGW_ROOT=str(TOOLCHAIN),PYTHONDONTWRITEBYTECODE='1')
commands=[[CMAKE,'-S',str(SOURCE),'-B',str(BUILD),'-DCMAKE_BUILD_TYPE=Release',
           '-DCMAKE_TOOLCHAIN_FILE='+str(SOURCE/'tools/windows-zen5.cmake'),'-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'],
          [CMAKE,'--build',str(BUILD),'--parallel','1']]
write('commands.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_and_tests_commit':COMMIT,'source_directory':str(SOURCE),'build_directory':str(BUILD),
 'commands':commands,'environment_subset':{'LLVM_MINGW_ROOT':str(TOOLCHAIN),'PYTHONDONTWRITEBYTECODE':'1'},
 'configuration':'Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
 'parallel_jobs':1,'runtime_checks':'pending','scope':'Build only; no performance/strength result'})
for command,name in zip(commands,('configure.log','build.log')):
    with (OUT/name).open('x') as log:result=subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        write('result.json',{'status':'build_failed','phase':name,'exit_code':result.returncode});raise SystemExit(result.returncode)
    print(name+' passed',flush=True)
for name in ('CMakeCache.txt','CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge.dir/link.txt'):
    shutil.copyfile(BUILD/name,OUT/name.replace('/','_'))
for extra in [BUILD/'compile_commands.json', *sorted((BUILD/'CMakeFiles').glob('*.dir/flags.make')), *sorted((BUILD/'CMakeFiles').glob('*.dir/link.txt'))]:
    shutil.copyfile(extra,OUT/extra.relative_to(BUILD).as_posix().replace('/','_'))
compiler=subprocess.check_output([str(TOOLCHAIN/'bin/x86_64-w64-mingw32-clang++'),'--version'],text=True)
(OUT/'compiler-version.txt').write_text(compiler)
assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==all_hashes
result={'status':'build_passed','source_and_tests_commit':COMMIT,'source_inputs_unchanged':True,
 'binaries':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size,'path':str(p)} for p in BUILD.glob('*.exe')},
 'libraries':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size,'path':str(p)} for p in BUILD.glob('*.a')},
 'compiler':compiler.strip(),'runtime_validation':'pending','script_sha256':sha(Path(__file__))}
write('result.json',result);print(json.dumps(result,indent=2))
