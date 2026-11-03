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
root=Path(__file__).parent/'material_admission_probe'
storage_guard(root,allowance=2_000_000)
root.mkdir()
pins={str(HERE/'records.py'):sha256(HERE/'records.py'),str(ENGINE):sha256(ENGINE)}
assert pins[str(ENGINE)]==LOCK
cases={}
for piece in ('Q','R','B','N'):
    for pawns in ('PPPPPPPP','PPPPP3'):
        fen='4k3/8/8/8/8/'+piece*3+'5/'+pawns+'/4K3 w - - 0 1'
        cases[piece+'_'+pawns]=fen
        cases[piece+'_'+pawns+'_mirror']=chess.Board(fen).mirror().fen(en_passant='fen')
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
