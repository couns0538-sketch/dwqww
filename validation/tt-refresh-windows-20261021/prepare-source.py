from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess

from pipeline_gate import load_freeze
FREEZE=load_freeze('source')
COMMIT=FREEZE['source_commit']
REPO=Path('/workspace/dwqww')
SOURCE=Path('/workspace/.cloud-setup/windows6423-source')
BUILD=Path('/workspace/.cloud-setup/windows6423-build')
OUT=Path('/workspace/dwqww/validation/tt-refresh-windows-20261021')
TOOLCHAIN=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64')
CMAKE='/workspace/.cloud-setup/venv/bin/cmake'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
assert not any(p.exists() for p in (SOURCE,BUILD))
SOURCE.mkdir()
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
write('PREPARED-SOURCE.json',{'status':'EXPORTED_ONLY_NO_COMPILER_OR_ENGINE','source_commit':COMMIT,'source_directory':str(SOURCE),'build_directory':str(BUILD),'source_files':len(all_hashes)})
print('Exported frozen23 source only:',len(all_hashes),'files')
