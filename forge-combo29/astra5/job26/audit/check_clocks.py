"""Regress the A/B versus White/Black distinction directly against accepted game receipts."""
import csv
import json
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=json.loads((p/'summary.json').read_text())
with (p/'game-readback.tsv').open() as f: games=list(csv.DictReader(f,delimiter='\t'))
n=len(games)
white=sum(int(g['W_final']) for g in games)
black=sum(int(g['B_final']) for g in games)
a=sum(int(g['W_final'] if g['White']=='A' else g['B_final']) for g in games)
b=sum(int(g['W_final'] if g['White']=='B' else g['B_final']) for g in games)
assert a+b==white+black
assert a==s['players']['A']['clock_total'] and b==s['players']['B']['clock_total']
assert n and a/n==s['players']['A']['mean_final_clock'] and b/n==s['players']['B']['mean_final_clock']
assert white/n==s['by_colour_mean_clock']['W'] and black/n==s['by_colour_mean_clock']['B']
for name,total in [('A',a),('B',b)]:
    searches=sum(int(g[name+'_searches']) for g in games)
    used=sum(int(g[name+'_used']) for g in games)
    forfeits=[f for f in s['time_losses'] if f[3]==name]
    assert total==6000*n+60*(searches-len(forfeits))-used+sum(f[5] for f in forfeits)
    print(name,'clock total',total,'mean',total/n,'searches',searches,'used',used,'forfeits',len(forfeits))
print('by color: White total',white,'mean',white/n,'Black total',black,'mean',black/n)
print('PASS: player totals match direct color-swapped receipts and game-clock conservation')
