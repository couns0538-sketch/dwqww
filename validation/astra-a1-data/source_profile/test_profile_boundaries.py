#!/usr/bin/env python3
"""Synthetic scalar-boundary regression for the read-only profiling script.
IDEA_SOURCE: declared inclusive bin boundaries; fixtures do not measure real data.
"""
import json
from pathlib import Path
import struct
import subprocess
import sys

root=Path(__file__).resolve().parent
repo=root.parents[2]
sys.path.insert(0,str(repo/'tools/data'))
from forge_pos import fen_record

fixture=root/'boundary_fixture';fixture.mkdir(exist_ok=False)
scores=[-1000,-999,-500,-499,-200,-199,-100,-99,-1,0,1,99,100,199,200,499,500,999,1000]
clocks=[0,9,10,29,30,49,50,69,70,89,90,99,100,101,0,0,0,0,0]
base='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
rows=[fen_record(base,score,0.5) for score in scores]
(fixture/'input.pos').write_bytes(struct.pack('<4sIQ',b'FPOS',1,len(rows))+b''.join(x.board for x in rows)+struct.pack('<'+'h'*len(rows),*scores)+bytes(x.meta for x in rows))
(fixture/'input.txt').write_text(''.join(f'{base.replace(" - 0 1",f" - {clock} 1")} | {score} | 0.5\n' for score,clock in zip(scores,clocks)))
argv=[sys.executable,'-B',str(root/'profile_source.py'),'--pos',str(fixture/'input.pos'),
      '--sidecar',str(fixture/'input.txt'),'--expected-rows',str(len(rows)),'--output',str(fixture/'result.json')]
p=subprocess.run(argv,capture_output=True)
(fixture/'stdout.txt').write_bytes(p.stdout);(fixture/'stderr.txt').write_bytes(p.stderr)
(fixture/'command.json').write_text(json.dumps({'argv':argv,'returncode':p.returncode},indent=2)+'\n')
if p.returncode:raise SystemExit(p.returncode)
r=json.loads((fixture/'result.json').read_text())
expected=[1,2,2,2,2,1,2,2,2,2,1]
observed=[x['count'] for x in r['source_score_stm_cp'].values()]
if observed!=expected:raise ValueError(('score boundaries',observed,expected))
if [x['count'] for x in r['halfmove_clock'].values()] != [7,2,2,2,2,2,2]:raise ValueError('clock boundaries')
print('PASS: exact signed cp and halfmove inclusive boundaries; synthetic 19-row fixture retained')
