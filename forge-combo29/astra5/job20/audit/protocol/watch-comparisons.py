"""Audit every durable game against the original depth lines and compare build records as they arrive."""
import csv
from contextlib import ExitStack
from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import time

W=Path('/workspace/work')
J=W/'j20match'
R=J/'results'
OUT=Path(__file__).resolve().parent
END=datetime.fromisoformat('2026-11-19T01:54:30+00:00').timestamp()
# A second method based on the actual formatting lambda. Capture unchanged fields in three spans.
FULL=re.compile(rb'([0-9]+ [0-9]+ [a-h][1-8][a-h][1-8][nbrq]? info depth [0-9]+ seldepth [0-9]+ score (?:cp|mate) -?[0-9]+ nodes [0-9]+) nps [0-9]+( hashfull [0-9]+) time [0-9]+( pv(?: [a-h][1-8][a-h][1-8][nbrq]?| 0000)*\n)')
NA=re.compile(rb'[0-9]+ [0-9]+ [a-h][1-8][a-h][1-8][nbrq]? NA\n')
class Arm:
    def __init__(self,arm,stack):
        self.name=arm
        self.rows=stack.enter_context((R/arm/'games.tsv').open())
        self.raw=stack.enter_context((J/'raw-labels'/f'{arm}.txt').open('rb'))
        self.rec=stack.enter_context((R/arm/'records.txt').open('rb'))
        self.fields=self.rows.readline().rstrip('\n').split('\t')
        assert 'record_bytes' in self.fields
        self.games=self.plies=self.mate=self.na=0
        self.digest=hashlib.sha256()
        self.cache={}
    def read(self):
        while True:
            before=self.rows.tell()
            line=self.rows.readline()
            if not line.endswith('\n'):
                self.rows.seek(before);return
            row=dict(zip(self.fields,line.rstrip('\n').split('\t')))
            game=int(row['book_line'])
            delta=int(row['record_bytes'])-self.rec.tell()
            block=self.rec.read(delta)
            moves=block.splitlines(keepends=True)
            assert len(block)==delta and len(moves)==int(row['plies'])
            for record in moves:
                raw=self.raw.readline()
                if NA.fullmatch(raw): expect=raw;self.na+=1
                else:
                    parts=FULL.fullmatch(raw)
                    if not parts: raise ValueError(f'Unexpected raw format in {self.name}: {raw!r}')
                    expect=b''.join(parts.groups())
                    if b' score mate ' in expect:self.mate+=1
                if expect!=record:raise ValueError(f'Normalization disagreement in {self.name}:\nraw {raw!r}\nwant {expect!r}\ngot {record!r}')
            self.plies+=len(moves)
            self.games+=1
            self.digest.update(block)
            self.cache[game]=block
    def final(self):
        return f'{self.name}\t{self.games}\t{self.plies}\t{self.na}\t{self.mate}\t{self.digest.hexdigest()}'
def ready(arm):
    p=R/arm/'games.tsv'
    return p.exists() and p.stat().st_size and (R/arm/'records.txt').exists() and (J/'raw-labels'/f'{arm}.txt').exists()
def delay():
    if time.time()>=END or (R/'JOB-STOP.txt').exists(): raise SystemExit('Stopped by deadline or refusal')
    time.sleep(1.0)
def main():
    if 0 in os.sched_getaffinity(0): os.sched_setaffinity(0,{0})
    print('arm\tgames\trecords\tNA\tscore_mate\tsha256_normalized_records',flush=True)
    settings=[('K20',['K20-1','K20-2'],20),('C20',['C20'],20),('P1',['P1-r15d','P1-kF'],3000),('P2',['P2-r15d','P2-kF'],500),('P3',['P3-r15d','P3-kF'],100)]
    for stage,names,count in settings:
        while not all(ready(name) for name in names): delay()
        with ExitStack() as stack:
            arms=[Arm(name,stack) for name in names]
            matched=0
            while matched<count:
                for arm in arms: arm.read()
                common=set.intersection(*(set(arm.cache) for arm in arms))
                for g in sorted(common):
                    groups=[arm.cache.pop(g) for arm in arms]
                    if len(groups)==2 and groups[0]!=groups[1]:
                        a,b=groups
                        from itertools import zip_longest
                        first=next((x,y) for x,y in zip_longest(a.splitlines(),b.splitlines()) if x!=y)
                        path=OUT/f'{stage}-DIVERGENCE.txt'
                        path.write_text(f'Stage {stage} game {g}. First differing complete records\n'+'\n'.join((v or b'EOF').decode() for v in first)+'\n')
                        print(path.read_text(),flush=True)
                        raise SystemExit(5)
                    matched+=1
                if matched<count: delay()
            for arm in arms: print(arm.final(),flush=True)
            print(f'# {stage} checked all raw depth labels against source-format captures for {count} completed games per arm.'+(f' Both record files byte-identical.' if len(arms)==2 else ''),flush=True)

if __name__=='__main__':main()
