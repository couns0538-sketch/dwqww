from pathlib import Path
import csv,time,sys,subprocess
from runstage import HERE,RAW,CASES,tsv,dump_tsv
def index():
    records=[]
    for stage in CASES:
        out=HERE/stage
        if (out/'verified.txt').is_file():records.extend(tsv(out/'score.tsv'))
    if records:
        dump_tsv(HERE/'stage-summary.tsv',list(records[0]),[r.values() for r in records])
    if any(r['match']=='B1' for r in records):
        b=next(r for r in records if r['match']=='B1')
        text=f'{b["reading"]}. B1 {"complete" if b["status"]=="complete" else "cut"}, {b["scored_games"]} scored games, {b["complete_pairs"]} whole pairs, paired Elo {b["elo"]} [{b["lower95"]}, {b["upper95"]}]. Only B1 decides the bundle.\n'
        for d in records:
            if d['match']=='B2':text+=f'B2 {"complete" if d["status"]=="complete" else "cut"}, description only, {d["scored_games"]} games, Elo {d["elo"]} [{d["lower95"]}, {d["upper95"]}].\n'
        (HERE/'reading.txt').write_text(text)
def main():
    for stage in CASES:
        if (HERE/stage/'verified.txt').is_file():index();continue
        meta=RAW/(stage+'.meta')
        while not (meta.is_file() and any(' '+stage+' end' in s for s in meta.read_text().splitlines())):time.sleep(1)
        with (HERE/(stage+'-audit.log')).open('w') as f:
            subprocess.run([sys.executable,'-B',str(HERE/'runstage.py'),stage],stdout=f,stderr=f,check=True)
        index()
if __name__=='__main__':main()
