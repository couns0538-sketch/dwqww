"""Report each newly available game milestone or audit issue, without altering run evidence."""
import pathlib,time
from audit import HERE,RAW,STAGES,rows
seen=set()
while True:
    alerts=[]
    for f in [HERE/'monitor-status.txt',HERE/'phase-check.log']:
        if f.exists() and f.stat().st_size and f.name not in seen:
            seen.add(f.name);alerts.append(f.read_text()[-2500:])
    for name in STAGES[2:]:
        for signal in ('live-first-difference.txt','verified.txt'):
            f=HERE/name/signal
            if f.is_file() and f not in seen:
                seen.add(f);alerts.append(f'{name} '+f.read_text().strip())
                if signal=='verified.txt':alerts.append((f.parent/'arms.tsv').read_text())
    a=RAW/'L1-r15d'/'rss-all.tsv';b=RAW/'L1-kF'/'rss-all.tsv'
    if a.is_file() and b.is_file():
        left=rows(a);right=rows(b);n=min(len(left),len(right))
        for tick in range(1000,5001,1000):
            if n>=tick and tick not in seen:
                seen.add(tick);alerts.append(f'L1 at {tick}: r15d {left[tick-1]["vmrss_kb"]} and kF {right[tick-1]["vmrss_kb"]} kB')
    for a in alerts:print(a,flush=True)
    if (HERE/'memory-prediction.tsv').is_file():
        print((HERE/'reading.txt').read_text(),(HERE/'memory-prediction.tsv').read_text(),flush=True);break
    time.sleep(5)
