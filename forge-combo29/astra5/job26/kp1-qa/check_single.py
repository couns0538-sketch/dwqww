"""Recount KP1 and CP1 from timestamped raw UCI lines; check both saved row formats."""
import argparse
import csv
from hashlib import sha256
from pathlib import Path
import re
import sys

NAMES = "Threads Hash OwnBook MateAlphaGuard LmrQuietBase LmrQuietDivisor LmrNoisyBase LmrNoisyDivisor LmrHistoryDivisor NullMoveBase LmpBase HistoryPruneMultiplier HistoryBonusQuadratic HistoryBonusLinear HistoryBonusMax SingularDepth IirDepth NonPawnCorrection CuckooRep HistRework TtPruneV2 CorrHistV2 NodeClock".split()
VALUES = "1 16 false true 93 205 13 333 5643 5 8 2220 24 54 2212 6 2 true true 2 true true 1000".split()
PINS = {
    "O0":("3eac50dd8fd5297e",54326,0,None),
    "A0":("424d931234dd3ff9",98026,1,1585152),
    "A1":("5a85f018917c736f",82001,1,1585152),
    "B0":("244776b6649f2ce1",45372,2,675840),
    "C0":("4e8210e936e59fd5",20715,7,174080),
}
TIMES = {"O0":6000,"A0":6000,"A1":6000,"B0":2000,"C0":300,"CP1":6000}
DIGESTS={"O":"02d59eaf2515a4e11aecb78c5736db193812516f42ab8a6aa0b2411332186300",
         "G":"af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d"}


def check(ok, message):
    if not ok: raise ValueError(message)


def raw_text(arm):
    path=arm/'uci.log'
    if path.exists():
        check(path.stat().st_size<=20_000_000, f"{arm} unsplit oversized log")
        return path.read_text()
    with (arm/'uci.log.parts.tsv').open() as f:
        entries=list(csv.DictReader(f,delimiter='\t'))
    combined=bytearray()
    for i,entry in enumerate(entries[:-1],1):
        check(entry['part']==f'uci.part{i:04d}.log',f"{arm} out-of-order log parts")
        data=(arm/entry['part']).read_bytes()
        check(len(data)==int(entry['bytes']) and len(data)<=15_000_000 and sha256(data).hexdigest()==entry['sha256'],
              f"{arm} log part digest mismatch")
        combined.extend(data)
    whole=entries[-1]
    check(whole['part']=='WHOLE' and int(whole['bytes'])==len(combined) and sha256(combined).hexdigest()==whole['sha256'],
          f"{arm} combined raw digest mismatch")
    return combined.decode('ascii')


def audit(root,epds,name):
    arm=root/name
    suite="O" if name=="O0" else "G"
    epi=(epds/(suite+'.epd')).read_bytes()
    check(sha256(epi).hexdigest()==DIGESTS[suite],f"{suite} EPD digest")
    fens=[" ".join(line.split()[:4])+ " 0 1" for line in epi.decode().splitlines()]
    expected_count=200 if suite=="O" else 353
    check(len(fens)==expected_count,"wrong number of original FENs")
    vals=VALUES.copy()
    if name=="CP1": vals[-1]="2000"
    options=[f"setoption name {s} value {v}" for s,v in zip(NAMES,vals,strict=True)]
    if name=="A1": options.append('setoption name TmFinishIteration value true')
    text=raw_text(arm).splitlines()
    events=[]
    for n,raw in enumerate(text,1):
        t,d,s=raw.split(' ',2)
        check(t.isdecimal() and d in ('>','<'),f"{name} bad raw line {n}")
        check(d=='>' or not re.search(r"unknown option|invalid value|\bERROR\b",s,re.I),f"{name} engine refusal {n}: {raw}")
        events.append((d,s))
    settings=[s for d,s in events if d=='>' and s.startswith('setoption ')]
    check(settings==options,f"{name} ordered UCI options differ\nexpected {options}\nobserved {settings}")
    check(events.count(('>','uci'))==1 and events.count(('<','uciok'))==1 and events.count(('>','quit'))==1,
          f"{name} expected one UCI handshake and quit")
    with (arm/'searches.tsv').open(newline='') as f:
        receipts=list(csv.DictReader(f,delimiter='\t'))
    check(len(receipts)==expected_count,f"{name} saved search count")
    clock=TIMES[name]
    go=f'go wtime {clock} btime {clock} winc 60 binc 60'
    starts=[j for j,e in enumerate(events) if e==('>','ucinewgame')]
    check(len(starts)==expected_count,f"{name} ucinewgame count")
    canonical=[]
    overs=[]
    spent=holds=sum_nodes=final_sum=0
    for i,(a,b,fen,row) in enumerate(zip(starts,starts[1:]+[len(events)-1],fens,receipts,strict=True),1):
        raw_block=events[a:b]
        cmds=[s for d,s in raw_block if d=='>']
        check(cmds==['ucinewgame','isready','position fen '+fen,go],f"{name} position {i} commands: {cmds}")
        check(raw_block.count(('<','readyok'))==1 and raw_block.index(('<','readyok'))<raw_block.index(('>','position fen '+fen)),
              f"{name} readyok order at position {i}")
        go_index=raw_block.index(('>',go))
        out=[(n+a+1,s) for n,(d,s) in enumerate(raw_block) if d=='<' and n>go_index]
        last_depth=[(n,s) for n,s in out if s.startswith('info depth ') and re.search(r'\bnodes \d+\b',s)]
        stop=[(n,s) for n,s in out if re.fullmatch(r'info string softnodes nodes \d+',s)]
        best=[(n,s) for n,s in out if s.startswith('bestmove ')]
        check(last_depth and len(stop)==len(best)==1 and last_depth[-1][0]<stop[0][0]<best[0][0],f"{name} position {i} last lines")
        hold_count=sum(s.startswith('info string TmFinishIteration hold') for _,s in out)
        fields=last_depth[-1][1].split()
        depth=int(fields[fields.index('depth')+1]); last=int(fields[fields.index('nodes')+1]); N=int(stop[0][1].split()[-1])
        move=best[0][1].split()[1]
        check(last<=N,f"{name} position {i} stopped nodes smaller than last depth nodes")
        vals=(i,fen,depth,last,move,N,N//1000,hold_count)
        rec=tuple(row[k] for k in ('index','fen','depth','last_nodes','bestmove','N','T1000','hold_lines'))
        check(tuple(map(str,vals))==rec,f"{name} position {i} saved fields disagree: {vals!r} {rec!r}")
        canonical.append(f"{i} {depth} {last} {move}\n")
        sum_nodes+=N; final_sum+=last; spent+=N//1000; holds+=int(hold_count>0)
        if N>last: overs.append((i,depth,last,N,N-last,stop[0][0]))
    canonical=''.join(canonical).encode('ascii')
    check(canonical==(arm/'rows.txt').read_bytes(),f"{name} literal saved row bytes disagree")
    sha=sha256(canonical).hexdigest()[:16]
    over_N=sorted({r[3] for r in overs})
    if name in PINS:
        expected,T,count,quoted=PINS[name]
        check((sha,spent,len(overs))==(expected,T,count),f"{name} pin mismatch {(sha,spent,len(overs))} vs {(expected,T,count)}")
        check(over_N==([quoted] if count else []),f"{name} quoted over-N {quoted}; observed {over_N}")
        if name=="A1": check(holds==162,f"A1 held on {holds} searches")
        if name in ('O0','A0'):
            first=b'1 16 172312 f1e2' if name=='O0' else b'1 16 170070 g7g6'
            check(canonical.split(b'\n',1)[0]==first,f"{name} first row")
    else:
        check(sha!=PINS['A0'][0],'CP1 matches the A0 rows digest')
    print(f"{name} {expected_count} searches; row sha {sha}; T1000 {spent}; over {len(overs)}; "
          f"unique over-N {over_N}; holds {holds}; finished-depth nodes sum {final_sum}; stopped N sum {sum_nodes}")
    for i,depth,last,N,diff,line in overs:
        print(f"  position {i} depth {depth} last_depth_nodes {last} N {N} excess {diff} stop_count_log_line {line}")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('runs',type=Path)
    p.add_argument('epds',type=Path)
    p.add_argument('names',nargs='+',choices=list(TIMES))
    opts=p.parse_args()
    for name in opts.names:
        audit(opts.runs,opts.epds,name)
        if name=='CP1':
            a=(opts.runs/'A0'/'rows.txt').read_bytes().splitlines()
            c=(opts.runs/'CP1'/'rows.txt').read_bytes().splitlines()
            changed=[i for i,(x,y) in enumerate(zip(a,c,strict=True)) if x!=y]
            moves=sum(x.split()[3]!=y.split()[3] for x,y in zip(a,c,strict=True))
            check(changed,'CP1 positive control did not change any rows')
            first=changed[0]
            print(f'CP1 vs A0: {len(changed)}/{len(a)} canonical rows differ, {moves}/{len(a)} bestmoves differ.')
            print('First differing row A0: '+a[first].decode())
            print('First differing row CP1: '+c[first].decode())


if __name__=='__main__':
    try: main()
    except (ValueError,KeyError,OSError) as e: sys.exit(str(e))
