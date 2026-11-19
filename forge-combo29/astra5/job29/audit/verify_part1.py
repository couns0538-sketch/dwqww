"""Independently recount all Part 1 fields and verify literal UCI, FEN and moves."""
from common29 import *
import sys
fens=Path(sys.argv[2]).read_text().splitlines()[:200];ans=[]
known={1000:(300918,1166,2,0,'9236b769d992254f'),2000:(590929,1393,0,0,'377dc0ab7edb4b30'),4000:(1140737,1613,0,0,'eb6b6afce426e7ea')}
for N in (500,1000,2000,4000,8000):
    d=Path(sys.argv[1])/str(N);raw=(d/'wire.txt').read_text().splitlines()
    check(not any(re.search('unknown option|invalid value|ERROR',x,re.I) for x in raw),'diagnostic')
    want=['uci']+['setoption name '+k+' value '+v for k,v in (x.rsplit(' ',1) for x in OPTIONS)]
    for fen in fens:want.extend(['ucinewgame','isready','position fen '+fen,'go softnodes '+str(N)])
    want+=['quit'];check([x[2:] for x in raw if x.startswith('> ')]==want,(N,'go commands'))
    check(raw.count('< uciok')==1 and raw.count('< readyok')==200,(N,'readiness'))
    total=depthsum=caps=scoreless=last_info=0;rows=[];batch=None
    for line in raw:
        if line=='> go softnodes '+str(N):batch=[];continue
        if batch is None or not line.startswith('< '):continue
        text=line[2:];batch.append(text)
        if not text.startswith('bestmove '):continue
        infos=[data_info(x) for x in batch if x.startswith('info ')]
        final_n=[int(x.rsplit(' ',1)[1]) for x in batch if x.startswith('info string softnodes nodes ')]
        check(len(final_n)==1,(N,len(rows),'footer'));n=final_n[0]
        depth=next((x['depth'] for x in reversed(infos) if 'depth' in x),0)
        last_info+=next((x['nodes'] for x in reversed(infos) if 'depth' in x and 'nodes' in x),0)
        move=text.split()[1];i=len(rows)+1;board=chess.Board(fens[i-1]);check(board.parse_uci(move) in board.legal_moves,(N,i,move))
        total+=n;depthsum+=depth;caps+=n>=4*N;scoreless+=not any('score' in x for x in infos)
        rows.append(f'{i} {n} {move}\n');batch=None
    out=''.join(rows).encode();check(len(rows)==200 and out==(d/'rows.txt').read_bytes(),(N,'joined rows'))
    sig=sha(out)[:16];values=(total,depthsum,caps,scoreless,sig)
    if N in known:check(values==known[N],(N,values,known[N]))
    if N==1000:check(last_info==294764,'last info nodes')
    if N==2000:check(rows[:3]==['1 2474 f1e2\n','2 2039 f1c4\n','3 3174 e5d4\n'],'2000 prefix')
    ans.append((N,len(rows),*values,last_info));print(N,values,last_info)
write_table(Path(sys.argv[3]),['limit','searches','sum_n','sum_depth','hardcap','scoreless','sha16','sum_last_depth_info_nodes'],ans)
