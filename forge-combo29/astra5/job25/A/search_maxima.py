"""After the prediction, extract each search's highest nodes field across all info lines."""
import argparse
import csv
from pathlib import Path
import re


def run(directory):
    raw=(directory/'uci.log').read_text().splitlines(); index=directory/'searches.tsv'
    with index.open(newline='') as f,(directory/'maxima.tsv').open('x',newline='') as out:
        writer=csv.writer(out,delimiter='\t',lineterminator='\n');writer.writerow(['position','repeat','largest_nodes','max_raw_line','info_lines_with_nodes','within60','legal'])
        for row in csv.DictReader(f,delimiter='\t'):
            low,high=int(row['first_raw_line']),int(row['last_raw_line']); found=[]
            for i in range(low-1,high):
                stamp,direction,line=raw[i].split(' ',2)
                if direction!='<' or not line.startswith('info '):continue
                nodes=re.search(r'\bnodes (\d+)\b',line)
                if nodes:found.append((int(nodes[1]),i+1))
            maximum=max(v for v,_ in found) if found else 'NA'
            first=next((i for v,i in found if v==maximum),'NA')
            writer.writerow([row['position'],row['repeat'],maximum,first,len(found),row['within60'],row['legal']])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='+',type=Path)
    for d in p.parse_args().directory:run(d)
