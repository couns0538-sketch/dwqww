"""Read-only independent handoff accounting. UNPROVEN strength."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from filter_positions import sha256, low_priority
from clear_holdouts import EXPECTED_HOLDOUTS

HERE=Path(__file__).resolve().parent
REVIEWABLE_RUNTIME={str((HERE/name).resolve()) for name in ('train_adapter.py','records.py')}
EXPECTED_RECIPES={'filtered_eval_v1':{'selfplay_known_lambda':1.0,'other_lambda':1.0},
                  'filtered_wdl_v1':{'selfplay_known_lambda':0.8,'other_lambda':1.0}}
EXPECTED_HYPERPARAMETERS={'features':'K32H3^','L1':1024,'batch_size':16384,
                         'epoch_size':152500000,'epochs':8,'lr':0.000875,'gamma':0.72,'seed':5108}

def verify_payload(item):
    h=hashlib.sha256(); count=0
    with open(item['path'],'rb') as fh:
        for line in fh:
            h.update(line); count+=1
    if h.hexdigest()!=item['sha256']: raise ValueError('payload hash mismatch')
    if count!=item['rows']: raise ValueError('payload row count mismatch')
    return count

def verify(path, *, allow_runtime_changes=()):
    """Default: strict admission. Overrides are only for reviewed historical-data reuse.

    The refresher hard-pins its prior manifest before allowing the two owned
    normalization/admission modules to change. No installed npt or native file
    can be exempted; a newly published manifest always passes strict verification.
    """
    manifest=json.loads(Path(path).read_text(encoding='utf-8'))
    required={'schema','strength','train','metadata','validation','sample','runtime','cohort',
              'holdouts','clearance','training_ready','pearson_stm_score_result',
              'baseline_wrapper','recipes','hyperparameters','known_result_count'}
    if not isinstance(manifest,dict) or not required <= manifest.keys():
        raise ValueError('incomplete handoff manifest')
    if manifest['schema']!=1:raise ValueError('unsupported manifest schema')
    if manifest['strength']!='UNPROVEN': raise ValueError('invalid strength claim')
    correlation=manifest['pearson_stm_score_result']
    if (type(correlation) not in (int,float) or not math.isfinite(correlation)
            or not 0.1 < correlation <= 1.0 or manifest['training_ready'] is not True):
        raise ValueError('training readiness/sign audit failed')
    if manifest['recipes']!=EXPECTED_RECIPES or manifest['hyperparameters']!=EXPECTED_HYPERPARAMETERS:
        raise ValueError('manifest recipe differs from the fixed training command')
    allowed={str(Path(p).resolve()) for p in allow_runtime_changes}
    if not allowed <= REVIEWABLE_RUNTIME:raise ValueError('runtime migration outside reviewed local modules')
    for name in ('train','metadata','validation','sample'):
        verify_payload(manifest[name])
    if manifest['train']['rows']!=manifest['metadata']['rows'] or manifest['train']['sha256']!=manifest['metadata']['sha256']:
        raise ValueError('metadata alignment mismatch')
    if Path(manifest['sample']['path']).stat().st_size>20*10**6: raise ValueError('sample over 20 MB')
    for p,h in manifest['runtime']['files'].items():
        if str(Path(p).resolve()) not in allowed and sha256(p)!=h:
            raise ValueError('runtime hash mismatch: '+p)
    for p,h in manifest.get('tooling',{}).items():
        if sha256(p)!=h:raise ValueError('tooling hash mismatch: '+p)
    wrapper=manifest['baseline_wrapper']
    if sha256(wrapper['path'])!=wrapper['sha256']:raise ValueError('baseline recipe wrapper changed')
    for source in manifest['cohort']['sources']:
        if sha256(source['path'])!=source['sha256']: raise ValueError('source hash mismatch')
    holds=manifest['holdouts']
    if len(holds)!=2 or {h['shard'] for h in holds}!=set(EXPECTED_HOLDOUTS):
        raise ValueError('incomplete holdouts')
    for h in holds:
        if h.get('complete_scan') is not True or (h['sha256'],h['rows'])!=EXPECTED_HOLDOUTS[h['shard']] or sha256(h['path'])!=h['sha256']:
            raise ValueError('holdout pin mismatch')
    clearance=manifest['clearance']
    if sha256(clearance['path'])!=clearance['sha256']: raise ValueError('clearance hash mismatch')
    receipt=json.loads(Path(clearance['path']).read_text())
    if receipt['status']!='PASS' or receipt['remaining_overlap_unique_keys']!=0:
        raise ValueError('holdout clearance failed')
    if receipt['selection']['records_sha256']!=manifest['train']['sha256'] or receipt['selection']['kept']!=manifest['train']['rows']:
        raise ValueError('clearance selection mismatch')
    if receipt['selection'].get('metadata_sha256')!=manifest['metadata']['sha256']:
        raise ValueError('clearance metadata mismatch')
    complete=receipt.get('complete_holdouts',[])
    expected={(str(Path(h['path']).resolve()),h['sha256'],h['rows']) for h in holds}
    observed={(str(Path(h['path']).resolve()),h['sha256'],h['rows']) for h in complete}
    if len(complete)!=2 or observed!=expected:raise ValueError('clearance complete holdout bindings mismatch')
    if type(manifest['known_result_count']) is not int or not 2 <= manifest['known_result_count'] <= manifest['train']['rows']:
        raise ValueError('invalid known-result count')
    return dict(status='PASS',training_rows=manifest['train']['rows'],validation_rows=manifest['validation']['rows'],
                sample_rows=manifest['sample']['rows'],sample_bytes=Path(manifest['sample']['path']).stat().st_size,
                strength='UNPROVEN',manifest_sha256=sha256(path))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');a=p.parse_args();low_priority()
    print(json.dumps(verify(a.manifest),indent=2))
