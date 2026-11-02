"""Explicit holdout split stage, separate from opt-in filtering. UNPROVEN."""
import argparse
import hashlib
import json
from pathlib import Path
from filter_positions import low_priority, sha256, storage_guard

EXPECTED_HOLDOUTS = {
    '013': ('fa383b67aa30b8df79d5989b8fc5a92b5edf615fcfca0f1b46085c47600e17b9',10000000),
    '014': ('b2c8ec79a2f24b72d5c1a124a14f64cd46c04221ff405cb4409b755a75abbef0',6388575),
}

def key(fen):
    return ' '.join(fen.split()[:2])

def write_selection(source, output, blocked, publish=True):
    output=Path(output); partial=output.with_name(output.name+'.partial')
    if output.exists() or partial.exists(): raise FileExistsError(output)
    storage_guard(allowance=Path(source).stat().st_size*2+20*10**6)
    partial.mkdir()
    count=kept=0; exclusions=[]
    with open(source,encoding='utf-8') as inp, open(partial/'records.jsonl','x',encoding='utf-8',newline='\n') as records, open(partial/'metadata.jsonl','x',encoding='utf-8',newline='\n') as metadata:
        for line in inp:
            r=json.loads(line); count+=1
            if key(r['fen']) in blocked:
                exclusions.append({'source':r['source'],'source_row':r['source_row'],'fen':r['fen']})
            else:
                kept+=1; records.write(line); metadata.write(line)
    report=dict(input=count,kept=kept,holdout_excluded=count-kept,exclusions=exclusions,
                policy='explicit conservative board+STM holdout exclusion; no deduplication or other changes',
                records_sha256=sha256(partial/'records.jsonl'),metadata_sha256=sha256(partial/'metadata.jsonl'))
    assert count==kept+len(exclusions)
    with open(partial/'selection.json','x') as fh: json.dump(report,fh,indent=2)
    if publish: partial.rename(output)
    return report

def run(root):
    audit=json.loads((root/'independent_audit/audit.json').read_text())
    holdouts=audit.get('holdouts',[])
    if len(holdouts)!=2 or {h.get('shard') for h in holdouts} != set(EXPECTED_HOLDOUTS):
        raise ValueError('both pinned complete holdouts 013 and 014 are required')
    for h in holdouts:
        if h.get('complete_scan') is not True or (h.get('sha256'),h.get('rows'))!=EXPECTED_HOLDOUTS[h['shard']]:
            raise ValueError('holdout identity/count differs from pinned complete audit')
    source=root/'filtered_default/records.jsonl'
    expected=json.loads((root/'filtered_default/report.json').read_text())['hashes']['records.jsonl']
    if sha256(source)!=expected: raise ValueError('filtered source changed')
    selected_keys=set()
    with open(source,encoding='utf-8') as fh:
        for line in fh: selected_keys.add(key(json.loads(line)['fen']))
    blocked=set(); receipts=[]
    for holdout in audit['holdouts']:
        if not holdout['complete_scan']: raise ValueError('complete prior validation required')
        path=Path(holdout['path']); h=hashlib.sha256(); count=0; matches=[]
        with open(path,'rb') as fh:
            for line_no,raw in enumerate(fh,1):
                h.update(raw)
                line=raw.decode('utf-8-sig')
                if not line.strip() or line.lstrip().startswith('#'): continue
                count+=1
                # Entire exact file was already schema/board validated by independent_audit.
                fen=line.split('|',1)[0].strip(); k=key(fen)
                if k in selected_keys:
                    blocked.add(k); matches.append(dict(source_row=line_no,fen=fen,key=k))
        if h.hexdigest()!=holdout['sha256'] or count!=holdout['rows']:
            raise ValueError('holdout differs from complete validated scan')
        receipts.append(dict(path=str(path),sha256=h.hexdigest(),rows=count,matches=matches))
    destination=root/'holdout_cleared'
    staged=root/'holdout_cleared.partial'
    report=write_selection(source,destination,blocked,publish=False)
    if sha256(source)!=expected: raise ValueError('selection source changed before publication')
    remaining=set()
    with open(staged/'records.jsonl',encoding='utf-8') as fh:
        for line in fh: remaining.add(key(json.loads(line)['fen']))
    # The receipts enumerate every held-out key present in the original selection.
    # Remaining is a subset of original, so this proves zero complete-holdout overlap.
    assert remaining <= selected_keys and not remaining.intersection(blocked)
    clearance=dict(status='PASS',original_selection_sha256=expected,selection=report,
                   complete_holdouts=receipts,blocked_unique_keys=len(blocked),
                   remaining_overlap_unique_keys=0,proof='complete hash-bound intersection receipts; retained subset disjoint from their union')
    with open(staged/'clearance.json','x') as fh: json.dump(clearance,fh,indent=2)
    staged.rename(destination)
    return clearance

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    low_priority();storage_guard();print(json.dumps(run(a.root),indent=2))
