#!/usr/bin/env python3
"""analyze_terminal.py ASANJSONL : checks the job-3 predictions. Fails loudly on a parse miss."""
import json, sys, collections
recs=[json.loads(l) for l in open(sys.argv[1])]
POS=[]
for line in open('sets/terminal20.fens'):
    if line.strip(): POS.append(line.strip())
print("records %d, positions %d" % (len(recs), len(POS)))
bad=[]
bm=collections.Counter(); info_runs=0; non0000=[]
for r in recs:
    lines=[]
    f='evidence/asan/asan_%03d_%s.txt' % (r['idx'], r['go'].replace(' ',''))
    for l in open(f):
        l=l.rstrip('\n'); lines.append(l)
    got=[l for l in lines if l.startswith('bestmove')]
    if not got:
        bad.append((r['idx'],r['go'],'NO BESTMOVE LINE')); continue
    b=got[-1].split()
    if len(b)<2: bad.append((r['idx'],r['go'],'malformed %r'%got[-1])); continue
    bm[b[1]]+=1
    if b[1]!='0000': non0000.append((r['idx'],r['go'],got[-1],POS[r['idx']]))
    inf=[l for l in lines if l.startswith('info depth') or l.startswith('info string')]
    if inf: info_runs+=1
print("P1 bestmove values: %s   non-0000: %d" % (dict(bm), len(non0000)))
for n in non0000[:10]: print("  ", n)
print("P2 runs printing any info line: %d of %d" % (info_runs, len(recs)))
print("P5 non-zero / broken exits: %d" % sum(1 for r in recs if r.get('exit') not in (0,)))
for r in recs:
    if r.get('exit') not in (0,): print("  ", r['idx'], r['go'], r['exit'])
w=[r['wall_ms'] for r in recs if r['go']=='movetime 50']
w.sort()
if w: print("P4 movetime-50 wall ms: min %d median %d max %d  over 500ms: %d" % (w[0], w[len(w)//2], w[-1], sum(1 for x in w if x>500)))
if bad:
    print("MALFORMED RECORDS: %d" % len(bad))
    for x in bad[:10]: print("  ", x)
