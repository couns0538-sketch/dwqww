"""Independently compare saved fastchess configuration, UCI preflight and actual engine traffic."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
W=Path('/workspace/work')
R=W/'j21match/results'
REVIEW=Path(__file__).resolve().parent
EXE=W/'j7patch/build/forge'
NET=W/'j7net/net768.nnue'
FC=W/'j8fast/source/fastchess'
PC=W/'j7base/pc20.txt'
EXPECTED={
 'C21':(7391,100,[10000,20000],[(0,'false'),(0,'false')]),
 'B1':(7392,600,[20000,20000],[(2,'true'),(0,'false')]),
 'B2':(7393,600,[2000,2000],[(2,'true'),(0,'false')])}
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    a=argparse.ArgumentParser()
    a.add_argument('stage',choices=EXPECTED)
    a.add_argument('--live',action='store_true')
    args=a.parse_args();stage=args.stage
    assert digest(PC)=='2c4785517c8eb7a47ac39d282bc3917f77a5d0264c18b7898036e4abbefe6d5f'
    assert digest(EXE)=='ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e'
    assert digest(NET)=='c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
    assert digest(FC)=='202c09fc8291eb7b4d6b946b44448d0d9c9ee481b04243f06fa7158c45689270'
    seed,rounds,limits,variants=EXPECTED[stage]
    pc=dict(re.fullmatch(r'setoption name (\S+) value (\S+)',l).groups() for l in PC.read_text().splitlines())
    common=pc | {'NNUEArchFile':str(NET),'NNUEArch':'true'}
    opts=lambda vals: {'NullMateGuard':str(vals[0]),'NullThreatVerify':vals[1]} | common
    fp=R/f'{stage}-config.json'
    if args.live and not fp.exists():fp=R/'config.json'
    cfg=json.loads(fp.read_text())
    assert cfg['seed']==seed and cfg['concurrency']==4 and cfg['games']==2 and cfg['rounds']==rounds
    assert not cfg['noswap'] and not cfg['reverse']
    assert not any(cfg[k]['enabled'] for k in ('draw','resign','tb_adjudication','sprt'))
    assert cfg['maxmoves']=={'enabled':True,'move_count':300}
    assert cfg['opening']['order']==0 and cfg['opening']['format']==0
    book=W/f'j21book/{stage}.epd'
    assert cfg['opening']['file']==str(book)
    receipt=(book.parent/f'{stage}-opening-preflight.txt').read_text()
    assert re.search(r'^derived_sha256 '+digest(book)+'$',receipt,re.M)
    text=(R/f'{stage}.meta').read_text()
    command=shlex.split(next(l[8:] for l in text.splitlines() if l.startswith('command ')))
    assert command[0]==str(FC) and command.count('-repeat')==1
    assert not {'-draw','-resign','-srandtime','-tb'} & set(command)
    def val(name):return command[command.index(name)+1]
    assert [int(val(k)) for k in ('-concurrency','-srand','-rounds','-games','-maxmoves')]==[4,seed,rounds,2,300]
    assert val('-openings')=='file='+str(book) and 'order=random' in command and 'format=epd' in command
    assert [e['name'] for e in cfg['engines']]==[stage+'-A',stage+'-B']
    engine_args=[]
    for k in range(2):
        i=command.index('-engine') if k==0 else command.index('-engine',command.index('-engine')+1)
        e=command.index('-engine',i+1) if k==0 else command.index('-each',i+1)
        engine_args.append(dict(x.split('=',1) for x in command[i+1:e]))
    each=dict(x.split('=',1) for x in command[command.index('-each')+1:command.index('-openings')])
    raw=W/f'j21match/{stage}-uci.log'
    with raw.open('rb') as f: prefix=f.read(2*1024*1024).decode('ascii',errors='replace').splitlines()
    print(f'{stage}: seed {seed}, {rounds} paired openings, four concurrent games, reversed colors, maxmoves 300. Controller config SHA-256 {digest(fp)}.')
    for i,(role,engine,valpair,hard) in enumerate(zip('AB',cfg['engines'],variants,limits)):
        expect=opts(valpair)
        assert len(engine['options'])==len(expect)==26 and dict(engine['options'])==expect
        assert engine['cmd']==str(EXE) and engine['dir']==str(EXE.parent)
        assert engine['limit']['nodes']==hard and engine['limit']['plies']==0 and not any(engine['limit']['tc'].values())
        effective=engine_args[i] | each
        assert {key[7:]:v for key,v in effective.items() if key.startswith('option.')}==expect
        assert int(effective['nodes'])==hard and effective['proto']=='uci'
        assert effective['cmd']==str(EXE) and effective['name']==stage+'-'+role
        manual=text.split(f'{role} preflight input\n',1)[1].split(f'{role} preflight output\n',1)[0].splitlines()
        assert manual==['uci',*[f'setoption name {k} value {v}' for k,v in common.items()],*[f'setoption name {k} value {v}' for k,v in list(expect.items())[:2]],'isready','quit']
        responses=text.split(f'{role} preflight output\n',1)[1].split(f'{role} preflight PASS',1)[0]
        assert f'{role} preflight PASS' in text and 'readyok' in responses.splitlines() and 'uciok' in responses.splitlines()
        assert 'option name NullMateGuard type spin default 0 min 0 max 2' in responses and 'option name NullThreatVerify type check default false' in responses
        assert not re.search(r'unknown option|invalid value|\bERROR\b',responses,re.I)
        label=f'{stage}-{role}'
        from collections import defaultdict
        actual=defaultdict(dict)
        go=defaultdict(set)
        active=set()
        loaded=set()
        for line in prefix:
            m=re.search(rf'<\s*(\d+)>\s+{label} <--- setoption name (\S+) value (.+)$',line)
            if m and m[2] in expect:
                assert m[3]==expect[m[2]]
                actual[m[1]][m[2]]=m[3]
            g=re.search(rf'<\s*(\d+)>\s+{label} <--- (go .+)$',line)
            if g:go[g[1]].add(g[2])
            net=re.search(rf'<\s*(\d+)>\s+{label} ---> info string NNUE v3 (loaded|active): .*checksum 30ab43b4ba5db5f3\b',line)
            if net:(loaded if net[2]=='loaded' else active).add(net[1])
        assert len(actual)==4 and set(actual)==active==loaded==set(go), (label,actual.keys(),active,loaded,go)
        assert all(options==expect for options in actual.values())
        assert all(received=={f'go nodes {hard}'} for received in go.values())
        print(f'  {label}. All 26 options matched in the fastchess argv, {fp.name}, manual UCI preflight and actual engine traffic on all four controller threads (initial 2 MiB). NullMateGuard={valpair[0]} NullThreatVerify={valpair[1]} Threads=1 Hash=16 OwnBook=false NNUEArch=true. Every thread recorded go nodes {hard} and both loaded and active checksum 30ab43b4ba5db5f3.')
    if not args.live:
        live=(R/f'{stage}-live-options.txt').read_text()
        assert live.endswith('match_refusal false\n') and not re.search(r'unknown option|invalid value|\bERROR\b',live,re.I)
        assert 'status ended' in text or 'status incomplete; minute 50' in text
        print('  Final live refusal monitor reported false.')
if __name__=='__main__':main()
