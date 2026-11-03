"""Bounded final-review comparison of Python/Forge material admission."""
import json
from pathlib import Path
import re
import subprocess
import sys
import chess

HERE=Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
sys.path.insert(0,str(HERE))
from filter_positions import low_priority, sha256
from records import board_from_fen
from native_forge_smoke import ENGINE, LOCK
from resource_policy import storage_guard

low_priority()
root=Path(__file__).parent/'material_admission_fixed'
storage_guard(root,allowance=2_000_000)
root.mkdir()
pins={str(HERE/'records.py'):sha256(HERE/'records.py'),str(ENGINE):sha256(ENGINE)}
assert pins[str(ENGINE)]==LOCK
sys.path.insert(0,str(HERE/'tests'))
from test_forge_material_admission import CASES
cases={}
for index,(bad,good) in enumerate(CASES):
    for name,fen in [('bad',bad),('good',good)]:
        cases[str(index)+'_'+name]=fen
        cases[str(index)+'_'+name+'_mirror']=chess.Board(fen).mirror().fen(en_passant='fen')
report={}
for name,fen in cases.items():
    try:
        board=board_from_fen(fen)
        admitted=True
        expected=board.legal_moves.count()
    except ValueError:
        admitted=False
        expected=None
    request='\n'.join(['uci','setoption name Threads value 1','setoption name Hash value 16',
        'setoption name OwnBook value false','isready','position startpos',
        'position fen '+fen,'go perft 1','quit'])+'\n'
    (root/(name+'.stdin.txt')).write_text(request,encoding='utf-8')
    reply=subprocess.run([str(ENGINE)],input=request.encode('ascii'),capture_output=True,
        cwd=root,timeout=15,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    (root/(name+'.stdout.log')).write_bytes(reply.stdout)
    (root/(name+'.stderr.log')).write_bytes(reply.stderr)
    text=reply.stdout.decode('utf-8',errors='replace')
    report[name]=dict(fen=fen,python_admitted=admitted,expected=expected,
         actual=[int(n) for n in re.findall(r'^nodes (\d+)\s*$',text,re.M)],
         rejected='info string invalid FEN:' in text,returncode=reply.returncode)
assert all(sha256(path)==digest for path,digest in pins.items())
(root/'report.json').write_text(json.dumps(dict(source_files=pins,cases=report),indent=2),encoding='utf-8')
print(json.dumps(report))

if not all(item['returncode']==0 and item['python_admitted']==(not item['rejected'])
           and (not item['python_admitted'] or item['actual']==[item['expected']])
           for item in report.values()):
    raise ValueError('Python/Forge material boundary mismatch')
(root/'validation.json').write_text(json.dumps(dict(status='PASS',cases=len(report),
    source_files=pins,strength='UNPROVEN'),indent=2),encoding='utf-8')
print('PASS: all 20 material boundaries agree with the exact Forge lock')