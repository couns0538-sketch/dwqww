"""Read the frozen point/range statements and compare against observed paired Elo."""
from pathlib import Path
import csv,re
here=Path(__file__).resolve().parent
pred=here.parent/'astra5/forge-combo29/astra5/job21/prediction.txt'
def grade():
    text=pred.read_text()
    matches=re.findall(r'^(B[12]),[^\n]*?I predict ([+-]?\d+(?:\.\d+)?) Elo.*?range of ([+-]?\d+(?:\.\d+)?) to ([+-]?\d+(?:\.\d+)?) Elo\.',text,re.M)
    assert [m[0] for m in matches]==['B1','B2']
    lines=[]
    for match,point,lo,hi in matches:
        c=here/match/'score.tsv'
        if not c.exists():continue
        with c.open() as f:r=next(csv.DictReader(f,delimiter='\t'))
        if not r['elo']:continue
        x,pt,l,h=map(float,(r['elo'],point,lo,hi))
        sign=lambda a:(a>0)-(a<0)
        lines.append(f'{match} {r["status"]}: predicted point {point}, range [{lo}, {hi}], observed paired Elo {x:+.8f}. Observed point in range: {l<=x<=h}. Predicted sign agrees: {sign(pt)==sign(x)}. Exact point met: {pt==x}.')
    if lines:(here/'prediction-check.txt').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':grade()
