#!/usr/bin/env python3
"""Reproduce temporary prototype; never modifies repository production source."""
import pathlib,subprocess as sp,json,os
repo=pathlib.Path(__file__).resolve().parents[2];tests=repo/'forge-combo29/tests'
out=pathlib.Path('/workspace/shared/forge-build/tt-packed');source=out/'source'
source.mkdir(parents=True,exist_ok=True)
p=sp.Popen(['git','archive','2da9593','--','forge-combo29/src','forge-combo29/include'],cwd=repo,stdout=sp.PIPE)
sp.run(['tar','-x','-C',str(source)],stdin=p.stdout,check=True);assert p.wait()==0
src=source/'forge-combo29'
sp.run(['patch','-p1','-i',str(tests/'tt_replace_packed_prototype.patch')],cwd=src,check=True)
commands=json.loads((tests/'tt_replace_cache_receipt.json').read_text())['commands']
c=commands[1][:];c[-1]=str(out/'engine');sp.run(c,cwd=src,check=True)
for mode in (0,1):
    c=next(c[:] for c in commands if c[0]=='g++-14' and c[-1].endswith('contract'+str(mode)+'1'))
    c=[x.replace('/workspace/shared/forge-build/tt-replace-cache/source/',str(source)+'/') for x in c];c[-1]=str(out/f'contract{mode}')
    sp.run(c,check=True)
    with (out/f'contract{mode}.log').open('w') as f:sp.run([c[-1]],stdout=f,stderr=sp.STDOUT,check=True,env={**os.environ,'TSAN_OPTIONS':'halt_on_error=1:exitcode=66'})
sp.run(['g++-14','-O2','-fsanitize=undefined','-fno-sanitize-recover=all',str(tests/'tt_replace_packed_oracle.cpp'),'-o',str(out/'oracle')],check=True)
sp.run([str(out/'oracle')],check=True)
