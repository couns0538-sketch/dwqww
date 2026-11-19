"""Check actual Fastchess UCI traffic for both arms independently of preflight metadata."""
from collections import Counter
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
RAW=HERE.parent/'j21match'
def verify(stage,out):
    path=RAW/(stage+'-uci.log')
    node={'C21':(10000,20000),'B1':(20000,20000),'B2':(2000,2000)}[stage]
    state={k:{'go':Counter(),'guard':Counter(),'verify':Counter(),'loaded':0,'active':0} for k in ('A','B')}
    pat=re.compile(rb'>\s+'+stage.encode()+rb'-([AB]) (?:<---|--->) (.*)$')
    with path.open('rb') as f:
        for line in f:
            if b'unknown option' in line.lower() or b'invalid value' in line.lower():
                raise ValueError(line.decode('ascii','replace'))
            if not any(x in line for x in (b' go ',b'setoption name Null',b'NNUE v3 loaded',b'NNUE v3 active')):continue
            m=pat.search(line.rstrip())
            if not m:continue
            role=m[1].decode();msg=m[2];d=state[role]
            if msg.startswith(b'go '):
                d['go'][msg.decode()]+=1
            if msg.startswith(b'setoption name NullMateGuard value '):d['guard'][msg.split()[-1].decode()]+=1
            if msg.startswith(b'setoption name NullThreatVerify value '):d['verify'][msg.split()[-1].decode()]+=1
            if msg.startswith(b'info string NNUE v3 loaded:') or msg.startswith(b'info string NNUE v3 active:'):
                assert b'checksum 30ab43b4ba5db5f3' in msg
                d['loaded' if b'NNUE v3 loaded' in msg else 'active']+=1
    from audit import read
    games,_=read(RAW/'results'/(stage+'.pgn'),True)
    projected=Counter()
    for g in games:
        n=len(g['moves']);t=g['tags'];white0=(g['fen'].split()[1]=='w')
        w=n//2+int(white0 and n%2)
        projected[t['White']]+=w;projected[t['Black']]+=n-w
    complete='status complete\n' in (out/'pgn-audit.txt').read_text()
    lines=[]
    for i,role in enumerate('AB'):
        d=state[role];nv=(i==0 and stage!='C21')
        assert set(d['go'])=={f'go nodes {node[i]}'},(stage,role,d['go'])
        assert set(d['guard'])=={'2' if nv else '0'} and set(d['verify'])=={'true' if nv else 'false'},(stage,role,d)
        assert min(d['loaded'],d['active'])>0
        if complete:assert sum(d['go'].values())==projected[stage+'-'+role],(stage,role,d['go'],projected)
        lines.append(f'{stage}-{role}: {d["go"][f"go nodes {node[i]}"]} actual go nodes {node[i]} commands, {dict(d["guard"])} guard messages, {dict(d["verify"])} verify messages, {d["loaded"]} net loads and {d["active"]} net activations with checksum 30ab43b4ba5db5f3. No refusal line seen.')
    (out/'live-traffic.txt').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':
    import sys
    verify(sys.argv[1],HERE/sys.argv[1])
