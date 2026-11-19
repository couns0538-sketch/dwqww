"""Exercise the Job 17 command construction and hard-node readback with local in-memory UCI replies."""
import hashlib
import importlib.util
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

here=Path(__file__).resolve().parent
driver=here.parent/'j17match/selfplay.py'
spec=importlib.util.spec_from_file_location('selfplay_job17',driver)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fen='r2qkb1r/pp3ppp/2n2n2/1B6/3Pp1b1/5N2/PPP2PPP/RNBQ1RK1 w kq - 0 8'
proc=SimpleNamespace(stdin=StringIO(),pid=321,stdout=iter([
    'info depth 6 nodes 75 score cp 2\n','info depth 7 nodes 188 score cp 5\n','bestmove g1h1\n',
    'bestmove c6b4\n','info depth 1 nodes 0\n','bestmove f3g1\n']))
assert module.search(proc,fen,[],50000)==('g1h1',188)
assert module.search(proc,fen,['g1h1'],50000)==('c6b4',None)
assert module.search(proc,fen,['g1h1','c6b4'],250000)==('f3g1',0)
expected=['position fen '+fen,'go nodes 50000','position fen '+fen+' moves g1h1','go nodes 50000',
    'position fen '+fen+' moves g1h1 c6b4','go nodes 250000']
assert proc.stdin.getvalue().splitlines()==expected
for lines,message in [(['info depth 1 nodes 2\n','info string no counter here\n','bestmove g1h1\n'],'missing'),
                      (['unknown option request\n','bestmove g1h1\n'],'refusal'),
                      (['invalid value error\n','bestmove g1h1\n'],'refusal')]:
    proc.stdout=iter(lines)
    try:module.search(proc,fen,[],50000)
    except (RuntimeError,ValueError):pass
    else:raise RuntimeError('expected failure: '+message)
print('Selfplay driver SHA-256 '+hashlib.sha256(driver.read_bytes()).hexdigest())
print('Synthetic UCI replies passed: chose 188 from the last info record after earlier 75; returned NA for the next search with no info; retained numeric zero for a later info line. A final info line with no nodes, an unknown option and an invalid value all interrupted the search.')
print('Captured commands used an untouched initial FEN, omitted moves at the first ply, replayed the full prefix thereafter, and requested exactly go nodes 50000 or go nodes 250000. This test launched no engine.')
