#!/usr/bin/env python3
"""Independent heap/stream recheck of every saved lane bound and manifest hash."""
from pathlib import Path
import hashlib
import heapq
import json
import re

base=Path('/workspace/forge-jobACD-20261025/forge_sol_jobACD_pack_20261025/03_nets')
out=Path('/workspace/forge-jobACD-net-audit-20261025/evidence')
evidence=json.loads((out/'forge_sol_accumulator_bounds_20261025.json').read_text())
checks=0
for net in evidence['nets']:
    data=(base/net['file']).read_bytes()
    assert hashlib.md5(data).hexdigest()==net['md5']
    assert hashlib.sha256(data).hexdigest()==net['sha256']
    text=data.decode('ascii')
    def values(name):
        body=re.search(r'\b'+name+r'\[\d+\]\s*=\s*\{(.*?)\};',text,re.S).group(1)
        return [int(token.group()) for token in re.finditer(r'[+-]?\d+',body)]
    weights=values('NnueW1');biases=values('NnueB1')
    assert len(weights)==768*256 and len(biases)==256
    columns=[[] for _ in range(256)]
    for offset,value in enumerate(weights):
        columns[offset%256].append(value)
    for lane,column in zip(net['per_lane'],columns):
        h=lane['lane'];bias=biases[h]
        for count in (32,64,768):
            lower=bias+sum(v for v in heapq.nsmallest(count,column) if v<0)
            upper=bias+sum(v for v in heapq.nlargest(count,column) if v>0)
            assert [lower,upper]==lane['refresh_prefix_bounds_q'][str(count)]
            checks+=2
        absolute=list(map(abs,column));maximum=max(absolute)
        total=abs(bias)
        for value in column:total+=abs(value)
        assert total+4*maximum==lane['full768_absolute_plus_dirty4_q']
        assert abs(bias)+sum(heapq.nlargest(32,absolute))+4*maximum==lane['top32_absolute_plus_dirty4_q']
        checks+=2
result={'status':'PASS','method':'Separately implemented heap selection and streaming absolute sum; reparsed every actual network','bounds_assertions':checks,'nets':len(evidence['nets']),'all_manifest_hashes_rechecked':True,'source_result_sha256':hashlib.sha256((out/'forge_sol_accumulator_bounds_20261025.json').read_bytes()).hexdigest(),'speed_or_strength_claim':False}
with (out/'forge_sol_accumulator_recheck_20261025.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result,indent=2))
