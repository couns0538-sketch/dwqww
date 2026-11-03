"""Read-only standard-FEN admission cases against the exact lock."""
import json
from pathlib import Path
import subprocess
import sys

HERE=Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
sys.path.insert(0,str(HERE))
from filter_positions import low_priority, sha256
from records import record
from native_forge_smoke import ENGINE, LOCK
from resource_policy import storage_guard

low_priority()
root=Path(__file__).parent/'standard_fen_probe'
storage_guard(root,allowance=1024*1024)
root.mkdir()
assert sha256(ENGINE)==LOCK
castle='r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1'
plain='8/8/8/8/8/6k1/8/K7 w - - 0 1'
cases={'castle':castle,'shredder':castle.replace('KQkq','HAha'),
       'duplicate_rights':castle.replace('KQkq','KKQkq'),
       'promoted_marker':'8/8/8/8/8/6k1/8/KR~6 w - - 0 1',
       'underscored_clock':plain[:-1]+'1_0',
       'overflow_clock':plain[:-1]+str(2**63),
       'tab':plain.replace(' w ','\tw ')}
observed={}
for name,fen in cases.items():
    try:
        record(fen,20,'cp',1,'fixture',1,'selfplay')
        accepted=True
    except ValueError:
        accepted=False
    request='\n'.join(['uci','setoption name Threads value 1','setoption name Hash value 16',
        'setoption name OwnBook value false','isready','position startpos',
        'position fen '+fen,'go perft 1','quit'])+'\n'
    (root/(name+'.stdin.txt')).write_text(request,encoding='utf-8')
    reply=subprocess.run([str(ENGINE)],input=request.encode('utf-8'),capture_output=True,
        cwd=root,timeout=15,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    (root/(name+'.stdout.log')).write_bytes(reply.stdout)
    (root/(name+'.stderr.log')).write_bytes(reply.stderr)
    lines=reply.stdout.decode('utf-8',errors='replace').splitlines()
    observed[name]={'admitted':accepted,'returncode':reply.returncode,'fen':fen,
                    'relevant':[line for line in lines if 'invalid FEN' in line or line.startswith('nodes ')]}
assert sha256(ENGINE)==LOCK
(root/'report.json').write_text(json.dumps(observed,indent=2),encoding='utf-8')
print(json.dumps(observed))
