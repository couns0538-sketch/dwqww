"""Reconcile runner and PGN results before validating all SAN moves and board endings."""
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import csv,hashlib,re,shlex,sys
from audit import run,read,dump_tsv,FINISHED,STARTED
from stats_seed import evaluate
from live import verify as verify_traffic
HERE=Path(__file__).resolve().parent
WORK=HERE.parent
try:import chess
except ImportError:
    sys.path.insert(0,str(WORK/'j10fens/vendor'))
    import chess
LIMIT='2026-11-19T02:22:00Z'
CASES={'C21':(200,7391,10000,20000),'B1':(1200,7392,20000,20000),'B2':(1200,7393,2000,2000)}
RAW=WORK/'j21match/results'
def tsv(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def key(fen):return tuple(fen.split()[:4])
def termcheck(b,why,result,n):
    if why in ('White mates','Black mates'):
        assert b.is_checkmate() and b.result()==result,(why,b.fen(),result)
    elif why=='Draw by stalemate':assert b.is_stalemate(),b.fen()
    elif why=='Draw by insufficient mating material':assert b.is_insufficient_material(),b.fen()
    elif why=='Draw by 3-fold repetition':assert b.is_repetition(3),b.fen()
    elif why=='Draw by fifty moves rule':assert b.is_fifty_moves(),b.fen()
    elif why=='Draw by adjudication':assert n==600 and result=='1/2-1/2',(b.fen(),n)
    elif 'loses on time' in why:pass
    else:raise ValueError(('unrecognized ending',why))
def legal(stage,games,details,out):
    schedule=tsv(WORK/'j21book'/f'{stage}-lines.tsv')
    id_to_line={int(r['round']):int(r['original_epd_line']) for r in schedule}
    lines=set(id_to_line.values())
    with (WORK/'j8gate/UHO_Lichess_4852_v1.epd').open() as f:
        physical={i:l.strip() for i,l in enumerate(f,1) if i in lines}
    actual={};ply_sum=0;verified=Counter();replay=[]
    for item in details:actual[(int(item['round']),item['white'],item['black'])]=item
    unique=set()
    for g in games:
        t=g['tags'];rnd=int(t['Round']);rr=actual[(rnd,t['White'],t['Black'])]
        src=physical[id_to_line[rnd]]
        assert key(src)==key(g['fen']),(stage,rnd,src,g['fen'])
        unique.add(key(g['fen']))
        b=chess.Board(g['fen'])
        for ply,san in enumerate(g['moves'],1):
            try:b.push(b.parse_san(san))
            except ValueError as exc:raise ValueError((stage,rnd,t['White'],ply,san,b.fen())) from exc
        n=len(g['moves']);ply_sum+=n
        assert n<=600,(stage,rnd,n)
        termcheck(b,rr['runner_reason'],rr['result'],n);verified[rr['runner_reason']]+=1
        replay.append((rr['game_id'],rnd,id_to_line[rnd],n,b.fen(),rr['runner_reason']))
    dump_tsv(out/'replay.tsv',('game_id','round','original_book_line','plies','final_fen','verified_reason'),sorted(replay,key=lambda q:int(q[0])))
    (out/'legality.txt').write_text(f'{stage}: replayed all {len(games)} scored PGNs ({ply_sum} legal SAN moves) from their FEN tags with python-chess {chess.__version__}. Verified the board state for every mate/rule ending; maxmove adjudications require 600 post-opening plies and draws. Fastchess increments its maximum-move tracker once per played ply and checks >= 2 * maxmoves. Each of {len(unique)} observed round position keys (placement, side, castling, en passant) matched the recorded original UHO source line.\n'+'\n'.join(f'{k}: {v}' for k,v in sorted(verified.items()))+'\n')
def config(stage,meta,outtext,out):
    planned,seed,na,nb=CASES[stage]
    alltext=meta+'\n'+outtext
    assert not re.search(r'unknown option|invalid value',alltext,re.I),stage
    cmd=next(l.removeprefix('command ') for l in meta.splitlines() if l.startswith('command '))
    words=shlex.split(cmd)
    for flag,nextval in [('-maxmoves','300'),('-concurrency','4'),('-srand',str(seed)),('-rounds',str(planned//2)),('-games','2')]:
        assert words[words.index(flag)+1]==nextval,(stage,flag)
    assert '-repeat' in words and '-resign' not in words and '-draw' not in words
    indexes=[i for i,w in enumerate(words) if w=='-engine']
    each=words.index('-each');segments=(words[indexes[0]+1:indexes[1]],words[indexes[1]+1:each])
    common=words[each+1:];pc= (WORK/'j7base/pc20.txt').read_text().splitlines()
    expected={s[len('setoption name '):].rsplit(' value ',1)[0]:s.rsplit(' value ',1)[1] for s in pc}
    lines=[]
    for lab,role,limit in zip(('A','B'),segments,(na,nb)):
        opt={k:v for k,v in [w[len('option.'):].split('=',1) for w in common+role if w.startswith('option.')]}
        nv=lab=='A' and stage!='C21'
        assert all(opt.get(k)==v for k,v in expected.items())
        assert opt['NNUEArch']=='true' and Path(opt['NNUEArchFile']).name=='net768.nnue'
        assert opt['NullMateGuard']==('2' if nv else '0') and opt.get('NullThreatVerify','false')==str(nv).lower(),(stage,lab,opt)
        assert [w for w in common+role if w.startswith('nodes=')]==['nodes='+str(limit)]
        assert 'name='+stage+'-'+lab in role
        sec=re.search(r'^'+lab+r' preflight output\n(.*?)^'+lab+r' preflight PASS',meta,re.M|re.S)
        assert sec,(stage,lab)
        for mode in ('loaded','active'):
            assert re.search(r'^info string NNUE v3 '+mode+r': .*checksum 30ab43b4ba5db5f3\b',sec[1],re.M),(stage,lab,mode)
        assert 'readyok' in sec[1]
        lines.append(f'{stage}-{lab}: limit {limit}, NullMateGuard {opt["NullMateGuard"]}, NullThreatVerify {str(nv).lower()}, PC20, Threads 1, Hash 16, net768 loaded+active checksum 30ab43b4ba5db5f3, readyok.')
    lines.append(f'Seed {seed}, {planned//2} opening pairs planned, repeat, concurrency 4, maxmoves 300, no score adjudication, no refusal in meta or runner stdout.')
    (out/'settings-check.txt').write_text('\n'.join(lines)+'\n')
def runstage(stage):
    want,*_=CASES[stage];out=HERE/stage
    args=SimpleNamespace(pgn=RAW/(stage+'.pgn'),match_out=RAW/(stage+'.out'),meta=RAW/(stage+'.meta'),deadline=LIMIT,want=want,engine_a=stage+'-A',out=out)
    run(args)
    summary=(out/'pgn-audit.txt').read_text()
    status=re.search(r'^status (\w+)$',summary,re.M)[1]
    config(stage,args.meta.read_text(),args.match_out.read_text(),out)
    games,partial=read(args.pgn,status!='complete')
    legal(stage,games,tsv(out/'games.tsv'),out)
    verify_traffic(stage,out)
    pairs=tsv(out/'pairs.tsv');obs=[];wld=Counter()
    for r in pairs:
        marks=[r['A_result_first'],r['A_result_second']]
        n=sum(dict(W=1,L=0,D=.5)[m] for m in marks)
        assert n==float(r['A_points']);obs.append(n/2);wld.update(marks)
    penta=[obs.count(i/4) for i in range(5)]
    if obs:e,lo,hi=evaluate(obs)
    else:e=lo=hi=None
    ends=dict(re.findall(r'(\w+)=(\d+)',next(l for l in summary.splitlines() if l.startswith('endings '))))
    if stage=='C21':verdict='PASS' if status=='complete' and hi is not None and hi<0 else 'STOP'
    elif stage=='B1':verdict='BUNDLE BETTER' if lo is not None and lo>0 else 'BUNDLE WORSE' if hi is not None and hi<0 else 'LEVEL' if obs else 'UNAVAILABLE'
    else:verdict='description only'
    header='match status scored_games complete_pairs A_wins A_losses A_draws penta0 penta05 penta1 penta15 penta2 elo lower95 upper95 mate draw_rule limit_300 time_A_loss time_B_loss other reading'.split()
    row=[stage,status,len(obs)*2,len(obs),wld['W'],wld['L'],wld['D'],*penta,*[f'{n:+.8f}' if n is not None else '' for n in (e,lo,hi)],*[ends[k] for k in ('mate','draw_rule','limit_300','time_A_loss','time_B_loss','other')],verdict]
    dump_tsv(out/'score.tsv',header,[row])
    (out/'reading.txt').write_text(f'{stage} {status if status=="complete" else "cut"}: {verdict} on {2*len(obs)} scored games, {len(obs)} complete pairs.\n')
    sig=out/'verified.tmp';sig.write_text(f'{stage} {status}, {len(obs)} reconciled and replayed pairs. {verdict}.\n');sig.replace(out/'verified.txt')
if __name__=='__main__':runstage(sys.argv[1])
