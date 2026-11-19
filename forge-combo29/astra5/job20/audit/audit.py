"""Replay completed seeded games and verify each kept info label directly against the raw engine label."""
import argparse
import csv
from collections import Counter
from datetime import datetime
from functools import lru_cache
import hashlib
from itertools import zip_longest
from pathlib import Path
import random
import re
import subprocess
import sys
from contextlib import ExitStack

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
try:import chess
except ImportError:
    sys.path.insert(0,str(WORK/'j10fens/vendor'))
    import chess
ARMS={'K20':('K20-1','K20-2',600001,600020),'C20':('K20-1','C20',600001,600020),
      'P1':('P1-r15d','P1-kF',600101,603100),'P2':('P2-r15d','P2-kF',610001,610500),
      'P3':('P3-r15d','P3-kF',620001,620100)}
MOVE=re.compile(rb'[a-h][1-8][a-h][1-8][nbrq]?')
TOKENS=re.compile(rb'\S+')
FIELD_NAMES=set('depth seldepth multipv score wdl nodes hashfull tbhits cpuload currmove currmovenumber refutation currline pv string ebf'.split())
ARM_HEADER='arm status games records na_records score_records mate_records mate_positive mate_zero mate_negative nodes bytes sha256'.split()
GAME_HEADER='arm game records na_records score_records mate_records nodes bytes sha256 result termination'.split()
def table(p,header,rows):
    with p.open('w',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(header);w.writerows(rows)
def rows(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def normalized(raw):
    if raw==b'NA':return raw
    assert raw.startswith(b'info depth'),raw
    matches=list(TOKENS.finditer(raw));spans=[]
    for i,t in enumerate(matches[:-1]):
        if t.group() in (b'time',b'nps') and matches[i+1].group().isdigit():
            start=t.start()-1;end=matches[i+1].end()
            assert start>=0 and raw[start:start+1].isspace()
            spans.append((start,end))
    for start,end in reversed(spans):
        raw=raw[:start]+raw[end:]
    return raw
def decoded(line):
    assert line.endswith(b'\n') and not line.endswith(b'\r\n'),line
    head,ply,move,label=line[:-1].split(b' ',3)
    assert head==str(int(head)).encode() and ply==str(int(ply)).encode() and MOVE.fullmatch(move),(head,ply,move)
    assert label==b'NA' or label.startswith(b'info depth'),label
    return (int(head),int(ply),move,label)
def numeric(tokens,key):
    idx=tokens.index(key)
    return int(tokens[idx+1])
def label_data(label):
    if label==b'NA':return Counter(na=1)
    words=label.split()
    assert words[:2]==[b'info',b'depth'] and int(words[2])>=0,label
    assert b'time' not in words and b'nps' not in words,label
    c=Counter()
    if b'nodes' in words:c['nodes']=numeric(words,b'nodes')
    if b'score' in words:
        idx=words.index(b'score')
        c['score']=1
        assert words[idx+1] in (b'cp',b'mate')
        number=int(words[idx+2])
        if words[idx+1]==b'mate':
            c['mate']=1
            c['positive' if number>0 else 'negative' if number<0 else 'zero']=1
    return c
@lru_cache(maxsize=4200)
def opening(gid):
    rng=random.Random(gid);board=chess.Board();prefix=[]
    for i in range(8):
        move=rng.choice(list(board.legal_moves));board.push(move);prefix.append(move.uci())
        if board.is_game_over(claim_draw=True):break
    return tuple(prefix),board.fen(en_passant='fen')
@lru_cache(maxsize=4)
def replay(gid,moves):
    prefix,_=opening(gid);b=chess.Board()
    for m in prefix:b.push_uci(m)
    assert len(prefix)+len(moves)<=300
    for m in moves:
        assert not b.is_game_over(claim_draw=True),(gid,'moved after game over')
        b.push(b.parse_uci(m.decode('ascii')))
    ending=b.outcome(claim_draw=True)
    assert ending or len(prefix)+len(moves)==300,(gid,'premature stop')
    return (ending.result(),ending.termination.name) if ending else ('*','PLY_LIMIT')
def first_field(a,b):
    if a==b:return 'identical'
    if b'NA' in (a,b):return 'info availability'
    pairs=[]
    for s in (a,b):
        seq=[];field='info'
        for i,span in enumerate(TOKENS.finditer(s)):
            word=span.group().decode('ascii')
            if i and word in FIELD_NAMES and field!='pv':field=word
            seq.append((word,field))
        pairs.append(seq)
    for i,(left,right) in enumerate(zip_longest(*pairs)):
        if left!=right:
            field=(left or right)[1]
            if left and right and left[1]!=right[1]:field=left[1]+'/'+right[1]
            return f'{field}, info token {i+1}: {(left or ("(missing)",))[0]} / {(right or ("(missing)",))[0]}'
    return 'whitespace'
def first_description(stage,a,b,gid,idx,ars,brs,line_number=None):
    ar=ars[idx] if idx<len(ars) else None;br=brs[idx] if idx<len(brs) else None
    sample=ar or br;ply=decoded(sample)[1]
    prefix,fen=opening(gid)
    text=[f'{stage}: game {gid}, absolute ply {ply}'+(f', record line {line_number}.' if line_number else '.'),f'Opening FEN after seeded prefix {fen}','Seeded UCI moves '+' '.join(prefix)]
    if ar is not None and br is not None:
        a_data=decoded(ar);b_data=decoded(br)
        assert a_data[:2]==b_data[:2]
        difference=first_field(a_data[3],b_data[3])
        text.extend([f'First differing record field: {"bestmove" if a_data[2]!=b_data[2] else difference}.',f'First differing info field in emitted token order: {difference}.'])
    else:text.append('One game ended before this ply.')
    for arm,record,data in [(a,ar,ars),(b,br,brs)]:
        text.append(f'{arm} record '+(record[:-1].decode('ascii') if record else '(absent)'))
        seq=list(prefix)+[decoded(line)[2].decode('ascii') for line in data[:idx]]
        text.append(f'{arm} position command: position startpos moves '+' '.join(seq))
    return text
class Arm:
    def __init__(self,name,path,raw,st,lo,hi):
        self.name=name;self.path=path;self.lo=lo;self.hi=hi
        log=(path/'run.log').read_text();self.log=log
        self.status=log.rstrip().splitlines()[-1].split()[-1]
        assert self.status in ('COMPLETE','INCOMPLETE'),(name,self.status)
        self.receipts=rows(path/'games.tsv')
        assert [int(r['book_line']) for r in self.receipts]==list(range(lo,lo+len(self.receipts)))
        if self.status=='COMPLETE':assert len(self.receipts)==hi-lo+1
        opens=rows(path/'openings.tsv')
        for r in opens:
            assert tuple(r['moves'].split())==opening(int(r['game']))[0],(name,r)
        self.nofile=rows(path/'no-info.tsv');self.na_events=[]
        self.records=st.enter_context((path/'records.txt').open('rb'))
        self.raw=st.enter_context(raw.open('rb'));self.c=Counter();self.game_rows=[]
        self.pid=None;self.digest=hashlib.sha256();self.raw_digest=hashlib.sha256()
    def game(self,gid):
        r=self.receipts[gid-self.lo]
        assert int(r['book_line'])==gid
        start=self.records.tell();n=int(r['plies']);lines=[];moves=[];c=Counter()
        white=chess.STARTING_FEN.split()[1]=='w'
        prefix,_=opening(gid)
        white=not bool(len(prefix)%2)
        roles=[0,0];role_na=[0,0]
        for j in range(n):
            row=self.records.readline();raw=self.raw.readline()
            g,p,m,l=decoded(row);gr,pr,mr,rl=decoded(raw)
            assert (g,p,m)==(gr,pr,mr) and (g,p)==(gid,len(prefix)+j),(self.name,gid,j)
            assert l==normalized(rl),(self.name,gid,p,l,normalized(rl))
            self.digest.update(row);self.raw_digest.update(raw);lines.append(row);moves.append(m)
            counts=label_data(l);c.update(counts)
            who=0 if white else 1;roles[who]+=1;role_na[who]+=counts['na']
            if counts['na']:
                self.na_events.append((gid,p,'White' if white else 'Black',r['p1_pid'],m.decode()))
            white=not white
        assert (r['result'],r['termination'])==replay(gid,tuple(moves)),(self.name,gid)
        for k,v in [('nodes',c['nodes']),('na',c['na']),('score',c['score']),('mate',c['mate']),('book_line',gid),('record_bytes',self.records.tell()),('p1_search',roles[0]),('p2_search',roles[1]),('p1_na',role_na[0]),('p2_na',role_na[1])]:
            assert int(r[k])==v,(self.name,gid,k,r[k],v)
        assert r['p1_pid']==r['p2_pid']
        if self.pid is None:self.pid=r['p1_pid']
        assert self.pid==r['p1_pid'] and int(r['slot'])==1
        assert datetime.fromisoformat(r['end_utc'])<datetime.fromisoformat('2026-11-19T01:55:01Z')
        blob=b''.join(lines);assert len(blob)==self.records.tell()-start
        self.game_rows.append((self.name,gid,n,c['na'],c['score'],c['mate'],c['nodes'],len(blob),hashlib.sha256(blob).hexdigest(),r['result'],r['termination']))
        self.c.update(c);self.c['records']+=n;self.c['bytes']+=len(blob)
        return lines
    def finish(self):
        assert not self.records.read(1) and not self.raw.read(1),self.name
        c=self.c;sha=self.digest.hexdigest()
        assert [(int(r['book_line']),int(r['ply']),r['side'],r['engine_pid'],r['bestmove']) for r in self.nofile]==self.na_events
        for label,value in dict(games=len(self.receipts),records=c['records'],na_records=c['na'],score_records=c['score'],mate_records=c['mate'],sum_nodes=c['nodes'],records_sha256=sha).items():
            assert re.findall(r'^'+label+r' (\S+)$',self.log,re.M)==[str(value)],(self.name,label,value)
        for m in ('loaded','active'):
            assert len([s for s in self.log.splitlines() if 'NNUE v3 '+m in s and 'checksum 30ab43b4ba5db5f3' in s])==1
        assert not re.search(r'unknown option|invalid value',self.log,re.I)
        return (self.name,self.status,len(self.receipts),c['records'],c['na'],c['score'],c['mate'],c['positive'],c['zero'],c['negative'],c['nodes'],c['bytes'],sha)

def sample_evidence(arm):
    items={}
    with (arm.path/'sample-uci.txt').open('rb') as f:
        for line in f:
            s=line.rstrip(b'\n')
            if s.startswith(b'begin '):
                _,gid,ply=s.split();key=(int(gid),int(ply));commands=[];reply=[];rc=None
            elif s.startswith(b'> '):commands.append(s[2:])
            elif s.startswith(b'< '):reply.append(s[2:])
            elif s.startswith(b'record '):rc=s[len(b'record '):]+b'\n'
            elif s==b'end':
                assert decoded(rc)[:2]==key and reply[-1].startswith(b'bestmove '),(arm.name,key)
                depth=[r for r in reply[:-1] if r.startswith(b'info depth')]
                literal=depth[-1] if depth else b'NA'
                assert decoded(rc)[2]==reply[-1].split()[1] and decoded(rc)[3]==normalized(literal)
                assert len(commands)==2 and key not in items
                items[key]=(commands,rc,literal)
            else:raise ValueError(s)
    return items
def settings(arm):
    hm=1 if arm.name.startswith('P2-') else 16
    cmd='go nodes 20000' if arm.name.startswith('P3-') else 'go softnodes 2000'
    source=(WORK/'j7base/pc20.txt').read_text().splitlines()
    expected=dict(s.removeprefix('setoption name ').rsplit(' value ',1) for s in source)
    expected['Hash']=str(hm);expected['NNUEArch']='true'
    if arm.name=='C20':expected['LmrQuietBase']='60'
    actual=dict(re.findall(r'(?:^| )setoption name (.*?) value (.*)$',arm.log,re.M))
    assert all(actual.get(k)==v for k,v in expected.items()),(arm.name,actual,expected)
    assert Path(actual['NNUEArchFile']).name=='net768.nnue'
    assert any(s.startswith(f'arm {arm.name} build ') and f'game_range {arm.lo} {arm.hi} go {cmd} hash_mb {hm}' in s for s in arm.log.splitlines())
    return cmd.encode()
def run(args):
    first,second,lo,hi=ARMS[args.stage]
    out=args.output/args.stage;out.mkdir(parents=True,exist_ok=True)
    with ExitStack() as close:
        arms=[Arm(n,args.results/n,args.raw/(n+'.txt'),close,lo,hi) for n in (first,second)]
        last=max(len(a.receipts) for a in arms)
        diffs=[];detail=None;rown=1
        samples={a.name:sample_evidence(a) for a in arms}
        expected_cmd={a.name:settings(a) for a in arms}
        sampled={a.name:0 for a in arms}
        for gid in range(lo,lo+last):
            moves_by_arm=[]
            for a in arms:
                if gid>=lo+len(a.receipts):
                    moves_by_arm.append(None);continue
                rr=a.game(gid);moves_by_arm.append(rr)
                pref=opening(gid)[0]
                for (key,ply),(commands,rc,literal) in samples[a.name].items():
                    if key!=gid:continue
                    idx=ply-len(pref)
                    assert rr[idx]==rc and decoded(rc)[3]==normalized(literal)
                    allmoves=[m.encode() for m in pref]+[decoded(x)[2] for x in rr[:idx]]
                    assert commands==[b'position startpos moves '+b' '.join(allmoves),expected_cmd[a.name]],(a.name,key,ply)
                    sampled[a.name]+=1
            left,right=moves_by_arm
            if left is None or right is None:continue
            if left!=right:
                n=next(j for j,(x,y) in enumerate(zip_longest(left,right)) if x!=y)
                x=left[n] if n<len(left) else None;y=right[n] if n<len(right) else None
                lf=first_field(decoded(x)[3],decoded(y)[3]) if x and y else 'absent ply'
                diffs.append((gid,decoded(x or y)[1],len(left),len(right),lf))
                if detail is None:detail=first_description(args.stage,first,second,gid,n,left,right,rown+n)
            rown+=len(left)
        for a in arms:
            assert sampled[a.name]==len(samples[a.name]) or a.status=='INCOMPLETE'
        totals=[a.finish() for a in arms]
        check=subprocess.run(['cmp','-s',str(arms[0].path/'records.txt'),str(arms[1].path/'records.txt')]).returncode
        assert check in (0,1)
        common=min(len(a.receipts) for a in arms)
        full=all(a.status=='COMPLETE' for a in arms)
        if full:assert check==bool(diffs)
        if args.stage=='K20':assert all(a.c['score']==a.c['records'] for a in arms)
        read=('IDENTICAL' if check==0 else 'DIFFERS') if full else 'INCOMPLETE'
        lines=[f'{args.stage} {read}',f'Canonical cmp -s exit {check}; {len(diffs)} different games in {common} jointly completed games. Planned {hi-lo+1} per arm.']
        for a in arms:
            c=a.c
            lines.append(f'{a.name}: {a.status}. Game IDs {lo}–{lo+len(a.receipts)-1}, {len(a.receipts)} games, {c["records"]} records, {c["na"]} NA, {c["score"]} scores, {c["mate"]} mate scores (positive {c["positive"]}, zero {c["zero"]}, negative {c["negative"]}), {c["nodes"]} nodes, SHA-256 {a.digest.hexdigest()}.')
            lines.append(f'{a.name}: verified {c["records"]} raw-label projections byte for byte; raw selected depth-line record stream SHA-256 {a.raw_digest.hexdigest()}. Selected the final depth line from {sampled[a.name]} sampled full UCI searches and verified their position commands, bestmoves and labels.')
        lines.append('Every whole game replayed from its seeded opening, including its initial move history for draw claims. Last depth lines are checked before bestmove, with only the time/nps numeric fields removed; the later softnodes diagnostic is outside the depth-line selection.')
        detail=detail or ['No differing record in games completed by both arms.']
        table(out/'arms.tsv',ARM_HEADER,totals);table(out/'games.tsv',GAME_HEADER,[g for a in arms for g in a.game_rows])
        table(out/'differences.tsv',('game','absolute_ply','left_records','right_records','first_info_field'),diffs)
        (out/'first-difference.txt').write_text('\n'.join(detail)+'\n')
        (out/'summary.txt').write_text('\n'.join(lines+detail)+'\n')
        sig=out/'verified.txt.tmp';sig.write_text(f'{args.stage} {read}, {len(diffs)} differing games in {common} jointly completed games.\n');sig.replace(out/'verified.txt')
        print('\n'.join(lines),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=ARMS);p.add_argument('--results',type=Path,default=WORK/'j20match/results')
    p.add_argument('--raw',type=Path,default=WORK/'j20match/raw-labels');p.add_argument('--output',type=Path,default=HERE)
    run(p.parse_args())
