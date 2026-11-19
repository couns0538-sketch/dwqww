"""Audit a whole-game UCI record comparison against the book and driver receipts."""
import argparse
import csv
import hashlib
from itertools import islice, zip_longest
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
try:
    import chess
except ImportError:
    sys.path.insert(0, str(WORK / 'j10fens/vendor'))
    import chess

ARMS = {
    'K16': ('K16-1', 'K16-2', 2201, 2220),
    'C16': ('K16-1', 'C16', 2201, 2220),
    'S1': ('S1-r15d', 'S1-kF', 2201, 3200),
    'S2': ('S2-r15d', 'S2-kF', 3201, 3400),
}
RECORD = re.compile(rb'([1-9][0-9]*) ([1-9][0-9]*) ([a-h][1-8][a-h][1-8][nbrq]?) (0|[1-9][0-9]*)\n')
REPLAY = {}
def rows(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))
def table(path, names, data):
    with path.open('w', newline='') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerow(names)
        writer.writerows(data)
def load_book(path, start, end):
    with path.open() as f:
        return dict(enumerate((line.strip() for line in islice(f,start-1,end)),start))
def replay(fen, moves):
    key = (fen, tuple(moves))
    if key not in REPLAY:
        board = chess.Board(fen)
        for ply, move in enumerate(moves,1):
            assert not board.is_game_over(claim_draw=True), (fen, ply, 'record after terminal position')
            board.push(board.parse_uci(move))
        outcome = board.outcome(claim_draw=True)
        assert outcome or len(moves) == 300, (fen, len(moves), 'reported start/end are not a full game')
        assert len(moves) <= 300
        REPLAY[key] = (outcome.result(),outcome.termination.name) if outcome else ('*','PLY_LIMIT')
    return REPLAY[key]
def read_arm(path, first, last, book):
    terminal = re.findall(r'^status (COMPLETE|INCOMPLETE|FAILED|STOPPED)\b', (path/'run.log').read_text(), re.M)
    assert len(terminal)==1,(path,terminal)
    receipt = rows(path/'games.tsv')
    raw = (path/'records.txt').read_bytes()
    lines = raw.splitlines(keepends=True)
    digest = hashlib.sha256(raw).hexdigest()
    current = {}
    for number,line in enumerate(lines,1):
        m = RECORD.fullmatch(line)
        assert m,(path,number,line)
        gid,ply,move,nodes=m.groups()
        gid,ply,nodes = int(gid),int(ply),int(nodes)
        assert first<=gid<=last and nodes>0, (path,number,gid,ply,nodes)
        items=current.setdefault(gid,[])
        assert ply==len(items)+1,(path,number,gid,ply)
        items.append((move.decode('ascii'),nodes,line))
    assert len(receipt) <= last-first+1
    assert [int(r['book_line']) for r in receipt]==list(range(first,first+len(receipt)))
    assert set(current).issubset(range(first,first+len(receipt)))
    if terminal[0]=='COMPLETE':
        assert len(receipt)==last-first+1,(path,len(receipt),first,last)
    else:
        assert len(receipt)<last-first+1, (path,terminal,len(receipt))
    pointer = 0
    game_sums = []
    for r in receipt:
        gid = int(r['book_line'])
        items = current.setdefault(gid,[])
        game_bytes = b''.join(x[2] for x in items)
        assert raw[pointer:pointer+len(game_bytes)]==game_bytes,(path,gid,'noncontiguous rows')
        pointer+=len(game_bytes)
        assert int(r['record_bytes'])==pointer,(path,gid,'receipt byte offset')
        assert len(items)==int(r['plies']), (path,gid,'plies')
        node_sum = sum(x[1] for x in items)
        assert node_sum==int(r['nodes']), (path,gid,'node sum')
        outcome,term = replay(book[gid], [x[0] for x in items])
        assert (outcome,term)==(r['result'],r['termination']), (path,gid,outcome,term,r)
        game_sums.append((path.name,gid,len(items),node_sum,len(game_bytes),
            hashlib.sha256(game_bytes).hexdigest(),outcome,term))
    assert pointer==len(raw), (path,'extra records beyond durable game receipts',pointer,len(raw))
    return dict(name=path.name, status=terminal[0], games=current, sums=game_sums,
        raw=raw, records=len(lines), nodes=sum(g[3] for g in game_sums), digest=digest)
def compare(a,b,book,out,stage,first,last):
    left,right = a['games'],b['games']
    common=sorted(left.keys() & right.keys())
    left_only=sorted(left.keys() - right.keys()); right_only=sorted(right.keys() - left.keys())
    diff=[];first_diff=None;startline=1
    for gid in common:
        left_rows,right_rows = left[gid],right[gid]
        first_ply=None; unequal_moves=unequal_nodes=extra=0
        for ply,(u,v) in enumerate(zip_longest(left_rows,right_rows),1):
            if u==v:
                continue
            if first_ply is None:
                first_ply=ply
            if u is None or v is None:extra+=1
            else:
                unequal_moves+=int(u[0]!=v[0]); unequal_nodes+=int(u[1]!=v[1])
            if first_diff is None:
                first_diff=(gid,ply,startline+ply-1,u,v,left_rows[:ply-1],right_rows[:ply-1])
        if first_ply is not None:diff.append((gid,first_ply,len(left_rows),len(right_rows),unequal_moves,unequal_nodes,extra))
        startline+=len(left_rows)
    whole=a['status']==b['status']=='COMPLETE'
    equal=a['raw']==b['raw']
    cmpcode=subprocess.run(['cmp','-s',str(args.results/a['name']/'records.txt'),str(args.results/b['name']/'records.txt')]).returncode
    assert cmpcode==int(not equal),(cmpcode,equal)
    if whole:assert equal==(not diff)
    table(out/'differences.tsv',('book_line','first_differing_ply','left_plies','right_plies','unequal_moves_on_shared_plies','unequal_nodes_on_shared_plies','unmatched_plies'),diff)
    detail=['No differing record in games completed by both arms.']
    if first_diff:
        gid,ply,line,u,v,before_a,before_b=first_diff
        board=chess.Board(book[gid])
        for m in before_a:board.push_uci(m[0])
        detail=[f'Book line {gid}, ply {ply}, record line {line} in left file.', 'Opening FEN '+book[gid], 'FEN before differing ply '+board.fen(en_passant='fen')]
        for arm,rec,before in [(a,u,before_a),(b,v,before_b)]:
            detail.append(arm['name']+' record '+(rec[2].decode('ascii').rstrip('\n') if rec else '(missing)'))
            detail.append(arm['name']+' preceding UCI moves '+(' '.join(r[0] for r in before) or '(none)'))
    (out/'first-difference.txt').write_text('\n'.join(detail)+'\n')
    gameword='IDENTICAL' if equal else 'DIFFERS'
    if not whole:
        gameword='INCOMPLETE; '+('DIFFERS on common completed games' if diff else 'no differences in common completed games')
    report=[f'{stage} {gameword}', f'Book lines {first}–{last}. Requested games per arm {last-first+1}.',
        'Four ASCII fields per line, canonical decimal book line, ply and nodes, legal UCI move, LF terminator and no header.',
        'Replayed each distinct opening and complete UCI move sequence with python-chess '+chess.__version__+'. No move follows a claimable game end. Last position is terminal under claim_draw=True or reaches 300 plies.',
        'Game ID order and contiguous one-based ply, per-game plies, termination, result, cumulative byte offset and node sum agree with the driver receipts.',
        f'cmp -s exit {cmpcode}. Record files byte-equal {equal}. Common completed games {len(common)}, differing games {len(diff)}.',
        f'Games with a differing move on shared plies {sum(d[4]>0 for d in diff)}; games with a differing node count on shared plies {sum(d[5]>0 for d in diff)}; games with unequal ply counts {sum(d[6]>0 for d in diff)}.',
        f'Games completed only in {a["name"]}: {left_only}. Games completed only in {b["name"]}: {right_only}.']
    for arm in (a,b):
        report.append(f'{arm["name"]} {arm["status"]}, {len(arm["games"])} games, {arm["records"]} records, {arm["nodes"]} nodes, {len(arm["raw"])} bytes, SHA-256 {arm["digest"]}.')
    report.extend(detail)
    (out/'summary.txt').write_text('\n'.join(report)+'\n')
    table(out/'arms.tsv',('arm','status','games','records','nodes','bytes','sha256'),[(r['name'],r['status'],len(r['games']),r['records'],r['nodes'],len(r['raw']),r['digest']) for r in (a,b)])
    table(out/'games.tsv',('arm','book_line','plies','nodes','bytes','sha256','result','termination'),a['sums']+b['sums'])
    print('\n'.join(report),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=ARMS)
    p.add_argument('--book',type=Path,default=WORK/'j8gate/UHO_Lichess_4852_v1.epd')
    p.add_argument('--results',type=Path,default=WORK/'j16match/results')
    p.add_argument('--output',type=Path,default=HERE)
    args=p.parse_args()
    a,b,lo,hi=ARMS[args.stage]
    book=load_book(args.book,lo,hi)
    out=args.output/args.stage
    out.mkdir(parents=True,exist_ok=True)
    compare(read_arm(args.results/a,lo,hi,book),read_arm(args.results/b,lo,hi,book),book,out,args.stage,lo,hi)
