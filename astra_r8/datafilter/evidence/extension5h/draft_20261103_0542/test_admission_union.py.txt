"""Adversarial receipt fixtures for complete current-parser audit aggregation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import chess

import pytest

import seal_admission as seal


def put(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


@pytest.fixture
def union(tmp_path, monkeypatch):
    prior_path = tmp_path/'prior.json'
    put(prior_path, {'fixture': True})
    bindings = [{'path': str(prior_path), 'sha256': seal.sha256(prior_path)}]
    pins = seal.validator_identity()
    earlier, plans, reports = [], [], []
    for number in (3, 4):
        source = tmp_path/f'forge_selfplay_{number:03}.txt'
        source.write_bytes(b'authored receipt fixture\n')
        sidecar = Path(str(source)+'.md5')
        md5 = hashlib.md5(source.read_bytes()).hexdigest()
        sidecar.write_text(md5+' '+source.name+'\n')
        prior = dict(path=str(source), data_rows=1, sha256=seal.sha256(source),
                     source_identity=seal.stat_key(source), sidecar_sha256=seal.sha256(sidecar),
                     expected_md5=md5, known_results=1, unknown_results=0, skipped_lines=0)
        earlier.append(prior)
        plans.append(dict(path=str(source), identity=prior['source_identity'], sidecar=str(sidecar),
                          sidecar_sha256=prior['sidecar_sha256'], expected_md5=md5,
                          expected_sha256=prior['sha256'], expected_data_rows=1))
        reports.append(dict(path=str(source), status='PASS', complete_scan=True, data_rows=1,
                            valid_rows=1, invalid_rows=0, known_results=1, unknown_results=0,
                            skipped_lines=0, invalid_examples=[], sha256=prior['sha256'], md5=md5,
                            expected_sha256=prior['sha256'], expected_data_rows=1,
                            source_identity=prior['source_identity'], sidecar_sha256=prior['sidecar_sha256'],
                            seconds=1.0, positions_per_second=1.0))
    reference = dict(profile_inputs=bindings, sources=earlier, totals={'data_rows':2})
    monkeypatch.setattr(seal, 'combine', lambda profiles: deepcopy(reference))
    summaries = []
    for index in range(2):
        folder = tmp_path/f'part{index}'; folder.mkdir()
        plan = dict(schema=1, sources=[plans[index]], partition=index, partitions=2,
                    reference_profiles=bindings, complete_reference_set=False,
                    reference_source_names=[Path(row['path']).name for row in earlier], reference_rows=2)
        run = dict(validator_files=pins, python=sys.version, chess_version=chess.__version__,
                   started_utc='2026-11-03T04:00:00+00:00')
        summary = dict(schema=1, status='PASS', training_ready=False, strength='UNPROVEN',
                       workers=1, complete_reference_set=False, validator_files=pins,
                       reference_profiles=bindings, sources=[reports[index]], total_data_rows=1,
                       total_invalid_rows=0, **{k:v for k,v in run.items() if k!='validator_files'},
                       finished_utc='2026-11-03T04:00:02+00:00')
        for name, value in [('PLAN.json',plan), ('RUN.json',run), ('000.json',reports[index]), ('SUMMARY.json',summary)]:
            put(folder/name, value)
        summaries.append(folder/'SUMMARY.json')
    return [prior_path], summaries, reference


def change(path, edit):
    value = json.loads(path.read_text())
    edit(value)
    put(path, value)


def change_source(path, edit):
    change(path, lambda summary: edit(summary['sources'][0]))
    change(path.parent/'000.json', edit)


def test_complete_disjoint_union_is_descriptive_only(union):
    profiles, summaries, _ = union
    result = seal.verify(profiles, summaries)
    assert result['status']=='PASS' and result['complete_reference_set'] is True
    assert result['total_data_rows']==2 and len(result['sources'])==2
    assert result['training_ready'] is False and result['strength']=='UNPROVEN'
    assert result['elapsed_span_seconds']==2 and result['source_compute_seconds']==2
    assert len(result['bound_receipts'])==9
    assert (result['python'],result['chess_version'])==(sys.version,chess.__version__)


@pytest.mark.parametrize('key,value', [('status','FAIL'), ('schema',True), ('workers',True),
    ('training_ready',True), ('strength','PROVEN'), ('validator_files',{}),
    ('total_data_rows',2), ('total_data_rows',True), ('total_invalid_rows',1),
    ('complete_reference_set',True), ('reference_profiles',[]),
    ('python','different-python'), ('started_utc','2026-11-03T04:00:00'),
    ('finished_utc','2026-11-03T03:59:00+00:00')])
def test_partition_summary_corruption_rejected(union,key,value):
    profiles,summaries,_=union
    change(summaries[0], lambda summary: summary.update({key:value}))
    with pytest.raises(ValueError): seal.verify(profiles,summaries)


@pytest.mark.parametrize('key,value', [('complete_scan',False), ('status','FAIL'),
    ('valid_rows',0), ('invalid_rows',1), ('data_rows',True), ('known_results',2),
    ('sha256','0'*64), ('expected_sha256','0'*64), ('md5','0'*32),
    ('expected_data_rows',2), ('expected_data_rows',True), ('invalid_examples',[{}]), ('seconds',0),
    ('seconds',float('nan')), ('positions_per_second',2)])
def test_matching_per_source_forgery_still_fails_reference(union,key,value):
    profiles,summaries,_=union
    change_source(summaries[0],lambda row:row.update({key:value}))
    with pytest.raises(ValueError):seal.verify(profiles,summaries)


@pytest.mark.parametrize('key,value', [('partition',True), ('partition',1),
    ('partitions',1), ('reference_rows',3), ('reference_source_names',[]),
    ('complete_reference_set',True), ('sources',[]), ('schema',True)])
def test_plan_contract_corruption_rejected(union,key,value):
    profiles,summaries,_=union
    change(summaries[0].parent/'PLAN.json',lambda plan:plan.update({key:value}))
    with pytest.raises(ValueError):seal.verify(profiles,summaries)


def test_missing_partition_cannot_claim_complete_union(union):
    profiles,summaries,_=union
    with pytest.raises(ValueError):seal.verify(profiles,summaries[:1])


def test_consistent_runtime_substitution_cannot_pass(union):
    profiles,summaries,_=union
    for summary in summaries:
        for path in (summary,summary.parent/'RUN.json'):
            change(path,lambda value:value.update(python='other-python',chess_version='other-chess'))
    with pytest.raises(ValueError,match='runtime'):seal.verify(profiles,summaries)


def test_known_unknown_swap_cannot_hide_coverage_disagreement(union):
    profiles,summaries,_=union
    change_source(summaries[0],lambda row:row.update(known_results=0,unknown_results=1))
    with pytest.raises(ValueError,match='coverage'):seal.verify(profiles,summaries)


def test_duplicate_partition_cannot_double_count(union):
    profiles,summaries,_=union
    with pytest.raises(ValueError):seal.verify(profiles,[summaries[0],summaries[0]])


def test_source_receipt_disagreement_rejected(union):
    profiles,summaries,_=union
    change(summaries[0].parent/'000.json',lambda row:row.update(seconds=2))
    with pytest.raises(ValueError,match='sealed source'):seal.verify(profiles,summaries)


def test_original_source_mutation_rejected(union):
    profiles,summaries,reference=union
    Path(reference['sources'][0]['path']).write_bytes(b'changed')
    with pytest.raises(ValueError,match='source identity'):seal.verify(profiles,summaries)


def test_producer_sidecar_mutation_rejected(union):
    profiles,summaries,reference=union
    Path(reference['sources'][0]['path']+'.md5').write_text('changed')
    with pytest.raises(ValueError,match='sidecar'):seal.verify(profiles,summaries)


def test_validator_drift_rejected(union,monkeypatch):
    profiles,summaries,_=union
    original=seal.validator_identity
    calls=0
    def drift():
        nonlocal calls
        calls+=1
        return original() if calls==1 else {}
    monkeypatch.setattr(seal,'validator_identity',drift)
    with pytest.raises(ValueError,match='validator'):seal.verify(profiles,summaries)


def test_changed_bound_receipt_after_read_is_rejected(union,monkeypatch):
    profiles,summaries,_=union
    original=seal.verify_source
    calls=0
    def drift(*args):
        nonlocal calls
        calls+=1
        result=original(*args)
        if calls==2:
            change(summaries[0],lambda value:value.update(total_data_rows=999))
        return result
    monkeypatch.setattr(seal,'verify_source',drift)
    with pytest.raises(ValueError,match='bound receipt changed'):seal.verify(profiles,summaries)


def test_partial_directory_never_becomes_complete_proof(union):
    profiles,summaries,_=union
    folder=summaries[0].parent
    renamed=folder.with_name(folder.name+'.partial')
    folder.rename(renamed)  # Only a newly authored temporary fixture.
    summaries[0]=renamed/'SUMMARY.json'
    with pytest.raises(ValueError,match='published'):seal.verify(profiles,summaries)


def test_publication_reuse_refused_and_failure_unpublished(union,tmp_path,monkeypatch):
    profiles,summaries,_=union
    monkeypatch.setattr(seal,'storage_guard',lambda *args,**kwargs:None)
    result=seal.run(profiles,summaries,tmp_path/'sealed')
    assert result['status']=='PASS'
    with pytest.raises(FileExistsError):seal.run(profiles,summaries,tmp_path/'sealed')
    change(summaries[0],lambda row:row.update(status='FAIL'))
    with pytest.raises(ValueError):seal.run(profiles,summaries,tmp_path/'invalid')
    assert not (tmp_path/'invalid').exists()


def test_real_profile_admission_and_complete_union_contract(tmp_path,monkeypatch):
    import audit_forge_admission as admission
    import profile_corpus as profile
    import report_corpus
    # Small authored fixtures only. Exercise the real 37-source name contract,
    # real profile reports/reservoirs, reference binding, and both admission runs.
    for module in (profile,admission,seal):
        monkeypatch.setattr(module,'storage_guard',lambda *args,**kwargs:None)
    paths=[]
    for name in sorted(report_corpus.EXPECTED_SOURCES):
        path=tmp_path/name
        path.write_text(chess.STARTING_FEN+' | 20 | 0.5\n',encoding='utf-8')
        Path(str(path)+'.md5').write_text(hashlib.md5(path.read_bytes()).hexdigest()+'  '+name+'\n')
        paths.append(path)
    profiles=[]
    for index in range(2):
        output=tmp_path/f'profile{index}'
        profile.run(profile.freeze_plan(paths[index::2]),output,mirror_stride=1,sample_rows=1)
        profiles.append(output/'SUMMARY.json')
    with pytest.raises(ValueError,match='incomplete'):
        admission.make_plan(profiles[:1])
    summaries=[]
    for index in range(2):
        output=tmp_path/f'admission{index}'
        plan=admission.make_plan(profiles,partition=index,partitions=2)
        admission.run(plan,output)
        summaries.append(output/'SUMMARY.json')
    result=seal.run(profiles,summaries,tmp_path/'union')
    assert result['total_data_rows']==37 and result['total_invalid_rows']==0
    assert len(result['sources'])==37 and result['complete_reference_set'] is True
