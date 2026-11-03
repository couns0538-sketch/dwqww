"""Read-only independent handoff accounting. UNPROVEN strength."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from filter_positions import sha256, low_priority
from clear_holdouts import EXPECTED_HOLDOUTS

HERE=Path(__file__).resolve().parent
APPROVED_PREVIOUS_SHA256='0b75136d5d3ead9881b8dc78f0b46ee55d918de499884272c790356f8001d4bb'
APPROVED_MANIFEST=HERE/'evidence/handoff_manifest.json'
MIN_MIRRORS=1000
TOOLING=('convert_forge.py', 'result_codec.py', 'filter_positions.py', 'pgn_input.py',
         'resource_policy.py', 'filter_lichess_rec.py', 'signcheck.py',
         'audit.py', 'audit_followup.py', 'audit_stm_roundtrip.py', 'audit_capture_cohort.py',
         'audit_raw_labels.py', 'independent_audit.py', 'clear_holdouts.py',
         'verify_handoff.py', 'refresh_handoff.py')
REVIEWABLE_RUNTIME={str((HERE/name).resolve()) for name in ('train_adapter.py','records.py','npt_adapter.py')}
EXPECTED_RECIPES={'filtered_eval_v1':{'selfplay_known_lambda':1.0,'other_lambda':1.0},
                  'filtered_wdl_v1':{'selfplay_known_lambda':0.8,'other_lambda':1.0}}
EXPECTED_HYPERPARAMETERS={'features':'K32H3^','L1':1024,'batch_size':16384,
                         'epoch_size':152500000,'epochs':8,'lr':0.000875,'gamma':0.72,'seed':5108}


def approved_runtime():
    """Recover the complete installed-runtime contract from the immutable first handoff."""
    payload=APPROVED_MANIFEST.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=APPROVED_PREVIOUS_SHA256:
        raise ValueError('approved runtime contract manifest changed')
    return json.loads(payload)['runtime']


def verify_runtime(runtime, allowed):
    expected=approved_runtime()
    if not isinstance(runtime,dict) or runtime.keys()!=expected.keys():
        raise ValueError('incomplete runtime identity')
    if any(runtime[key]!=value for key,value in expected.items() if key!='files'):
        raise ValueError('runtime versions differ from the approved contract')
    files=runtime['files']
    if not isinstance(files,dict) or not files:
        raise ValueError('missing runtime file identities')
    observed={}
    for path,digest in files.items():
        if (not isinstance(path,str) or not path or '\x00' in path
                or not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest)):
            raise ValueError('invalid runtime file identity')
        resolved=Path(path).resolve()
        if resolved in observed:
            raise ValueError('duplicate resolved runtime file')
        observed[resolved]=(path,digest)
    pinned={Path(path).resolve():digest for path,digest in expected['files'].items()}
    if observed.keys()!=pinned.keys():
        raise ValueError('runtime file set differs from the approved contract')
    local={Path(path).resolve() for path in REVIEWABLE_RUNTIME}
    exempt={Path(path).resolve() for path in allowed}
    for resolved,(path,digest) in observed.items():
        if resolved not in local and digest!=pinned[resolved]:
            raise ValueError('installed runtime identity differs from the approved contract')
        if resolved not in exempt and sha256(path)!=digest:
            raise ValueError('runtime hash mismatch: '+path)


def count_value(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('invalid '+name+' count')
    return value


def verify_cohort(cohort):
    if not isinstance(cohort,dict) or not isinstance(cohort.get('sources'),list) or not cohort['sources']:
        raise ValueError('missing cohort sources')
    paths=[Path(source['path']).resolve() for source in cohort['sources']]
    if len(set(paths))!=len(paths) or paths!=[Path(p).resolve() for p in cohort.get('source_order',[])]:
        raise ValueError('cohort source order mismatch')
    consumed=0
    for source in cohort['sources']:
        n=count_value(source['consumed'],'source consumed',1)
        first=count_value(source['first_source_row'],'first source row',1)
        last=count_value(source['last_source_row'],'last source row',first)
        if last-first+1<n:raise ValueError('source boundary shorter than consumed rows')
        size=count_value(source['bytes'],'source bytes',1)
        if Path(source['path']).stat().st_size!=size or sha256(source['path'])!=source['sha256']:
            raise ValueError('source hash/length mismatch')
        consumed+=n
    if consumed!=count_value(cohort.get('count'),'cohort',1):
        raise ValueError('cohort consumption count mismatch')


def verify_sign(manifest):
    sign=manifest.get('sign_audit')
    if not isinstance(sign,dict):raise ValueError('missing sign audit')
    train=manifest['train']
    if (count_value(sign.get('rows'),'sign rows',1)!=train['rows'] or
            count_value(sign.get('known_result_count'),'sign known',2)!=manifest['known_result_count'] or
            count_value(sign.get('unknown_result_count'),'sign unknown')+sign['known_result_count']!=train['rows'] or
            sign.get('selection_sha256')!=train['sha256'] or
            sign.get('pearson_stm_score_result')!=manifest['pearson_stm_score_result']):
        raise ValueError('sign audit does not bind the selected payload')
    mirrors=count_value(sign.get('mirror_checked'),'mirror',MIN_MIRRORS)
    if mirrors>train['rows'] or sign.get('mirror_status')!='PASS':
        raise ValueError('mirror audit failed')
    if count_value(sign.get('sample_bytes'),'sample bytes',1)!=Path(manifest['sample']['path']).stat().st_size:
        raise ValueError('sign audit sample size mismatch')


def verify_payload(item):
    count_value(item['rows'],'payload rows',1)
    h=hashlib.sha256(); count=0
    with open(item['path'],'rb') as fh:
        for line in fh:
            h.update(line); count+=1
    if h.hexdigest()!=item['sha256']: raise ValueError('payload hash mismatch')
    if count!=item['rows']: raise ValueError('payload row count mismatch')
    return count

def verify(path, *, allow_runtime_changes=()):
    """Default: strict admission. Overrides are only for reviewed historical-data reuse.

    The refresher hard-pins its prior manifest before allowing the three owned
    normalization/admission modules to change. No installed npt or native file
    can be exempted; a newly published manifest always passes strict verification.
    """
    original_bytes=Path(path).read_bytes()
    manifest_digest=hashlib.sha256(original_bytes).hexdigest()
    manifest=json.loads(original_bytes)
    required={'schema','strength','train','metadata','validation','sample','runtime','cohort',
              'holdouts','clearance','training_ready','pearson_stm_score_result',
              'baseline_wrapper','recipes','hyperparameters','known_result_count'}
    if not isinstance(manifest,dict) or not required <= manifest.keys():
        raise ValueError('incomplete handoff manifest')
    if type(manifest['schema']) is not int or manifest['schema']!=1:raise ValueError('unsupported manifest schema')
    if manifest['strength']!='UNPROVEN': raise ValueError('invalid strength claim')
    correlation=manifest['pearson_stm_score_result']
    if (type(correlation) not in (int,float) or not math.isfinite(correlation)
            or not 0.1 < correlation <= 1.0 or manifest['training_ready'] is not True):
        raise ValueError('training readiness/sign audit failed')
    if manifest['recipes']!=EXPECTED_RECIPES or manifest['hyperparameters']!=EXPECTED_HYPERPARAMETERS:
        raise ValueError('manifest recipe differs from the fixed training command')
    allowed={str(Path(p).resolve()) for p in allow_runtime_changes}
    if not allowed <= REVIEWABLE_RUNTIME:raise ValueError('runtime migration outside reviewed local modules')
    historical=bool(allowed) and manifest_digest==APPROVED_PREVIOUS_SHA256
    if allowed and not historical:raise ValueError('runtime migration requires the approved historical manifest')
    verify_runtime(manifest['runtime'],allowed)
    if not historical:
        tooling=manifest.get('tooling')
        expected={(HERE/name).resolve() for name in TOOLING}
        if (not isinstance(tooling,dict) or len(tooling)!=len(expected) or
                {Path(p).resolve() for p in tooling}!=expected):
            raise ValueError('incomplete handoff tooling identity')
    for name in ('train','metadata','validation','sample'):
        verify_payload(manifest[name])
    if manifest['train']['rows']!=manifest['metadata']['rows'] or manifest['train']['sha256']!=manifest['metadata']['sha256']:
        raise ValueError('metadata alignment mismatch')
    if Path(manifest['sample']['path']).stat().st_size>20*10**6: raise ValueError('sample over 20 MB')
    for p,h in manifest.get('tooling',{}).items():
        if sha256(p)!=h:raise ValueError('tooling hash mismatch: '+p)
    wrapper=manifest['baseline_wrapper']
    if sha256(wrapper['path'])!=wrapper['sha256']:raise ValueError('baseline recipe wrapper changed')
    verify_cohort(manifest['cohort'])
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
    selection=receipt['selection']
    before=count_value(selection.get('input'),'clearance input',1)
    kept=count_value(selection.get('kept'),'clearance kept',1)
    excluded=count_value(selection.get('holdout_excluded'),'clearance excluded')
    if before!=manifest['cohort']['count'] or kept+excluded!=before:
        raise ValueError('clearance row conservation failed')
    original=manifest['cohort'].get('hashes',{}).get('million.jsonl')
    if not original or receipt.get('original_selection_sha256')!=original:
        raise ValueError('clearance original cohort mismatch')
    complete=receipt.get('complete_holdouts',[])
    expected={(str(Path(h['path']).resolve()),h['sha256'],h['rows']) for h in holds}
    observed={(str(Path(h['path']).resolve()),h['sha256'],h['rows']) for h in complete}
    if len(complete)!=2 or observed!=expected:raise ValueError('clearance complete holdout bindings mismatch')
    if type(manifest['known_result_count']) is not int or not 2 <= manifest['known_result_count'] <= manifest['train']['rows']:
        raise ValueError('invalid known-result count')
    if not historical:verify_sign(manifest)
    if sha256(path)!=manifest_digest:raise ValueError('manifest changed during verification')
    return dict(status='PASS',training_rows=manifest['train']['rows'],validation_rows=manifest['validation']['rows'],
                sample_rows=manifest['sample']['rows'],sample_bytes=Path(manifest['sample']['path']).stat().st_size,
                strength='UNPROVEN',manifest_sha256=manifest_digest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');a=p.parse_args();low_priority()
    print(json.dumps(verify(a.manifest),indent=2))
