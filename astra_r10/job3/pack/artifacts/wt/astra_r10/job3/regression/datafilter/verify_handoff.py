"""Read-only independent handoff accounting. UNPROVEN strength."""
import argparse
import hashlib
import json
from pathlib import Path
from filter_positions import sha256, low_priority
from clear_holdouts import EXPECTED_HOLDOUTS

def verify_payload(item):
    h=hashlib.sha256(); count=0
    with open(item['path'],'rb') as fh:
        for line in fh:
            h.update(line); count+=1
    if h.hexdigest()!=item['sha256']: raise ValueError('payload hash mismatch')
    if count!=item['rows']: raise ValueError('payload row count mismatch')
    return count

def verify(path):
    manifest=json.loads(Path(path).read_text(encoding='utf-8'))
    if manifest['strength']!='UNPROVEN': raise ValueError('invalid strength claim')
    for name in ('train','metadata','validation','sample'):
        verify_payload(manifest[name])
    if manifest['train']['rows']!=manifest['metadata']['rows'] or manifest['train']['sha256']!=manifest['metadata']['sha256']:
        raise ValueError('metadata alignment mismatch')
    if Path(manifest['sample']['path']).stat().st_size>20*10**6: raise ValueError('sample over 20 MB')
    for p,h in manifest['runtime']['files'].items():
        if sha256(p)!=h: raise ValueError('runtime hash mismatch: '+p)
    for source in manifest['cohort']['sources']:
        if sha256(source['path'])!=source['sha256']: raise ValueError('source hash mismatch')
    holds=manifest['holdouts']
    if len(holds)!=2 or {h['shard'] for h in holds}!=set(EXPECTED_HOLDOUTS):
        raise ValueError('incomplete holdouts')
    for h in holds:
        if (h['sha256'],h['rows'])!=EXPECTED_HOLDOUTS[h['shard']] or sha256(h['path'])!=h['sha256']:
            raise ValueError('holdout pin mismatch')
    clearance=manifest['clearance']
    if sha256(clearance['path'])!=clearance['sha256']: raise ValueError('clearance hash mismatch')
    receipt=json.loads(Path(clearance['path']).read_text())
    if receipt['status']!='PASS' or receipt['remaining_overlap_unique_keys']!=0:
        raise ValueError('holdout clearance failed')
    if receipt['selection']['records_sha256']!=manifest['train']['sha256'] or receipt['selection']['kept']!=manifest['train']['rows']:
        raise ValueError('clearance selection mismatch')
    if not manifest['training_ready'] or manifest['pearson_stm_score_result']<=0.1:
        raise ValueError('training readiness/sign audit failed')
    return dict(status='PASS',training_rows=manifest['train']['rows'],validation_rows=manifest['validation']['rows'],
                sample_rows=manifest['sample']['rows'],sample_bytes=Path(manifest['sample']['path']).stat().st_size,
                strength='UNPROVEN',manifest_sha256=sha256(path))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');a=p.parse_args();low_priority()
    print(json.dumps(verify(a.manifest),indent=2))
