"""Independent literal outcome oracle against original source text, not normalization."""
import argparse
import itertools
import json
from pathlib import Path
from filter_positions import low_priority

def run(root):
    manifest=json.loads((root/'cohort/manifest.json').read_text())
    oracle={('w','0'):-1,('b','0'):1,('w','0.5'):0,('b','0.5'):0,
            ('w','1'):1,('b','1'):-1,('w','?'):None,('b','?'):None}
    checked=[]
    with open(root/'cohort/million.jsonl',encoding='utf-8') as normalized:
        for source in manifest['sources']:
            with open(source['path'],encoding='utf-8-sig') as raw:
                for line_number,line in enumerate(raw,1):
                    if not line.strip() or line.lstrip().startswith('#'):continue
                    if len(checked)==1000:break
                    fen,score,result=[v.strip() for v in line.split('|')]
                    token={'0.0':'0','1.0':'1','*':'?','':'?'}.get(result,result)
                    expected=oracle[(fen.split()[1],token)]
                    row=json.loads(next(normalized))
                    assert row['fen']==fen and row['score_stm']==int(score)
                    assert row['result_stm']==expected and row['has_result']==(expected is not None)
                    assert Path(row['source'])==Path(source['path']) and row['source_row']==line_number
                    checked.append(dict(source=source['path'],source_row=line_number,fen=fen,
                                        raw_white_result=result,expected_stm=expected,score_stm=int(score)))
            if len(checked)==1000:break
    assert len(checked)==1000
    destination=root/'actual_source_orientation1000.json'
    with open(destination,'x',encoding='utf-8') as fh:
        json.dump(dict(status='PASS',rows=len(checked),cases=checked),fh,indent=1)
    return dict(status='PASS',rows=len(checked),output=str(destination))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();low_priority()
    print(json.dumps(run(a.root),indent=2))
