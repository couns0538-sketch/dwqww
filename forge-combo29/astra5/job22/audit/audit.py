"""Verify each durable game and raw UCI last-info projection while the single-process runs advance."""
import argparse,csv,hashlib,random,re,subprocess,sys,time
from collections import Counter
from functools import lru_cache
from pathlib import Path
from datetime import datetime
from itertools import zip_longest
HERE=Path(__file__).resolve().parent
WORK=HERE.parent
MATCH=WORK/'j22match'
RAW=MATCH/'results'
try:import chess
except ImportError:
    sys.path.insert(0,str(WORK/'j10fens/vendor'));import chess
STAGES=('K22','C22','L1','L0-r15d','L0-kF')
PAIR={'K22':('K22-1','K22-2',700001,700010),'C22':('K22-1','C22',700001,700010),'L1':('L1-r15d','L1-kF',700001,705000)}
ARM_HEAD='arm status games first_game last_game records na_records nodes bytes sha256 pid start_ticks'.split()
GAME_HEAD='arm game plies na_records nodes bytes sha256 result termination byte_offset'.split()
RSS_HEAD='arm completed game pid start_ticks vmrss_kb observed_utc'.split()
ROW=re.compile(rb'([1-9][0-9]*) ([1-9][0-9]*) ([a-h][1-8][a-h][1-8][nbrq]?) (NA|0|[1-9][0-9]*)\n')
def rows(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def table(path,cols,records):
    with path.open('w',newline='') as f:w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(cols);w.writerows(records)
def status(p):
    if not p.exists():return ''
    with p.open('rb') as f:
        f.seek(0,2);f.seek(max(0,f.tell()-256));last=f.read().rstrip().splitlines()
    if last and last[-1].startswith(b'status '):return last[-1].split(b' ',1)[1].decode()
    return ''
@lru_cache(maxsize=6500)
def opening(gid):
    b=chess.Board();r=random.Random(gid);moves=[]
    for i in range(8):
        m=r.choice(list(b.legal_moves));b.push(m);moves.append(m.uci())
        if b.is_game_over(claim_draw=True):break
    return tuple(moves),b.fen(en_passant='fen')
@lru_cache(maxsize=12)
def replay(gid,history):
    op,_=opening(gid);b=chess.Board()
    for m in op:b.push_uci(m)
    for i,m in enumerate(history):
        assert not b.is_game_over(claim_draw=True),(gid,i,'past game end')
        b.push(b.parse_uci(m.decode('ascii')))
    assert len(op)+len(history)<=300
    end=b.outcome(claim_draw=True)
    assert end or len(op)+len(history)==300,(gid,len(history),'not a whole game')
    return (end.result(),end.termination.name) if end else ('*','PLY_LIMIT')
def decode(line):
    m=ROW.fullmatch(line);assert m,line
    return int(m[1]),int(m[2]),m[3],None if m[4]==b'NA' else int(m[4])
def difference(stage,names,gid,left,right,rown):
    i=next(idx for idx,(a,b) in enumerate(zip_longest(left,right)) if a!=b)
    sample=left[i] if i<len(left) else right[i];op,fen=opening(gid)
    lines=[f'{stage}: game {gid}, absolute ply {decode(sample)[1]}, row {rown+i}.','Opening FEN '+fen,'Eight seeded UCI moves '+' '.join(op)]
    for name,data in zip(names,(left,right)):
        row=data[i].decode().rstrip('\n') if i<len(data) else '(absent)'
        lines.extend([name+' record '+row,name+' position command: position startpos moves '+' '.join(list(op)+[decode(s)[2].decode() for s in data[:i]])])
    return lines
def check_lifetime(name,pid,log):
    """Save the contemporaneous observation and reuse it for a later offline reread."""
    dest=HERE/'L1';dest.mkdir(exist_ok=True)
    evidence=dest/('process-'+name+'.txt')
    ticks=re.findall(r'^engine_start_ticks (\d+)$',log,re.M)
    assert len(ticks)==1,(name,'unique process start')
    proc=Path('/proc')/pid
    try:
        observed_ticks=proc.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]
        stat=proc.joinpath('status').read_text()
        exe=proc.joinpath('cmdline').read_bytes().split(b'\0')[0].decode()
    except (FileNotFoundError,PermissionError,ProcessLookupError):
        observed_ticks=None
    if observed_ticks==ticks[0] and exe:
        rss=re.search(r'^VmRSS:\s+(\d+) kB$',stat,re.M)[1]
        assert exe in log
        if not evidence.exists():
            evidence.write_text(f'Independently observed running engine PID {pid}, /proc stat start_ticks {ticks[0]}, executable argv[0] {exe}, VmRSS {rss} kB when inspecting the first audited game. Official per-game memory rows are from the separate after-game reads.\n')
    ref=re.fullmatch(r'Independently observed running engine PID (\d+), /proc stat start_ticks (\d+), executable argv\[0\] (\S+), VmRSS (\d+) kB when inspecting the first audited game\. Official per-game memory rows are from the separate after-game reads\.\n',evidence.read_text())
    assert ref and ref[1]==pid and ref[2]==ticks[0] and ref[3] in log and int(ref[4])>0,(name,pid,ref)
class Stream:
    def __init__(self,name,first):
        self.name=name;self.base=RAW/name;self.first=first;self.pid=None;self.c=Counter()
        self.hash=hashlib.sha256();self.rawhash=hashlib.sha256();self.game_rows=[];self.na_rows=[];self.rss=[]
        self.records=(self.base/'records.txt').open('rb')
        self.raw=(MATCH/'raw-last'/(name+'.txt')).open('rb')
        self.receipts=(self.base/'games.tsv').open('rb')
        self.header=self.receipts.readline().decode().strip().split('\t')
        assert self.header[:4]==['book_line','plies','result','termination'],(name,self.header)
        self.held=None
    def peek(self):
        if self.held is not None:return self.held
        offset=self.receipts.tell()
        line=self.receipts.readline()
        if not line.endswith(b'\n'):self.receipts.seek(offset);return None
        fields=line.decode().strip().split('\t')
        assert len(fields)==len(self.header)
        self.held=dict(zip(self.header,fields));return self.held
    def take(self):
        r=self.peek();assert r is not None
        self.held=None
        gid=int(r['book_line']);assert gid==self.first+len(self.game_rows)
        op,_=opening(gid);data=[];moves=[];ps=[0,0];pn=[0,0];nodes=na=0
        for j in range(int(r['plies'])):
            row=self.records.readline();raw=self.raw.readline()
            actual,p,m,n=decode(row)
            assert (actual,p)==(gid,len(op)+j),(self.name,gid,j,actual,p)
            assert raw.endswith(b'\n') and not raw.endswith(b'\r\n'),(self.name,gid,p)
            gfield,pfield,mfield,last=raw[:-1].split(b' ',3)
            assert (gfield,pfield,mfield)==(str(gid).encode(),str(p).encode(),m)
            if last==b'NA':assert n is None,(gid,p,n)
            else:
                assert last.startswith(b'info '),(gid,p,last)
                nums=re.findall(rb'(?:^|\s)nodes\s+([0-9]+)(?=\s|$)',last)
                assert len(nums)==1 and int(nums[0])==n,(gid,p,last,n)
                self.c['soft']+=last.startswith(b'info string softnodes nodes ')
            idx=p%2;ps[idx]+=1
            if n is None:
                na+=1;pn[idx]+=1;self.na_rows.append((gid,p,'White' if idx==0 else 'Black',r['p1_pid'],m.decode()))
            else:nodes+=n
            self.hash.update(row);self.rawhash.update(raw);data.append(row);moves.append(m)
        assert replay(gid,tuple(moves))==(r['result'],r['termination']),(self.name,gid,r)
        for k,val in [('p1_search',ps[0]),('p2_search',ps[1]),('p1_na',pn[0]),('p2_na',pn[1]),('na',na),('nodes',nodes),('record_bytes',self.records.tell()),('slot',1)]:
            assert int(r[k])==val,(self.name,gid,k,r[k],val)
        assert r['p1_pid']==r['p2_pid']
        if self.pid is None:
            self.pid=r['p1_pid']
            if self.name.startswith('L1-'):
                check_lifetime(self.name,self.pid,(self.base/'run.log').read_text())
        assert r['p1_pid']==self.pid
        blob=b''.join(data)
        self.c.update(records=len(data),na=na,nodes=nodes,bytes=len(blob))
        self.game_rows.append((self.name,gid,len(data),na,nodes,len(blob),hashlib.sha256(blob).hexdigest(),r['result'],r['termination'],self.records.tell()))
        return gid,data
    def finish(self):
        assert self.peek() is None and not self.records.read(1) and not self.raw.read(1),self.name
        log=(self.base/'run.log').read_text();self.status=status(self.base/'run.log')
        assert self.status in ('COMPLETE','CUT_MINUTE40','INCOMPLETE'),(self.name,self.status)
        for k,val in dict(games=len(self.game_rows),records=self.c['records'],sum_nodes=self.c['nodes'],na_records=self.c['na'],records_sha256=self.hash.hexdigest()).items():
            assert re.findall(r'^'+k+r' (\S+)$',log,re.M)==[str(val)],(self.name,k,val)
        for mode in ('loaded','active'):
            assert any('NNUE v3 '+mode in l and 'checksum 30ab43b4ba5db5f3' in l for l in log.splitlines())
        assert not re.search(r'unknown option|invalid value',log,re.I)
        baseline=dict(s[len('setoption name '):].rsplit(' value ',1) for s in (WORK/'j7base/pc20.txt').read_text().splitlines())
        baseline['NNUEArch']='true'
        if self.name=='C22':baseline['LmrQuietBase']='60'
        actual=dict(re.findall(r'(?:^| )setoption name (.+?) value (.*)$',log,re.M))
        assert all(actual.get(k)==v for k,v in baseline.items()),(self.name,actual,baseline)
        assert Path(actual['NNUEArchFile']).name=='net768.nnue'
        op_rows=rows(self.base/'openings.tsv')
        assert all(tuple(r['moves'].split())==opening(int(r['game']))[0] for r in op_rows)
        assert [int(r['game']) for r in op_rows][:len(self.game_rows)]==[r[1] for r in self.game_rows]
        marked=[(int(r['book_line']),int(r['ply']),r['side'],r['engine_pid'],r['bestmove']) for r in rows(self.base/'no-info.tsv')]
        assert marked==self.na_rows
        self.rss,self.ticks=memory(self,log)
        self.records.close();self.raw.close();self.receipts.close()
        return (self.name,self.status,len(self.game_rows),self.first,self.first+len(self.game_rows)-1,self.c['records'],self.c['na'],self.c['nodes'],self.c['bytes'],self.hash.hexdigest(),self.pid,self.ticks)
def memory(s,log):
    ticks=re.findall(r'^engine_start_ticks (\d+)$',log,re.M)
    pid=re.findall(r'^P1_Both pid (\d+) child_cpu_affinity \[(\d+)\]$',log,re.M)
    assert len(ticks)==len(pid)==1 and s.pid==pid[0][0]
    cpu=pid[0][1];s.cpu=int(cpu)
    assert f'nproc 5 S 1 logical_cpu {cpu} python_chess {chess.__version__}' in log.splitlines()
    allmem=rows(s.base/'rss-all.tsv')
    milestones=rows(s.base/'rss.tsv')
    literal=(s.base/'rss-source.txt').read_text().splitlines()
    assert len(allmem)==len(literal)==len(s.game_rows)
    for index,(r,raw) in enumerate(zip(allmem,literal),1):
        assert int(r['completed'])==index and int(r['game'])==s.first+index-1 and r['pid']==s.pid and r['start_ticks']==ticks[0]
        regex=r'^(\d+) (\d+) (\d+) (\S+) VmRSS:\s+(\d+) kB$'
        m=re.fullmatch(regex,raw);assert m and m.groups()==tuple(r[k] for k in ('completed','game','pid','observed_utc','vmrss_kb')),(s.name,r,raw)
        assert int(r['vmrss_kb'])>0 and datetime.fromisoformat(r['observed_utc']).tzinfo is not None
    expected={i for i in (1,1000,2000,3000,4000,len(allmem)) if 1<=i<=len(allmem)}
    assert milestones==[allmem[i-1] for i in sorted(expected)],(s.name,'milestone rows',milestones,expected)
    start_rows=re.findall(r'^game_start (\d+) (\S+) (\S+) (\d+)$',log,re.M)
    assert [int(r[0]) for r in start_rows][:len(s.game_rows)]==[r[1] for r in s.game_rows]
    assert all(r[3]==s.pid for r in start_rows)
    assert re.findall(r'^raw_last_sha256 (\S+)$',log,re.M)==[s.rawhash.hexdigest()]
    return [(s.name,*r.values()) for r in milestones],ticks[0]
def waitfiles(arm):
    p=RAW/arm
    while not all(x.is_file() and x.stat().st_size>0 for x in [p/'games.tsv',p/'run.log',MATCH/'raw-last'/(arm+'.txt')]):time.sleep(.3)
def write(stage,r,arms,totals,allgames,mem,diffs,detail,hints):
    out=HERE/stage;out.mkdir(exist_ok=True)
    table(out/'arms.tsv',ARM_HEAD,totals);table(out/'games.tsv',GAME_HEAD,allgames)
    table(out/'rss.tsv',RSS_HEAD,mem);table(out/'differences.tsv',('game','absolute_ply','left_plies','right_plies'),diffs)
    if not detail:detail=['No differing record in comparable completed games.']
    (out/'first-difference.txt').write_text('\n'.join(detail)+'\n')
    summary=[f'{stage} {r}',f'{len(diffs)} differing games.']+hints
    for name,state,games,lo,hi,n,na,nodes,nb,h,pid,ticks in totals:
        summary.append(f'{name} {state}, IDs {lo}–{hi}, {games} games, {n} records, {na} NA, {nodes} summed nodes, {nb} bytes, SHA256 {h}, PID {pid}, lifetime start_ticks {ticks}.')
    summary+=detail
    (out/'summary.txt').write_text('\n'.join(summary)+'\n')
    sig=out/'verified.tmp';sig.write_text(f'{stage} {r}; {len(diffs)} differing games.\n');sig.replace(out/'verified.txt');print(summary[0],flush=True)
def pair(stage):
    a,b,lo,hi=PAIR[stage]
    for name in (a,b):waitfiles(name)
    arms=[Stream(n,lo) for n in (a,b)]
    readrows=0;diffs=[];detail=[];out=HERE/stage;out.mkdir(exist_ok=True)
    while True:
        ready=[s.peek() is not None for s in arms]
        if all(ready):
            (g,l),(gid,r)=[s.take() for s in arms];assert g==gid
            if l!=r:
                ix=next(j for j,(x,y) in enumerate(zip_longest(l,r)) if x!=y);diffs.append((g,decode((l[ix:ix+1] or r[ix:ix+1])[0])[1],len(l),len(r)))
                if not detail:
                    detail=difference(stage,(a,b),g,l,r,readrows+1)
                    (out/'live-first-difference.txt').write_text('\n'.join(detail)+'\n')
            readrows+=len(l)
            continue
        if all(status(s.base/'run.log') for s in arms):
            if any(ready):raise ValueError((stage,'unequal ending game number',ready))
            break
        time.sleep(.2)
    totals=[s.finish() for s in arms]
    for s in arms:
        assert s.game_rows and s.game_rows[-1][1]<=hi
        if s.status=='COMPLETE':assert s.game_rows[-1][1]==hi
    cmp=subprocess.run(['cmp','-s',str(arms[0].base/'records.txt'),str(arms[1].base/'records.txt')]).returncode
    assert cmp==int(bool(diffs)),(stage,cmp,diffs[:1])
    if stage=='L1':assert arms[0].cpu!=arms[1].cpu
    hints=[f'Whole record-file cmp -s exit {cmp}. Both arms share the same final completed game ID. Nodes projected independently from every retained raw final info line. Seeded UCI opening history, legal moves, terminal position, per-color counts and durable game offsets verified. Every recorded VmRSS source matches its engine PID and process start ticks.']
    hints+= [f'{s.name}: {s.c["soft"]} records were taken from the final softnodes diagnostic.' for s in arms]
    write(stage,'DIFFERS' if cmp else 'IDENTICAL',arms,totals,[g for s in arms for g in s.game_rows],[m for s in arms for m in s.rss],diffs,detail,hints)
if __name__=='__main__':
    pair(sys.argv[1])
