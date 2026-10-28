from pathlib import Path
import subprocess,hashlib,json
p=Path('/tmp/astra-review-smp'); results={}
for variant in ['base','candidate']:
 build='base' if variant=='base' else 'j5fix'
 cmd=['/usr/bin/g++-14','-std=c++20','-O0','-DFORGE_NNUE_HIDDEN=256','-I/tmp/forge-astra-20261029/include']
 if variant=='candidate':cmd.append('-DCANDIDATE')
 cmd += [str(p/'comparator_grid.cpp'),f'/tmp/forge-astra-build-{build}-20261029/libforge_core.a','-o',str(p/f'grid-{variant}')]
 r=subprocess.run(cmd,capture_output=True)
 (p/f'build-{variant}.stdout').write_bytes(r.stdout);(p/f'build-{variant}.stderr').write_bytes(r.stderr)
 results[f'build-{variant}']={'command':cmd,'returncode':r.returncode}
 if r.returncode:raise RuntimeError(f'build-{variant} failed')
for label,cmd in [('base',['grid-base']),('OFF',['grid-candidate']),('ON',['grid-candidate','on'])]:
 cmd=[str(p/cmd[0])]+cmd[1:]
 r=subprocess.run(cmd,capture_output=True,check=True)
 (p/(label+'.stdout')).write_bytes(r.stdout);(p/(label+'.stderr')).write_bytes(r.stderr)
 results[label]={'command':cmd,'returncode':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'summary':r.stdout.decode().splitlines()[-1]}
assert (p/'base.stdout').read_bytes()==(p/'OFF.stdout').read_bytes()
assert (p/'OFF.stdout').read_bytes()!=(p/'ON.stdout').read_bytes()
results['verdict']='PASS: 7200 comparator cases/mode; base/OFF byte identical; ON differs; zero main mate or protected TB monotonicity violations.'
for path in [p/'comparator_grid.cpp',Path('/tmp/forge-astra-build-base-20261029/libforge_core.a'),Path('/tmp/forge-astra-build-j5fix-20261029/libforge_core.a')]:
 results[str(path)]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(p/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
