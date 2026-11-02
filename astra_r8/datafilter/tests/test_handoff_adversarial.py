"""Admission must bind the proof, not just trust a readiness boolean."""
import copy
import json
from pathlib import Path
import pytest
import verify_handoff as v


def fixture(tmp_path, monkeypatch):
    template=Path(__file__).resolve().parents[1]/'evidence/handoff_manifest.json'
    manifest=json.loads(template.read_text())
    rows=tmp_path/'rows.jsonl'; rows.write_bytes(b'{}\n{}\n')
    payload={'path':str(rows),'sha256':v.sha256(rows),'rows':2}
    for name in ('train','metadata','validation','sample'):manifest[name]=dict(payload)
    wrapper=tmp_path/'wrapper.py';wrapper.write_bytes(b'# fixture\n')
    manifest['baseline_wrapper']={'path':str(wrapper),'sha256':v.sha256(wrapper)}
    manifest['runtime']={'files':{str(wrapper):v.sha256(wrapper)}}
    manifest['cohort']={'sources':[{'path':str(rows),'sha256':v.sha256(rows)}]}
    holds=[];pins={}
    for shard in ('013','014'):
        p=tmp_path/(shard+'.txt');p.write_bytes((shard+'\n').encode())
        item={'shard':shard,'path':str(p),'sha256':v.sha256(p),'rows':1,'complete_scan':True}
        holds.append(item);pins[shard]=(item['sha256'],1)
    monkeypatch.setattr(v,'EXPECTED_HOLDOUTS',pins)
    manifest['holdouts']=holds
    receipt={'status':'PASS','remaining_overlap_unique_keys':0,
             'selection':{'records_sha256':payload['sha256'],'metadata_sha256':payload['sha256'],'kept':2},
             'complete_holdouts':copy.deepcopy(holds)}
    clearance=tmp_path/'clearance.json';clearance.write_text(json.dumps(receipt))
    manifest['clearance']={'path':str(clearance),'sha256':v.sha256(clearance)}
    manifest['known_result_count']=2;manifest['pearson_stm_score_result']=0.5
    path=tmp_path/'manifest.json'
    return path,manifest,receipt


@pytest.mark.parametrize('correlation',[float('nan'),float('inf'),1.5])
def test_nonfinite_or_impossible_correlation_rejected(tmp_path,monkeypatch,correlation):
    path,m,_=fixture(tmp_path,monkeypatch);m['pearson_stm_score_result']=correlation
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError):v.verify(path)


@pytest.mark.parametrize('field',['clearance','tooling','wrapper','recipe','hyperparameters','ready'])
def test_unbound_proof_and_recipe_rejected(tmp_path,monkeypatch,field):
    path,m,receipt=fixture(tmp_path,monkeypatch)
    if field=='clearance':
        receipt['complete_holdouts']=[]
        p=Path(m['clearance']['path']);p.write_text(json.dumps(receipt));m['clearance']['sha256']=v.sha256(p)
    elif field=='tooling':m['tooling']={m['baseline_wrapper']['path']:'0'*64}
    elif field=='wrapper':m['baseline_wrapper']['sha256']='0'*64
    elif field=='recipe':m['recipes']['filtered_wdl_v1']['selfplay_known_lambda']=0.2
    elif field=='hyperparameters':m['hyperparameters']['seed']=1
    else:m['training_ready']='yes'
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError):v.verify(path)


def test_valid_complete_proof(tmp_path,monkeypatch):
    path,m,_=fixture(tmp_path,monkeypatch);path.write_text(json.dumps(m))
    assert v.verify(path)['status']=='PASS'


def test_migration_cannot_exempt_installed_runtime(tmp_path,monkeypatch):
    path,m,_=fixture(tmp_path,monkeypatch);path.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='migration'):
        v.verify(path,allow_runtime_changes=[m['baseline_wrapper']['path']])


def test_refresher_migration_only_allows_reviewed_local_modules():
    from refresh_handoff import check_runtime_migration,HERE
    local=str((HERE/'train_adapter.py').resolve())
    old={'python':'same','torch':'same','files':{local:'old','F:/installed/train.py':'fixed'}}
    new=copy.deepcopy(old);new['files'][local]='new'
    assert set(check_runtime_migration(old,new))=={local}
    new['files']['F:/installed/train.py']='changed'
    with pytest.raises(ValueError,match='installed'):
        check_runtime_migration(old,new)
