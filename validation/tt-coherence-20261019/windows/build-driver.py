from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess

REPO=Path('/workspace/dwqww')
COMMIT='df5d839a6a03f705310bb958601375fa9411e810'
SOURCE=Path('/workspace/.cloud-setup/forge-windows-tt-coherent-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-tt-coherent')
EVIDENCE=Path('/workspace/.cloud-setup/forge-windows-tt-coherent-evidence')
TOOLCHAIN=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64')
CMAKE='/workspace/.cloud-setup/venv/bin/cmake'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,data):(EVIDENCE/name).write_text(json.dumps(data,indent=2)+'\n')
assert not SOURCE.exists() and not BUILD.exists() and not EVIDENCE.exists()
SOURCE.mkdir();EVIDENCE.mkdir()
files=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','--name-only',COMMIT,'--',
                               'CMakeLists.txt','LICENSE','include','src','bench','tests','tools'],text=True).splitlines()
production={}
for name in files:
    if name.endswith('.pyc'):continue
    data=subprocess.check_output(['git','-C',str(REPO),'show',COMMIT+':'+name])
    destination=SOURCE/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
    if name=='CMakeLists.txt' or name.startswith(('src/','include/')):
        assert (REPO/name).read_bytes()==data, 'Working production source differs from requested commit: '+name
        production[name]=sha(destination)
# Root may have refined this regression fixture without changing engine code.
fixture='tests/tt_coherence_tests.cpp'
shutil.copyfile(REPO/fixture,SOURCE/fixture)
fixture_diff=subprocess.check_output(['git','-C',str(REPO),'diff',COMMIT,'--',fixture],text=True)
(EVIDENCE/'test-fixture.diff').write_text(fixture_diff)
write('source-hashes.json',{p.relative_to(SOURCE).as_posix():sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()})
write('production-hashes.json',production)
environment=os.environ.copy();environment['LLVM_MINGW_ROOT']=str(TOOLCHAIN);environment['PYTHONDONTWRITEBYTECODE']='1'
commands=[[CMAKE,'-S',str(SOURCE),'-B',str(BUILD),'-DCMAKE_BUILD_TYPE=Release',
           '-DCMAKE_TOOLCHAIN_FILE='+str(SOURCE/'tools/windows-zen5.cmake')],
          [CMAKE,'--build',str(BUILD),'-j1']]
metadata={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'production_commit':COMMIT,'worktree_head_observed':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
          'source_directory':str(SOURCE),'build_directory':str(BUILD),'commands':commands,
          'environment_subset':{'LLVM_MINGW_ROOT':str(TOOLCHAIN),'PYTHONDONTWRITEBYTECODE':'1'},
          'configuration':'Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
          'parallel_jobs':1,'runtime_validation':'Not run; Wine checks await root coordination',
          'fixture_sha256':sha(SOURCE/fixture),'fixture_diff_sha256':sha(EVIDENCE/'test-fixture.diff')}
write('commands.json',metadata)
for command,name in zip(commands,('configure.log','build.log')):
    with (EVIDENCE/name).open('x') as log:
        completed=subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT)
    if completed.returncode:
        write('result.json',{'status':'build_failed','phase':name,'exit_code':completed.returncode});raise SystemExit(completed.returncode)
    print(name+' passed',flush=True)
for name in ('CMakeCache.txt','CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge.dir/link.txt'):
    shutil.copyfile(BUILD/name,EVIDENCE/name.replace('/','_'))
compiler=subprocess.check_output([str(TOOLCHAIN/'bin/x86_64-w64-mingw32-clang++'),'--version'],text=True)
(EVIDENCE/'compiler-version.txt').write_text(compiler)
binaries={name:{'path':str(BUILD/name),'sha256':sha(BUILD/name),'bytes':(BUILD/name).stat().st_size}
          for name in ('forge.exe','forge_tests.exe','forge_tt_tests.exe','forge_bench.exe')}
current={p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}
assert current==json.loads((EVIDENCE/'source-hashes.json').read_text())
result={'status':'build_passed','production_commit':COMMIT,'binaries':binaries,
        'source_inputs_unchanged':True,'compiler':compiler.strip(),
        'runtime_validation':'Not run; hold Wine pending root coordination',
        'commands_sha256':sha(EVIDENCE/'commands.json'),'production_hashes_sha256':sha(EVIDENCE/'production-hashes.json'),
        'script_sha256':sha(Path(__file__))}
write('result.json',result);print(json.dumps(result,indent=2))
