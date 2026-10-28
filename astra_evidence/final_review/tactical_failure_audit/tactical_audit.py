from pathlib import Path
import sys,subprocess,threading,queue,json,hashlib
sys.path.insert(0,'/workspace/.cloud-setup/venv/lib/python3.12/site-packages')
import chess
p=Path('/tmp/astra-review-smp')
exe='/tmp/forge-astra-build-j5fix-20261029/forge'
fen='8/k1P5/2K5/8/8/8/8/8 w - - 0 1'
positions=[('white',chess.Board(fen)),('black',chess.Board(fen).mirror())]
jobs=[]
for label,b in positions:
    for limit in ['', ' searchmoves c7c8q' if label=='white' else ' searchmoves c2c1q', ' searchmoves c7c8r' if label=='white' else ' searchmoves c2c1r']:
        jobs.append((label+('free' if not limit else limit.split()[-1]),b.fen(),1,limit))
jobs.append(('wac001','2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1',12,''))
results=[]
for label,fen,depth,limit in jobs:
    q=queue.Queue();out=[];err=[];sent=[]
    child=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    def reader(stream,items,enqueue):
        for raw in iter(stream.readline,b''):
            items.append(raw)
            if enqueue:q.put(raw.decode().strip())
        if enqueue:q.put(None)
    threads=[threading.Thread(target=reader,args=(child.stdout,out,True)),threading.Thread(target=reader,args=(child.stderr,err,False))]
    for t in threads:t.start()
    def send(line):
        sent.append((line+'\n').encode());child.stdin.write(sent[-1]);child.stdin.flush()
    def wait(prefix):
        while True:
            line=q.get(timeout=30)
            if line is None:raise AssertionError('EOF')
            if line.startswith(prefix):return line
    send('uci');wait('uciok')
    send('setoption name OwnBook value false');send('setoption name Hash value 1');send('setoption name Threads value 1');send('isready');wait('readyok')
    send('position fen '+fen);send('go depth '+str(depth)+limit);best=wait('bestmove ')
    send('quit');assert child.wait(timeout=5)==0
    for t in threads:t.join(timeout=1)
    for ext,data in [('stdin',sent),('stdout',out),('stderr',err)]:(p/('tactical_'+label+'.'+ext)).write_bytes(b''.join(data))
    info=[x.decode().strip() for x in out if x.startswith(b'info depth ')]
    b=chess.Board(fen);move=chess.Move.from_uci(best.split()[1]);assert move in b.legal_moves
    b.push(move)
    results.append({'label':label,'fen':fen,'depth':depth,'root_restriction':limit,'bestmove':move.uci(),'last_info':info[-1] if info else None,'move_legal':True,'after_move_stalemate':b.is_stalemate(),'after_move_checkmate':b.is_checkmate()})
(p/'tactical_audit.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
