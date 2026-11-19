"""Materialize complete Job 23 game evidence, with whole-line parts for large files."""
import argparse
import csv
import hashlib
from pathlib import Path
import shutil

from selfplay import RESULTS, ROOT, sha

LIMIT=20_000_000
PART=15_000_000


def write_stream(source, target, stem):
    split=source.stat().st_size>LIMIT
    digest=hashlib.sha256()
    size=rows=0
    with (target/(stem+'-manifest.tsv')).open('x',encoding='ascii',newline='') as f:
        index=csv.writer(f,delimiter='\t',lineterminator='\n')
        index.writerow(('kind','file','bytes','rows','sha256'))
        block=bytearray()
        part=0
        def flush():
            nonlocal part
            part+=1
            name=f'{stem}.part{part:04d}.txt' if split else stem+'.txt'
            path=target/name
            with path.open('xb') as out: out.write(block)
            checksum=hashlib.sha256(block).hexdigest()
            if sha(path)!=checksum: raise ValueError('published part changed')
            index.writerow(('part',name,len(block),block.count(b'\n'),checksum))
            block.clear()
        with source.open('rb') as raw:
            for line in raw:
                if not line.endswith(b'\n') or b'\x00' in line or len(line)>PART:
                    raise ValueError(f'{source}: partial or invalid text row')
                line.decode('ascii')
                if split and block and len(block)+len(line)>PART: flush()
                digest.update(line)
                block.extend(line)
                rows+=1;size+=len(line)
        if block or not part: flush()
        if sha(source)!=digest.hexdigest(): raise ValueError('source changed during archive')
        index.writerow(('whole',stem+'.txt',size,rows,digest.hexdigest()))
    return rows,size


def archive(arm,dest):
    src=RESULTS/arm
    target=dest/arm
    target.mkdir(parents=True,exist_ok=False)
    with (src/'games.tsv').open() as f:
        games=list(csv.DictReader(f,delimiter='\t'))
    if not games: raise ValueError('no complete games')
    if any(int(r['book_line'])!=700001+i for i,r in enumerate(games)): raise ValueError('game gap')
    if len({(r['p1_pid'],r['p2_pid']) for r in games})!=1 or games[0]['p1_pid']!=games[0]['p2_pid']:
        raise ValueError('engine lifetime changed')
    for kind,file in (('records',src/'records.txt'),('raw-last',ROOT/'raw-last'/f'{arm}.txt')):
        rows,size=write_stream(file,target,kind)
        if rows!=sum(int(r['plies']) for r in games): raise ValueError(f'{kind}: row count')
        if kind=='records' and size!=int(games[-1]['record_bytes']): raise ValueError('uncommitted records')
    for p in src.iterdir():
        if p.name!='records.txt' and p.is_file(): shutil.copyfile(p,target/p.name)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    parser.add_argument('arms',nargs='+')
    args=parser.parse_args()
    for label in args.arms: archive(label,args.destination)
