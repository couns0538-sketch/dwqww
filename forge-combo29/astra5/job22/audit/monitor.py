from pathlib import Path
import subprocess,sys,time
from audit import HERE,RAW,STAGES,rows,table,ARM_HEAD,RSS_HEAD
def index():
    summary=[];memory=[];d={}
    for n in STAGES:
        p=HERE/n
        if not (p/'verified.txt').exists():continue
        reading=(p/'summary.txt').read_text().splitlines()[0].split(' ',1)[1]
        ca=rows(p/'arms.tsv');d[n]=ca[0] if n=='L1' else ca[-1]
        diffs=len(rows(p/'differences.tsv'))
        summary.extend((n,reading,diffs,*r.values()) for r in ca)
        if n=='L1':memory.extend(r.values() for r in rows(p/'rss.tsv'))
    t=HERE/'stage-summary.tmp';table(t,['stage','reading','differing_games',*ARM_HEAD],summary);t.replace(HERE/'stage-summary.tsv')
    if memory:
        t=HERE/'memory.tmp';table(t,RSS_HEAD,memory);t.replace(HERE/'memory.tsv')
    if all(n in d for n in ('L1','L0-r15d','L0-kF')):
        reads={p:(HERE/p/'summary.txt').read_text().splitlines()[0].split(' ',1)[1] for p in ('L1','L0-r15d','L0-kF')}
        word='KEEPS' if list(reads.values())==['IDENTICAL','SAME','SAME'] else 'DIFFERS'
        l=d['L1']
        (HERE/'reading.txt').write_text(f'{word}. L1 {reads["L1"]} ({l["status"]}, {l["games"]} games per build ending at {l["last_game"]}). L0 r15d {reads["L0-r15d"]}; L0 kF {reads["L0-kF"]}. Memory is descriptive.\n')
def main():
    for s in STAGES:
        if not (HERE/s/'verified.txt').exists():
            command=['tail.py',s[3:]] if s.startswith('L0-') else ['audit.py',s]
            with (HERE/(s+'-audit.log')).open('w') as f:subprocess.run([sys.executable,'-Bu',str(HERE/command[0]),command[1]],stdout=f,stderr=f,check=True)
        index()
if __name__=='__main__':main()
