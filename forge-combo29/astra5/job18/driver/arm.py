"""Launch both fixed slots and merge complete games in numeric order."""
import csv
import hashlib
from pathlib import Path
import subprocess
import sys
import time
from selfplay import slot_count, ARMS, HEADER, NA_HEADER, RESULTS, ROOT, sha, utc

def read_games(arm):
    found = {}
    for slot in range(1,slot_count(arm)+1):
        dest = RESULTS / arm / f'slot{slot}'
        if not (dest/'games.tsv').exists(): continue
        offset = 0
        with (dest/'games.tsv').open() as f, (dest/'records.txt').open('rb') as raw:
            for row in csv.DictReader(f,delimiter='\t'):
                if not row.get('end_utc',''):
                    continue
                number = int(row['book_line'])
                if number in found or int(row['slot']) != slot:
                    raise ValueError('duplicate or incorrectly assigned book line')
                stop = int(row['record_bytes'])
                data = raw.read(stop-offset)
                if len(data) != stop-offset: raise ValueError('receipt exceeds records file')
                offset = stop
                found[number] = (row,data)
    return found

def merge(arm):
    dest = RESULTS / arm
    data = read_games(arm)
    nodata = []
    for slot in range(1,slot_count(arm)+1):
        p = dest/f'slot{slot}'/'no-info.tsv'
        if p.exists():
            with p.open() as f:
                nodata.extend(row for row in csv.DictReader(f,delimiter='\t') if int(row['book_line']) in data)
    with (dest/'records.txt').open('xb') as rec, (dest/'games.tsv').open('x') as games, (dest/'no-info.tsv').open('x') as nas:
        w = csv.DictWriter(games,fieldnames=HEADER,delimiter='\t',lineterminator='\n')
        nw = csv.DictWriter(nas,fieldnames=NA_HEADER,delimiter='\t',lineterminator='\n')
        w.writeheader()
        nw.writeheader()
        nw.writerows(sorted(nodata,key=lambda r:(int(r['book_line']),int(r['ply']))))
        for number,(row,raw) in sorted(data.items()):
            lines = raw.splitlines()
            if len(lines)!=int(row['plies']) or any(s.split()[:2] != [str(number).encode(),str(ply).encode()] for ply,s in enumerate(lines,8 if ARMS[arm][-1]=="R" else 1)):
                raise ValueError('malformed book line or ply')
            rec.write(raw)
            row['record_bytes'] = rec.tell()
            w.writerow(row)
    return data

def run(arm):
    build,first,last,limit,v,driver = ARMS[arm]
    dest = RESULTS / arm
    dest.mkdir(parents=True)
    started = utc()
    outfiles=[]
    workers=[]
    try:
        for slot in range(1,slot_count(arm)+1):
            out=(dest/f'slot{slot}-controller.txt').open('x')
            outfiles.append(out)
            workers.append(subprocess.Popen([sys.executable,'-B',str(ROOT/'selfplay.py'),arm,str(slot)],stdout=out,stderr=subprocess.STDOUT))
        while any(p.poll() is None for p in workers):
            if any(p.returncode not in (0,None) for p in workers):
                for p in workers:
                    if p.poll() is None: p.terminate()
                break
            time.sleep(.1)
    finally:
        for p in workers:
            p.wait()
        for f in outfiles: f.close()
    data = merge(arm)
    opening=dest/'slot1'/'openings.tsv'
    if opening.exists(): (dest/'openings.tsv').write_bytes(opening.read_bytes())
    ok = all(p.returncode==0 for p in workers) and set(data)==set(range(first,last+1))
    with (dest/'run.log').open('x') as log:
        def note(*v): print(*v,file=log)
        note('start_utc',started)
        note('arm',arm,'build',build,'id_range',first,last,'go softnodes' if driver=='R' else 'go nodes',limit,'set',v,'driver',driver)
        note('nproc',subprocess.check_output(['nproc'],text=True).strip(),'S',slot_count(arm))
        for slot in range(1,slot_count(arm)+1):
            path = dest / f'slot{slot}' / 'run.log'
            note(f'BEGIN slot{slot} log')
            if path.exists(): log.write(path.read_text())
            else: note('missing slot log')
            note(f'END slot{slot} log')
        note('end_utc',utc())
        note('games',len(data))
        for key,col in [('records','plies'),('na_records','na'),('sum_nodes','nodes')]:
            note(key,sum(int(row[col]) for row,_ in data.values()))
        note('records_sha256',sha(dest/'records.txt'))
        note('status','COMPLETE' if ok else 'INCOMPLETE')
    print(arm, 'COMPLETE' if ok else 'INCOMPLETE', len(data),sha(dest/'records.txt'),flush=True)
    return 0 if ok else 3

if __name__=='__main__':
    sys.exit(run(sys.argv[1]))
