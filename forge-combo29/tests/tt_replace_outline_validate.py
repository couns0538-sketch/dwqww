#!/usr/bin/env python3
"""Reproduce temporary prototype; never modifies repository production source."""
import pathlib,subprocess as sp,json,os
repo=pathlib.Path(__file__).resolve().parents[2];tests=repo/'forge-combo29/tests'
out=pathlib.Path('/workspace/shared/forge-build/tt-outline');source=out/'source'
source.mkdir(parents=True,exist_ok=True)
p=sp.Popen(['git','archive','2da9593','--','forge-combo29/src','forge-combo29/include'],cwd=repo,stdout=sp.PIPE)
sp.run(['tar','-x','-C',str(source)],stdin=p.stdout,check=True);assert p.wait()==0
src=source/'forge-combo29'
sp.run(['patch','-p1','-i',str(tests/'tt_replace_outline_prototype.patch')],cwd=src,check=True)
commands=json.loads((tests/'tt_replace_cache_receipt.json').read_text())['commands']
c=commands[1][:];c[-1]=str(out/'engine');sp.run(c,cwd=src,check=True)
