#!/usr/bin/env python3
"""Frozen candidate correctness gates; no timing experiment."""
import argparse,hashlib,json,os,pathlib,re,subprocess
LOCK='16833ecc03b425586f91f4c8834dea8807bf4c22'
CANDIDATE='8c447f4e676f86ee034f82b33cd0856b00eed230'
p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('/workspace/shared/forge-build/evasion-prefilter'));a=p.parse_args()
if not a.run:p.exit(message='Default off. Explicit --run after coordination required.\n')
tests=pathlib.Path(__file__).resolve().parent;repo=tests.parents[1];out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
root=out/'source';root.mkdir(exist_ok=True)
receipt={'lock':LOCK,'candidate':CANDIDATE,'commands':[],'snapshots':{},'binary_identity':{},'sanitizers':[],'mutations':[]}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(): (tests/'evasion_prefilter_validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
def run(cmd,**kw):
 receipt['commands'].append(list(map(str,cmd)));save();print('RUN', ' '.join(map(str,cmd)),flush=True)
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=600,**kw)
 if r.returncode: print(r.stdout,r.stderr,flush=True)
 return r
def snapshot(rev):
 names=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','--name-only',rev,'forge-combo29/src','forge-combo29/include']).decode().splitlines();manifest={}
 for n in names:
  assert pathlib.Path(n).suffix in ('.hpp','.h','.cpp','.inc')
  data=subprocess.check_output(['git','-C',str(repo),'show',f'{rev}:{n}']);t=root/pathlib.Path(n).relative_to('forge-combo29');t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(data);manifest[n]=sha(t)
 receipt['snapshots'][rev]=manifest;save()
flags=['-std=c++20','-O3','-DNDEBUG','-DFORGE_NNUE_HIDDEN=256','-DFORGE_EXPOSE_TUNABLES=1','-DFORGE_SPD_TT_NOTLS=1','-DFORGE_SPD_NO_ZERO_MOVELISTS=2','-DFORGE_SEARCH_SPEED2=1','-DFORGE_SPD_PREFETCH_EARLY=1','-DFORGE_SPD_SLIDER_PEXT=1','-DFORGE_SPD_NNUE_ZMM=1','-ffp-contract=off','-fno-fast-math','-march=x86-64-v4','-pthread','-Iinclude','-Isrc']
for label,rev,extra in [('lock',LOCK,[]),('off',CANDIDATE,[]),('on',CANDIDATE,['-DFORGE_SPD_CHECK_EVASION_PREFILTER=1'])]:
 snapshot(rev);exe=out/label
 r=run(['g++-14',*flags,*extra,*sorted((root/'src').glob('*.cpp')),'-o',exe],cwd=root);assert r.returncode==0
 receipt['binary_identity'][label]=sha(exe);save()
assert receipt['binary_identity']['lock']==receipt['binary_identity']['off'],'off binary differs from immutable lock'
r=run(['bash',tests.parent/'scripts/check_pins.sh',out/'on'],cwd=out)
(tests/'evasion_prefilter_pins.log').write_text(r.stdout+r.stderr);assert r.returncode==0
(tests/'evasion_prefilter_pins_raw.log').write_bytes((out/'pins_out.txt').read_bytes())
r=run(['python3',tests/'equivalence_screen.py',out/'lock',out/'on','--fixtures',tests/'evasion_prefilter_positions.fen','--output',tests/'evasion_prefilter_equivalence.json']);assert r.returncode==0
# Frozen fixture corpus plus explicit roots needed for coverage counters.
fixtures=(tests/'evasion_prefilter_positions.fen').read_text()+'\n4r2k/8/8/8/1b6/8/PP6/4K1N1 w - - 0 1\n7k/8/8/3pP3/4K3/8/8/8 w - d6 0 1\n'
fixture=out/'fixtures.fen';fixture.write_text(fixtures);receipt['fixture_sha256']=sha(fixture);receipt['oracle_sha256']=sha(tests/'evasion_prefilter_oracle.cpp')
snapshot(CANDIDATE);original=(root/'src/board.cpp').read_text()
unitflags=['-std=c++20','-O1','-g','-DFORGE_NNUE_HIDDEN=256','-DFORGE_SPD_SLIDER_PEXT=0','-DFORGE_SPD_NO_ZERO_MOVELISTS=2','-Iinclude','-pthread']
for king in (0,1):
 for enabled in (0,1):
  exe=out/f'unit-k{king}-e{enabled}'
  r=run(['g++-14',*unitflags,'-fsanitize=address,undefined','-fno-omit-frame-pointer',f'-DFORGE_SPD_KING_LINES={king}',f'-DFORGE_SPD_CHECK_EVASION_PREFILTER={enabled}',tests/'evasion_prefilter_oracle.cpp',root/'src/board.cpp',root/'src/bitboard.cpp','-o',exe],cwd=root);assert r.returncode==0
  r=run([exe,fixture],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'});receipt['sanitizers'].append(dict(king_lines=king,enabled=enabled,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));save();assert r.returncode==0
  if len(receipt['sanitizers'])>1:assert r.stdout==receipt['sanitizers'][0]['stdout']
mutations={
 'no_checker_capture':('const Bitboard evasions = checkers_ | attacks::between','const Bitboard evasions = attacks::between'),
 'no_interposition':('checkers_ | attacks::between(king_square(us), lsb(checkers_))','checkers_'),
 'no_ep_bypass':('checkers_ != 0 && (move.flags & EnPassant) == 0U && piece_type(moving) != King','checkers_ != 0 && piece_type(moving) != King'),
 'accept_survivor':('if ((evasions & square_bb(move.to)) == 0) return false;','if ((evasions & square_bb(move.to)) == 0) return false;\n        return true;'),
}
for name,(old,new) in mutations.items():
 assert original.count(old)==2,(name,original.count(old));(root/'src/board.cpp').write_text(original.replace(old,new));exe=out/name
 r=run(['g++-14',*unitflags,'-DFORGE_SPD_CHECK_EVASION_PREFILTER=1',tests/'evasion_prefilter_oracle.cpp',root/'src/board.cpp',root/'src/bitboard.cpp','-o',exe],cwd=root);assert r.returncode==0
 r=run([exe,fixture]);receipt['mutations'].append(dict(name=name,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));save();assert r.returncode!=0
(root/'src/board.cpp').write_text(original)
# Preserve bounded disassembly for subsequent static instruction review.
r=run(['objdump','-d','-C',out/'on']);assert r.returncode==0
match=re.search(r'^([0-9a-f]+ <forge::Board::is_legal\(forge::Move const&\) const>:\n.*?)(?=\n[0-9a-f]+ <)',r.stdout,re.M|re.S);assert match
(tests/'evasion_prefilter_codegen.txt').write_text(match.group(1))
receipt['passed']=True;save();print('ALL EVASION PREFILTER GATES PASSED',flush=True)
