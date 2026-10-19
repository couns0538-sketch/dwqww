from pathlib import Path
import collections,hashlib,json
work=Path(__file__).resolve().parent;root=work.parents[1];out=work/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
config=json.loads((out/'config.json').read_text());final=json.loads((out/'final.json').read_text());receipt=json.loads((out/'receipt.json').read_text())
assert receipt['complete']is True and receipt['records']==config['spec']['expectedRecords']==2
assert receipt['finalSha256']==sha(out/'final.json')and receipt['configSha256']==final['configSha256']==sha(out/'config.json')
corpus=root/'diagnostics/quiet-sort11/evidence/phases.ndjson'
assert sha(corpus)==config['spec']['corpusSha256']=='70be6fca5a3946fa4d3cac80cb34e96284838d5623e6adf0239a9cda39d91571'
source=[json.loads(l)for l in corpus.open()];assert len(source)==16336 and sum(len(r['source'])for r in source)==462831
assert [p.name for p in sorted((out/'records').iterdir())]==['000000.json','000001.json']
for i,iteration in enumerate([15,16]):
    record=json.loads((out/f'records/{i:06d}.json').read_text())
    assert record==final['records'][i]and sha(out/f'records/{i:06d}.json')==final['recordHashes'][i]
    assert record['iteration']==iteration and record['phases']==16336 and record['items']==462831
    assert record['sourceSha256']==sha(root/f'staged/iteration-{iteration}/candidate/search/movepicker.js')
    stream=out/f'source{iteration}.ndjson';assert sha(stream)==record['streamSha256']
    rows=[json.loads(l)for l in stream.open()];assert len(rows)==16336;totals=collections.Counter()
    for j,(row,original)in enumerate(zip(rows,source)):
        n=len(original['source']);scores=original['scores']
        assert row['id']==j and row['items']==n
        for k,v in row.items():
            assert type(v)is int and v>=0
            if k not in ['id','items']:totals[k]+=v
        ordered=all(a>=b for a,b in zip(scores,scores[1:]))
        sort_items=n if iteration==15 else sum(score!=0 for score in scores)
        native=sort_items>=32 and not ordered
        assert row['nativeSortCalls']==int(native)
        assert row['nativeSortItems']==(sort_items if native else 0)
    assert dict(totals)==record['totals']
a,b=[r['totals']for r in final['records']];keys=[k for k in a if k not in ['nativeSortCalls','nativeSortItems']]
result={'status':'PASS','diagnosticOnly':True,'phasesPerSource':16336,'itemsPerSource':462831,
        'nativeSortCallsBeforeAfter':[a['nativeSortCalls'],b['nativeSortCalls']],
        'nativeSortItemsBeforeAfter':[a['nativeSortItems'],b['nativeSortItems']],
        'explicitIndexedTotals':[sum(r[k]for k in keys)for r in[a,b]],
        'limits':'Prefiltered quiet corpus only; native sort internals, allocation, geometry and history reads excluded. Not an NPS comparison.'}
assert result['nativeSortCallsBeforeAfter']==[5165,962]
assert result['nativeSortItemsBeforeAfter']==[187673,33479]
with(work/'independent-readback.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
