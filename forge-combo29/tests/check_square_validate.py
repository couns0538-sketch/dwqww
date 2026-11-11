#!/usr/bin/env python3
"""Frozen S11 correctness gates. No timing or strength experiment."""
import argparse,hashlib,json,os,pathlib,subprocess
LOCK='16833ecc03b425586f91f4c8834dea8807bf4c22';CANDIDATE='1e6c398dec7717868a740f5d322cf7434336345f'
p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('/workspace/shared/forge-build/check-square'));a=p.parse_args()
if not a.run:p.exit(message='Use --run only after coordination.\n')
tests=pathlib.Path(__file__).resolve().parent;repo=tests.parents[1];out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);root=out/'source';root.mkdir(exist_ok=True)
rpt=dict(lock=LOCK,candidate=CANDIDATE,commands=[],snapshots={},binaries={},units=[],mutations=[],passed=False)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save():(tests/'check_square_validation.json').write_text(json.dumps(rpt,indent=2)+'\n')
def run(cmd,**kw):
 rpt['commands'].append(list(map(str,cmd)));save();print('RUN',' '.join(map(str,cmd)),flush=True)
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=600,**kw)
 print(r.stdout,r.stderr,flush=True);return r
def snapshot(rev):
 manifest={}
 for n in subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','--name-only',rev,'forge-combo29/src','forge-combo29/include']).decode().splitlines():
  assert pathlib.Path(n).suffix in ('.cpp','.hpp','.h','.inc');data=subprocess.check_output(['git','-C',str(repo),'show',f'{rev}:{n}']);t=root/pathlib.Path(n).relative_to('forge-combo29');t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(data);manifest[n]=sha(t)
 rpt['snapshots'][rev]=manifest;save()
flags=['-std=c++20','-O3','-DNDEBUG','-DFORGE_NNUE_HIDDEN=256','-DFORGE_EXPOSE_TUNABLES=1','-DFORGE_SPD_TT_NOTLS=1','-DFORGE_SPD_PREFETCH_EARLY=1','-DFORGE_SPD_SLIDER_PEXT=1','-DFORGE_SPD_NNUE_ZMM=1','-ffp-contract=off','-fno-fast-math','-march=x86-64-v4','-pthread','-Iinclude','-Isrc']
for label,rev,enabled in [('lock',LOCK,0),('off',CANDIDATE,0),('on',CANDIDATE,1)]:
 snapshot(rev);exe=out/label
 r=run(['g++',*flags,'-DFORGE_SPD_NO_ZERO_MOVELISTS=2','-DFORGE_SEARCH_SPEED2=1',f'-DFORGE_SPD_CHECK_SQUARE_PRESENCE={enabled}',*sorted((root/'src').glob('*.cpp')),'-o',exe],cwd=root);assert r.returncode==0
 rpt['binaries'][label]=dict(path=str(exe),sha256=sha(exe));save()
assert rpt['binaries']['lock']['sha256']==rpt['binaries']['off']['sha256']
r=run(['bash',tests.parent/'scripts/check_pins.sh',out/'on'],cwd=out);(tests/'check_square_pins.log').write_text(r.stdout+r.stderr);assert r.returncode==0
(tests/'check_square_pins_raw.log').write_bytes((out/'pins_out.txt').read_bytes())
r=run(['python3',tests/'equivalence_screen.py',out/'lock',out/'on','--output',tests/'check_square_equivalence.json']);assert r.returncode==0
# Same fixture bytes and oracle are recorded; no external runtime source.
fixture=tests/'equivalence_positions.fen';rpt['fixture_sha256']=sha(fixture);rpt['unit_sha256']=sha(tests/'check_square_unit.cpp')
unitflags=['-std=c++20','-O1','-g','-DNDEBUG','-DFORGE_NNUE_HIDDEN=256','-DFORGE_SPD_SLIDER_PEXT=0','-DFORGE_SPD_NNUE_ZMM=0','-DFORGE_SPD_CHECK_SQUARE_PRESENCE=1','-pthread','-Iinclude','-Isrc']
sanflags=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
# Reuse only common objects built with the exact same generation/sanitizer flags.
for zero in (0,1,2):
 common=[]
 for name in ('bitboard','board','book','eval','eval_params','nnue'):
  obj=out/f'{name}-z{zero}.o';r=run(['g++',*unitflags,*sanflags,f'-DFORGE_SPD_NO_ZERO_MOVELISTS={zero}','-c',root/f'src/{name}.cpp','-o',obj],cwd=root);assert r.returncode==0;common.append(obj)
 for speed in (0,1):
  exe=out/f'unit-s{speed}-z{zero}'
  r=run(['g++',*unitflags,*sanflags,f'-DFORGE_SPD_NO_ZERO_MOVELISTS={zero}',f'-DFORGE_SEARCH_SPEED2={speed}',tests/'check_square_unit.cpp',*common,'-o',exe],cwd=root);assert r.returncode==0
  r=run([exe,fixture],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'});rpt['units'].append(dict(speed2=speed,no_zero_lists=zero,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,binary_sha256=sha(exe)));save();assert r.returncode==0
  if len(rpt['units'])>1:assert r.stdout==rpt['units'][0]['stdout']
# Mutate only scratch source. Reuse z2 sanitizer objects to keep flags identical.
source=root/'src/search.cpp';original=source.read_text()
mutations={
 'drop_queen_from_bishop':('(board_.pieces(us, Bishop) | queens) != 0','board_.pieces(us, Bishop) != 0'),
 'drop_queen_from_rook':('(board_.pieces(us, Rook) | queens) != 0','board_.pieces(us, Rook) != 0'),
 'poison_absent_slot':('? attacks::bishop(enemy_king, occupancy) : 0;','? attacks::bishop(enemy_king, occupancy) : ~Bitboard(0);'),
}
for name,(old,new) in mutations.items():
 assert original.count(old)==1;source.write_text(original.replace(old,new));exe=out/name
 r=run(['g++',*unitflags,*sanflags,'-DFORGE_SPD_NO_ZERO_MOVELISTS=2','-DFORGE_SEARCH_SPEED2=1',tests/'check_square_unit.cpp',*common,'-o',exe],cwd=root);assert r.returncode==0
 r=run([exe,fixture],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'});rpt['mutations'].append(dict(name=name,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));save();assert r.returncode!=0 and 'FAIL' in r.stderr
source.write_text(original);rpt['passed']=True;save();print('ALL CHECK SQUARE GATES PASSED',flush=True)
