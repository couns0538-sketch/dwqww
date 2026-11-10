#!/usr/bin/env python3
"""Isolated source-only candidate validation; no timing/strength inference."""
import pathlib, subprocess as sp, hashlib, json, sys
repo=pathlib.Path(__file__).resolve().parents[2]
out=pathlib.Path(sys.argv[1]).resolve(); out.mkdir(parents=True,exist_ok=True)
ref='2da9593'; root=out/'source'; root.mkdir(exist_ok=True)
p=sp.Popen(['git','archive',ref,'--','forge-combo29/src','forge-combo29/include'],cwd=repo,stdout=sp.PIPE)
sp.run(['tar','-x','-C',str(root)],stdin=p.stdout,check=True); assert p.wait()==0
src=root/'forge-combo29'; tests=repo/'forge-combo29/tests'
flags='-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Iinclude'.split()
records=[]
def run(cmd,**kw):
    records.append([str(x) for x in cmd]); sp.run(cmd,check=True,**kw)
for enabled in (0,1):
    run(['g++-14',*flags,f'-DFORGE_SPD_TT_REPLACE_CACHE={enabled}',*[str(x.relative_to(src)) for x in sorted((src/'src').glob('*.cpp'))],'-o',str(out/f'engine{enabled}')],cwd=src)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(out/'engine0')==sha(pathlib.Path('/workspace/shared/forge-build/baseline')),'default off identity mismatch'
for notls in (0,1):
    for enabled in (0,1):
        binary=out/f'contract{notls}{enabled}'
        run(['g++-14','-std=c++20','-O1','-g','-pthread','-fno-omit-frame-pointer','-fno-pie','-no-pie','-fsanitize=thread','-DFORGE_NNUE_HIDDEN=256','-DFORGE_SPD_SLIDER_PEXT=0','-DFORGE_SPD_NNUE_ZMM=0',f'-DFORGE_SPD_TT_NOTLS={notls}',f'-DFORGE_SPD_TT_REPLACE_CACHE={enabled}','-I'+str(src/'include'),str(tests/'tt_replace_cache_test.cpp'),*[str(src/'src'/f'{name}.cpp') for name in ['search','board','bitboard','eval','eval_params','nnue']],'-o',str(binary)])
        import os
        with (out/f'contract{notls}{enabled}.log').open('w') as log: run([str(binary)],stdout=log,stderr=sp.STDOUT,env={**os.environ,'TSAN_OPTIONS':'halt_on_error=1:exitcode=66'})
with (out/'pins.log').open('w') as log: run(['bash',str(repo/'forge-combo29/scripts/check_pins.sh'),str(out/'engine1')],cwd=out,stdout=log,stderr=sp.STDOUT)
run(['python3',str(tests/'equivalence_screen.py'),'/workspace/shared/forge-build/baseline',str(out/'engine1'),'--output',str(out/'equivalence.json')])
(out/'receipt.json').write_text(json.dumps({'ref':sp.check_output(['git','rev-parse',ref],cwd=repo,text=True).strip(),'test_hashes':{name:sha(tests/name) for name in ['tt_replace_cache_test.cpp','tt_contract_test.cpp','equivalence_screen.py','equivalence_positions.fen']},'commands':records,'hashes':{p.name:sha(p) for p in out.iterdir() if p.is_file() and (p.name.startswith('engine') or p.name.startswith('contract'))}},indent=2)+'\n')
print('PASS identity, 4 TSan contract/oracle variants, full pins, 256 comparisons')
