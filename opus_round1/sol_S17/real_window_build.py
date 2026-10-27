"""Copy the LAST n rows of a real self-play shard (.pos, .hce, .txt, row for row) into a NEW stem, read-only on the
source, so a chronological real window can start shortly before a file boundary whose game continues.
Usage: python -I -B real_window_build.py <pos dir> <hce dir> <text dir> <stem> <n> <out dir> <new stem>"""
import collections,pathlib,sys
sys.dont_write_bytecode=True
pos,hce,txt=(pathlib.Path(a) for a in sys.argv[1:4]);stem,n,out,new=sys.argv[4],int(sys.argv[5]),pathlib.Path(sys.argv[6]),sys.argv[7]
with open(pos/f'{stem}.pos','rb') as f:
    h=f.read(16);N=int.from_bytes(h[8:16],'little');assert h[:4]==b'FPOS' and 0<n<=N;a=N-n
    f.seek(16+32*a);boards=f.read(32*n);f.seek(16+32*N+2*a);scores=f.read(2*n);f.seek(16+34*N+a);metas=f.read(n)
with open(hce/f'{stem}.hce','rb') as f:
    h=f.read(16);assert h[:4]==b'FHCE' and int.from_bytes(h[8:16],'little')==N;f.seek(16+2*a);hces=f.read(2*n)
tail=collections.deque(maxlen=n);count=0
with open(txt/f'{stem}.txt','rb') as f:
    for line in f:tail.append(line);count+=1
assert count==N and len(tail)==n,(count,N)
head=lambda magic:magic+(1).to_bytes(4,'little')+n.to_bytes(8,'little')
with open(out/f'{new}.pos','xb') as f:f.write(head(b'FPOS')+boards+scores+metas)
with open(out/f'{new}.hce','xb') as f:f.write(head(b'FHCE')+hces)
with open(out/f'{new}.txt','xb') as f:f.writelines(tail)
print(f'{new}: rows {a}..{N-1} of {stem} ({n} rows)')
