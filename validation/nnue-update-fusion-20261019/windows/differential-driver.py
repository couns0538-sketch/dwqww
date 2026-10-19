from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import struct
import subprocess

REPO=Path('/workspace/dwqww')
SOURCE=Path('/workspace/.cloud-setup/forge-windows-nnue-update-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-nnue-update')
PARENT=Path('/workspace/.cloud-setup/forge-windows-ownbook-control')
PARENT_SOURCE=Path('/workspace/.cloud-setup/forge-windows-ownbook-control-source')
OUT=Path('/workspace/.cloud-setup/forge-windows-nnue-update-evidence/differential-attempt1')
TOOLS=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64/bin')
WINE=Path('/workspace/.cloud-setup/wine/usr/lib/wine/wine64')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda name,value:(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
OUT.mkdir(exist_ok=False)
environment=os.environ.copy()
environment.update(WINEPREFIX='/workspace/.cloud-setup/wine-prefix-ready',WINEDEBUG='-all',
 XDG_CACHE_HOME='/workspace/.cloud-setup/font-cache',PYTHONDONTWRITEBYTECODE='1')
flags=['-std=c++20','-O3','-DNDEBUG','-march=znver5','-mtune=znver5',
 '-fno-fast-math','-ffp-contract=off','-fno-lto','-I',str(SOURCE/'include')]
native=REPO/'validation/nnue-update-fusion-20261019'
native_inputs={name:native/name for name in ('parent-update-snapshot.bin','candidate-nnue_update_snapshot.bin',
 'parent-nnue_snapshot.bin','candidate-nnue_snapshot.bin')}
inputs={'parent-core':PARENT/'libforge_core.a','candidate-core':BUILD/'libforge_core.a',
 'compiler':TOOLS/'x86_64-w64-mingw32-clang++','wine-loader':WINE,
 'update-driver':SOURCE/'tools/nnue_update_snapshot.cpp','old-driver':SOURCE/'tools/nnue_snapshot.cpp',
 **native_inputs}
before={name:sha(path) for name,path in inputs.items()}
parent_hashes=json.loads((REPO/'validation/ownbook-control-20261019/windows/source-hashes.json').read_text())
candidate_hashes=json.loads((OUT.parent/'source-hashes.json').read_text())
guards={name:parent_hashes[name]==candidate_hashes[name] for name in parent_hashes
 if name.startswith('include/') or name.startswith('src/nnue_weights')}
assert all(guards.values())
commands=[]
for driver in ('nnue_update_snapshot','nnue_snapshot'):
 for label,core in (('parent649',PARENT/'libforge_core.a'),('candidate6410',BUILD/'libforge_core.a')):
  binary=OUT/(label+'-'+driver+'.exe')
  command=[str(TOOLS/'x86_64-w64-mingw32-clang++'),*flags,str(SOURCE/('tools/'+driver+'.cpp')),
   str(core),'-pthread','-static','-o',str(binary)]
  commands.append({'name':label+'-'+driver,'command':command,'execute':[str(WINE),str(binary)],
   'core':str(core),'source':str(SOURCE/('tools/'+driver+'.cpp'))})
write('protocol.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'parent_source_commit':'4edda780c68a742f20565d4e6a54a0c99a2c88a6',
 'candidate_source_commit':'36f5b2f6e1ff519e82a4b52edc85caceaf15aed0','commands':commands,
 'input_sha256_before':before,'unchanged_api_and_network_guards':guards,
 'environment_subset':{key:environment[key] for key in ('WINEPREFIX','WINEDEBUG','XDG_CACHE_HOME','PYTHONDONTWRITEBYTECODE')},
 'comparison':'cmp actual parent/candidate Windows streams before hashing; compare native streams only with matching update-header floating-point controls; preserve mismatches',
 'scope':'Finite-input API equality only; no timing, speed, NPS, Elo, or native-hardware claim'})
results=[]
try:
 for item in commands:
  name=item['name']
  with (OUT/(name+'-compile.log')).open('xb') as log:
   compiled=subprocess.run(item['command'],env=environment,stdout=log,stderr=subprocess.STDOUT)
  if compiled.returncode:raise RuntimeError(name+' compile failed with '+str(compiled.returncode))
  with (OUT/(name+'.bin')).open('xb') as stdout,(OUT/(name+'-stderr.log')).open('xb') as stderr:
   completed=subprocess.run(item['execute'],env=environment,stdout=stdout,stderr=stderr,timeout=300)
  row={'name':name,'compile_return_code':compiled.returncode,'execute_return_code':completed.returncode,
   'executable_sha256':sha(Path(item['execute'][1])),'core_sha256':sha(Path(item['core'])),
   'driver_sha256':sha(Path(item['source'])),'stream_bytes':(OUT/(name+'.bin')).stat().st_size}
  results.append(row);write('progress.json',results);print(json.dumps(row),flush=True)
  if completed.returncode:raise RuntimeError(name+' execution failed with '+str(completed.returncode))
 comparisons=[]
 for driver,size in (('nnue_update_snapshot',4097860),('nnue_snapshot',21192328)):
  gold=OUT/('parent649-'+driver+'.bin');child=OUT/('candidate6410-'+driver+'.bin')
  compare=['cmp',str(gold),str(child)]
  with (OUT/(driver+'-cmp.log')).open('xb') as log:
   result=subprocess.run(compare,stdout=log,stderr=subprocess.STDOUT)
  comparisons.append({'command':compare,'exit_code':result.returncode,'bytes':gold.stat().st_size})
  assert result.returncode==0 and gold.stat().st_size==child.stat().st_size==size
  comparisons[-1]['sha256']=sha(gold)
 controls={name:struct.unpack('<III',path.read_bytes()[:12]) for name,path in {
  'windows_parent':OUT/'parent649-nnue_update_snapshot.bin',
  'windows_candidate':OUT/'candidate6410-nnue_update_snapshot.bin',
  'linux_parent':native_inputs['parent-update-snapshot.bin'],
  'linux_candidate':native_inputs['candidate-nnue_update_snapshot.bin']}.items()}
 assert all(value[0]==0x3155554e and value[1]==128 for value in controls.values())
 same_controls=len(set(controls.values()))==1
 native_comparisons=[]
 for driver,native_parent,native_child in (
  ('nnue_update_snapshot','parent-update-snapshot.bin','candidate-nnue_update_snapshot.bin'),
  ('nnue_snapshot','parent-nnue_snapshot.bin','candidate-nnue_snapshot.bin')):
  for label,native_name in (('parent649',native_parent),('candidate6410',native_child)):
   command=['cmp',str(OUT/(label+'-'+driver+'.bin')),str(native_inputs[native_name])]
   with (OUT/(label+'-'+driver+'-linux-cmp.log')).open('xb') as log:
    comparison=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
   native_comparisons.append({'command':command,'exit_code':comparison.returncode,
    'floating_point_controls_match':same_controls,'scope':'cross-platform byte equality' if same_controls else 'diagnostic comparison; floating-point controls differ'})
 after={name:sha(path) for name,path in inputs.items()}
 assert before==after
 write('result.json',{'status':'passed','parent_source_commit':'4edda780c68a742f20565d4e6a54a0c99a2c88a6',
  'candidate_source_commit':'36f5b2f6e1ff519e82a4b52edc85caceaf15aed0','results':results,
  'windows_parent_candidate_comparisons':comparisons,'update_header_words':controls,
  'floating_point_controls_identical':same_controls,'native_comparisons':native_comparisons,
  'native_all_identical':same_controls and all(item['exit_code']==0 for item in native_comparisons),
  'input_sha256_before':before,'input_sha256_after':after,'unchanged_api_and_network_guards':guards,
  'scope':'Finite-input NNUE API parity only; no speed, NPS, timing, Elo, or native hardware claim'})
 print('Windows actual649/6410 update and original snapshot streams are byte-identical.',flush=True)
 print(json.dumps({'floating_point_controls_identical':same_controls,'native_all_identical':same_controls and all(item['exit_code']==0 for item in native_comparisons)}),flush=True)
except Exception as error:
 write('result.json',{'status':'failed','error':repr(error),'results':results,
  'input_sha256_before':before,'input_sha256_after':{name:sha(path) for name,path in inputs.items()}})
 raise
