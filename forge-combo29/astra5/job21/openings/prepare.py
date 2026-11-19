"""Recover historic openings, then filter the full fastchess shuffled book order."""
from pathlib import Path
import csv,re,hashlib,subprocess,sys,tempfile,os
from collections import defaultdict
try: import chess
except ImportError:
    sys.path.insert(0,'/workspace/work/j10fens/vendor')
    import chess

W=Path('/workspace/work'); OUT=W/'j21book'
ARCH=W/'astra5/forge-combo29/astra5'; BOOK=W/'j8gate/UHO_Lichess_4852_v1.epd'
GAMES={'C21':(7391,100),'B1':(7392,600),'B2':(7393,600)}
TOTAL=2632036
UHO='7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
SHUFFLE="""
#include <algorithm>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>
int main(int argc, char** argv) {
    const size_t n = std::stoull(argv[1]), take = std::stoull(argv[2]);
    std::mt19937_64 g(std::stoull(argv[3])); std::vector<size_t> a(n);
    std::iota(a.begin(), a.end(), 1);
    for (size_t i=0; i<take; ++i) {
        if (i+1<n) std::swap(a[i],a[i+g()%(n-i)]);
        std::cout<<a[i]<<'\\n';
    }
}
"""
def shuffle(n,take,seed):
    exe=OUT/'shuffle'
    if not exe.exists(): subprocess.run(['g++','-O2','-std=c++17','-x','c++','-','-o',str(exe)],input=SHUFFLE,text=True,check=True)
    return list(map(int,subprocess.check_output([str(exe),str(n),str(take),str(seed)]).split()))
def sha(data):return hashlib.sha256(data).hexdigest()
def key(fen):
    board,side,castle,ep,_,_=fen.split()
    return board,side,''.join(c for c in 'KQkq' if c in castle) or '-'
def put(path,b):
    p=OUT/path
    if p.exists() and p.read_bytes()==b:return
    a=p.with_suffix(p.suffix+'.tmp');a.write_bytes(b);a.replace(p)
def tsv(name,header,rows):
    data=['\t'.join(header)]+['\t'.join(map(str,row)) for row in rows]
    put(name,('\n'.join(data)+'\n').encode())

def main():
    assert chess.__version__=='1.11.2'
    history=defaultdict(set); receipts=[]; lineset=set(); seedmoves={}
    round_total=0
    pgn_paths=[p for j in (8,9,10,11,12,13,14,15,16,17,18,19,20) for p in sorted((ARCH/f'job{j}').glob('*.pgn'))]
    assert len(pgn_paths)==24
    overlap=ARCH/'job15/T1b/opening-overlap.txt'
    saved_interrupt={}
    for label,roundno,fen in re.findall(r'^(T1 prior|T1b current) round (\d+): (.+)$',overlap.read_text(),re.M):
        saved_interrupt[(label.split()[0],int(roundno))]=fen
    assert len(saved_interrupt)==4
    for p in pgn_paths:
        data=p.read_bytes()
        fn=p.with_suffix('.out')
        controller=fn.read_bytes()
        starts={int(x) for x in re.findall(rb'^Started game (\d+) of ',controller,re.M)}
        rounds=defaultdict(list)
        for h in re.findall(rb'(?m)^\[Event [^\n]*(?:\n\[[^\n]+)*',data):
            ri=int(re.search(rb'(?m)^\[Round "(\d+)"\]',h)[1])
            fen=re.search(rb'(?m)^\[FEN "([^"]+)"\]',h)[1].decode()
            rounds[ri].append(fen)
        assert all(len(values)==2 and values[0]==values[1] for values in rounds.values())
        assert rounds and starts and set(rounds)<={(g+1)//2 for g in starts}
        for rid,vals in rounds.items(): history[key(vals[0])].add('prior_PGN')
        missing=sorted({(g+1)//2 for g in starts}-rounds.keys())
        for rid in missing: history[key(saved_interrupt[p.stem,rid])].add('interrupted_start')
        receipts.append((p.relative_to(ARCH),'PGN paired starts',len(rounds),len(starts),','.join(map(str,missing)) or '-',sha(data),sha(controller)))
        round_total+=len(rounds)
    for j in range(16,21):
        for log in sorted((ARCH/f'job{j}').glob('*/games.tsv')):
            arm=log.parent
            raw=log.read_bytes()
            rows=list(csv.DictReader(raw.decode().splitlines(),delimiter='\t'))
            ids=[int(r['book_line']) for r in rows]
            if not ids: continue
            if min(ids)<400000:
                lineset.update(ids)
                receipts.append((log.relative_to(ARCH),'EPD selfplay receipts',len(rows),len(set(ids)),'-',sha(raw),'-'))
            else:
                op=arm/'openings.tsv'
                roots=list(csv.DictReader(op.read_text().splitlines(),delimiter='\t'))
                assert list(map(int,[r['game'] for r in roots]))==ids
                for row in roots:
                    i=int(row['game']); seq=row['moves']
                    if i in seedmoves:assert seedmoves[i]==seq
                    else:seedmoves[i]=seq
                receipts.append((op.relative_to(ARCH),'random selfplay roots',len(roots),len(set(ids)),'-',sha(op.read_bytes()),sha(raw)))
    assert lineset==set(range(2201,3813))
    for moves in seedmoves.values():
        b=chess.Board()
        for mv in moves.split():b.push_uci(mv)
        history[key(b.fen(en_passant='fen'))].add('random_selfplay')
    prefix={stage:shuffle(TOTAL,n+128,seed) for stage,(seed,n) in GAMES.items()}
    required=lineset.union(*(set(k) for k in prefix.values()))
    data={}; bookhash=hashlib.sha256()
    with BOOK.open('rb') as f:
        for number,row in enumerate(f,1):
            bookhash.update(row)
            if number in required:data[number]=row.rstrip(b'\r\n').decode()
    assert number==TOTAL and bookhash.hexdigest()==UHO and len(data)==len(required)
    for i in lineset:history[key(data[i])].add('book_selfplay')
    tsv('history-sources.tsv',['source','kind','observed_rounds_or_rows','started_games_or_distinct_ids','PGN_missing_started_rounds','source_sha256','controller_or_games_sha256'],receipts)
    base_history=set(history)
    unique={tag:sum(tag in v for v in history.values()) for tag in ('prior_PGN','interrupted_start','book_selfplay','random_selfplay')}
    notes=[f'Original book SHA-256 {UHO}',f'Original physical entries {TOTAL}',f'Prior fastchess match PGNs {len(pgn_paths)}; {round_total} completed pairs and {unique["prior_PGN"]} distinct historical paired position keys. Four extra started round roots were reconstructed for T1 (rounds 56,57) and T1b (58,59).',
        f'Job 16–20 game receipts supply {len(lineset)} original UHO line numbers (2201–3812) and {len(seedmoves)} distinct generated opening IDs. After position-key deduplication: {unique["book_selfplay"]} UHO roots, {unique["random_selfplay"]} random roots, {len(base_history)} total keys across all historical sources.',
        'Position key uses piece placement, side to move and castling rights in KQkq order. En-passant and FEN counters are ignored for exclusion, as in jobs 12 to 15.',
        'The underlying book uses one FEN per physical line. Original full-book seeded order uses fastchess mt19937_64 and incremental Fisher-Yates; removed entries are replaced by the next eligible candidate. The derived small book inverts the deterministic second fastchess shuffle, so the effective match order is the TSV round order.']
    put('history.txt',('\n'.join(notes)+'\n').encode())
    for stage,(seed,n) in GAMES.items():
        selected=[]; skipped=[]; this=set()
        for rank,lineno in enumerate(prefix[stage],1):
            fen=data[lineno]; k=key(fen)
            if k in history or k in this:
                reason=sorted(history.get(k,set())) or ['same_match']
                skipped.append((rank,lineno,','.join(reason)));continue
            selected.append((lineno,rank,fen));this.add(k)
            if len(selected)==n:break
        assert len(this)==len(selected)==n and not (this&set(history))
        perm=shuffle(n,n,seed); output=[None]*n
        for pick,(_,_,fen) in zip(perm,selected):output[pick-1]=fen
        assert [output[i-1] for i in perm]==[f for _,_,f in selected]
        epd=('\n'.join(output)+'\n').encode()
        tsv(stage+'-lines.tsv',['round','original_epd_line','full_book_seed_rank','position_key_sha256'],((r,line,rank,sha(' '.join(key(f)).encode())) for r,(line,rank,f) in enumerate(selected,1)))
        tsv(stage+'-skips.tsv',['full_book_seed_rank','original_epd_line','excluded_source'],skipped)
        info=[f'match {stage} seed {seed}',f'original_sha256 {UHO}',f'original_nonempty_entries {TOTAL}',f'scheduled_pairs {n}',f'full_book_seeded_candidates_tested {selected[-1][1]}',f'skipped {len(skipped)}',f'prior_history_keys {len(base_history)}',f'earlier_job21_keys_reserved {len(set(history)-base_history)}',f'selected_distinct {len(this)}',f'overlap_with_history_or_earlier_job21 0',f'derived_sha256 {sha(epd)}',f'line_schedule_sha256 {sha((OUT/(stage+"-lines.tsv")).read_bytes())}']
        put(stage+'-opening-preflight.txt',('\n'.join(info)+'\n').encode())
        put(stage+'.epd',epd)
        for k in this:history[k].add('job21_'+stage)
        print(stage,*info[-4:],flush=True)
if __name__=='__main__':main()
