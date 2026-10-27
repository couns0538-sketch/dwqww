"""For every consecutive pair of real self-play text shards, does the last game of one continue into the next?
Sol's rule on the edge lines only (fullmove decrease, piece-count increase or result change = new game). Read-only."""
import pathlib
T=pathlib.Path('D:/grok-pc-data/selfplay_out');R={'0.0':0,'0.5':1,'1.0':2}
def ctx(line):
    p=line.split('|');f=p[0].split();return int(f[5]),sum(c.isalpha() for c in f[0]),R[p[2].strip()]
def first(p):
    with open(p,encoding='utf-8') as s:return s.readline()
def last(p):
    with open(p,'rb') as f:
        f.seek(-4096,2);return f.read().decode('utf-8').splitlines()[-1]
files=sorted(T.glob('forge_selfplay_0[0-3][0-9].txt'))
for a,b in zip(files,files[1:]):
    x,y=ctx(last(a)),ctx(first(b));new=y[0]<x[0] or y[1]>x[1] or y[2]!=x[2]
    print(f'{a.stem}->{b.stem}: last {x} first {y} -> {"new game" if new else "CONTINUES"}')
