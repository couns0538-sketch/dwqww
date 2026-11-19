"""Read-only checks on the job 17 match driver, its logs and saved records."""
import csv
import hashlib
import importlib.util
import io
from pathlib import Path
from itertools import islice
import re
import sys
sys.dont_write_bytecode = True
work = Path('/workspace/work')
job = work/'j17match'
spec = importlib.util.spec_from_file_location('driver_under_review', job/'selfplay.py')
drv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drv)

class Pipe:
    def __init__(self, reply):
        self.stdin = io.StringIO()
        self.stdout = io.StringIO(reply)
        self.pid = 1

def parser_checks():
    p = Pipe('info depth 1 nodes 8\ninfo depth 2 nodes 35\nbestmove a2a4\nbestmove a7a5\ninfo depth 1 nodes 0\nbestmove h2h4\n')
    assert drv.search(p, 'original-fen', [], 50000) == ('a2a4',35)
    assert drv.search(p, 'original-fen', ['a2a4'], 50000) == ('a7a5',None)
    assert drv.search(p, 'original-fen', ['a2a4','a7a5'], 250000) == ('h2h4',0)
    assert p.stdin.getvalue().splitlines() == ['position fen original-fen', 'go nodes 50000', 'position fen original-fen moves a2a4', 'go nodes 50000', 'position fen original-fen moves a2a4 a7a5', 'go nodes 250000']
    for bad in ['info depth 1 nodes 8\ninfo depth 2 score cp 5\nbestmove a2a4\n','info string unknown option\n','info string invalid value\n','info string ERROR\n']:
        try: drv.search(Pipe(bad), 'original-fen', [], 50000)
        except ValueError: continue
        raise AssertionError(bad)
    print('In-memory UCI stream checks passed: last of multiple info lines; no-info after previous search returns NA; numeric zero preserved; exact two commands for initial and noninitial moves; malformed final info or refusal stops.')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rows(p):
    with p.open() as f: return list(csv.DictReader(f,delimiter='\t'))

def examine(arm):
    name,first,last,cap,lmr = drv.ARMS[arm]
    expected = {'r15d':('9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',[1,2]),'kF':('c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb',[3,4])}[name]
    dest=job/'results'/arm
    canonical=dest/'records.txt'
    pc=(work/'j7base/pc20.txt').read_text().splitlines()
    pc[pc.index('setoption name LmrQuietBase value 93')]=f'setoption name LmrQuietBase value {lmr}'
    options=pc+['setoption name NNUEArchFile value /workspace/work/j7net/net768.nnue','setoption name NNUEArch value true']
    assert len(pc)==22 and 'setoption name OwnBook value false' in pc and 'setoption name Threads value 1' in pc and 'setoption name Hash value 16' in pc
    with drv.BOOK.open() as book:
        white_root={n:line.split()[1]=='w' for n,line in enumerate(islice(book,first-1,last),first)}
    all_pids=[]
    na_total=0
    node_sum=0
    record_count=0
    for slot,cpu in enumerate(expected[1],1):
        folder=dest/f'slot{slot}'
        log=(folder/'run.log').read_text()
        assert re.search(r'executable \S+ sha256 '+expected[0]+r'$',log,re.M)
        assert re.search(r'book \S+ sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a$',log,re.M)
        assert re.search(r'net \S+ sha256 c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7$',log,re.M)
        assert f'hard_node_limit {cap} claim_draw True max_plies 300' in log
        assert re.findall(r'^both (.*)$',log,re.M)==options
        pids=[]
        slot_games=rows(folder/'games.tsv')
        for role,prefix in [('P1_White','p1'),('P2_Black','p2')]:
            pid = re.search(rf'^{role} pid (\d+) child_cpu_affinity \[{cpu}\]$',log,re.M)[1]
            assert all(row[prefix+'_pid']==pid for row in slot_games)
            for label in ['loaded','active']:
                assert re.search(rf'^{role} info string NNUE v3 {label}: .*checksum 30ab43b4ba5db5f3 ',log,re.M)
            pids.append(pid)
        all_pids.extend(pids)
        starts = re.findall(r'^game_start (\d+) \S+ readyok_both (\d+) (\d+)$',log,re.M)
        assert [int(a) for a,_,_ in starts]==list(range(first+slot-1,last+1,2)), (arm,slot,starts[-3:])
        assert all([p1,p2]==pids for _,p1,p2 in starts)
        assert [int(r['book_line']) for r in slot_games]==[int(a) for a,_,_ in starts]
        for row in slot_games:
            line=int(row['book_line'])
            plies=int(row['plies'])
            white_plies=plies//2 + int((plies%2==1) and white_root[line])
            assert int(row['p1_search'])==white_plies
            assert int(row['p2_search'])==plies-white_plies
            assert plies<=300
        for row in rows(folder/'no-info.tsv'):
            white_to_move=white_root[int(row['book_line'])] == (int(row['ply'])%2==1)
            assert row['side']==('White' if white_to_move else 'Black')
            assert row['engine_pid']==pids[0 if white_to_move else 1]
    assert len(set(all_pids))==4
    ordered=rows(dest/'games.tsv')
    assert [int(r['book_line']) for r in ordered]==list(range(first,last+1))
    from collections import defaultdict
    per_book=defaultdict(list)
    for row in canonical.read_text().splitlines():
        l,p,m,n=row.split()
        per_book[int(l)].append((int(p),m,n))
        record_count+=1
        if n=='NA': na_total+=1
        else: node_sum+=int(n)
    assert [int(r['book_line']) for r in ordered]==list(per_book)
    assert all([ply for ply,_,_ in moves]==list(range(1,len(moves)+1)) for moves in per_book.values())
    assert record_count==sum(int(r['plies']) for r in ordered)
    assert na_total==len(rows(dest/'no-info.tsv'))==sum(int(r['na']) for r in ordered)
    assert node_sum==sum(int(r['nodes']) for r in ordered)
    summary=(dest/'run.log').read_text()
    for k,val in [('records',record_count),('na_records',na_total),('sum_nodes',node_sum),('records_sha256',sha(canonical)),('status','COMPLETE')]:
        assert f'{k} {val}' in summary.splitlines()[-6:]
    print(f'{arm} verified two fixed slots by physical book-line arithmetic, stable distinct White/Black PIDs {",".join(all_pids)}, and both ready before every start. Starts were {sum(white_root.values())} White and {len(white_root)-sum(white_root.values())} Black to move; search counts per process match the starting color and recorded ply counts. All four processes verified active net, all logged options and CPU affinities. {len(ordered)} games, {record_count} numerically ordered records, {na_total} NA, sum {node_sum}, sha256 {sha(canonical)}.')

if __name__=='__main__':
    parser_checks()
    for arm in sys.argv[1:]: examine(arm)
