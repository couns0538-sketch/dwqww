"""The full-source admission audit must use the same parser as filtering."""
import hashlib
import json
from pathlib import Path

import chess
import pytest

import audit_forge_admission as audit
from test_corpus_profile import plan_for


def item_for(tmp_path, rows):
    source, plan = plan_for(tmp_path, rows)
    item = plan['sources'][0]
    item.update(expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                expected_data_rows=len(rows))
    return source, item


def test_complete_read_uses_strict_material_and_fen_contract(tmp_path):
    impossible = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNQ w KQkq - 0 1'
    # This board has no h1 rook but eight white pawns and two queens.
    impossible = impossible.replace('KQkq', 'Qkq')
    assert chess.Board(impossible).is_valid()
    source, item = item_for(tmp_path, [f'{chess.STARTING_FEN} | 0 | 0.5',
                                      f'{impossible} | 5 | 1',
                                      f'{chess.STARTING_FEN.replace(" w ", chr(160)+"w ")} | 1 | 1'])
    report = audit.scan_source(item)
    assert report['complete_scan'] is True and report['status'] == 'FAIL'
    assert (report['data_rows'], report['valid_rows'], report['invalid_rows']) == (3, 1, 2)
    assert len(report['invalid_examples']) == 2
    assert report['sha256'] == item['expected_sha256']
    assert source.read_text().count('|') == 6


def test_known_unknown_results_and_mirrors_pass_current_parser(tmp_path):
    fens = [chess.STARTING_FEN, chess.Board(chess.STARTING_FEN).mirror().fen(),
            '4k3/8/8/8/8/8/P7/QQ2K3 w - - 0 81']
    source, item = item_for(tmp_path, [f'{fen} | {score} | {result}'
        for fen, score, result in zip(fens, [100, -100, 0], ['1', '1', '?'])])
    report = audit.scan_source(item)
    assert report['status'] == 'PASS' and report['valid_rows'] == 3
    assert report['known_results'] == 2 and report['unknown_results'] == 1
    assert report['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()


def test_bounded_scan_does_not_claim_complete_source(tmp_path):
    source, item = item_for(tmp_path, [f'{chess.STARTING_FEN} | {n} | 0.5' for n in range(5)])
    report = audit.scan_source(item, max_rows=2)
    assert report['data_rows'] == 2 and report['complete_scan'] is False
    assert report['sha256'] == item['expected_sha256']


def test_expected_full_digest_and_row_count_are_required(tmp_path, monkeypatch):
    source, item = item_for(tmp_path, [f'{chess.STARTING_FEN} | 0 | 0.5'])
    item['expected_sha256'] = '0'*64
    with pytest.raises(ValueError, match='digest'):
        audit.scan_source(item)
    item['expected_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    item['expected_data_rows'] = 2
    with pytest.raises(ValueError, match='row count'):
        audit.scan_source(item)


def test_source_or_sidecar_mutation_rejected(tmp_path, monkeypatch):
    source, item = item_for(tmp_path, [f'{chess.STARTING_FEN} | 0 | 0.5'])
    original = audit.selfplay_record
    def corrupt(*args):
        Path(item['sidecar']).write_text('changed fixture sidecar')
        return original(*args)
    monkeypatch.setattr(audit, 'selfplay_record', corrupt)
    with pytest.raises(ValueError, match='sidecar'):
        audit.scan_source(item)


def test_invalid_examples_are_bounded(tmp_path):
    source, item = item_for(tmp_path, ['broken']*40)
    report = audit.scan_source(item)
    assert report['invalid_rows'] == 40 and len(report['invalid_examples']) == 32
    assert report['valid_rows'] == 0 and report['status'] == 'FAIL'


def test_bad_unicode_rows_are_counted_once(tmp_path):
    source, item = item_for(tmp_path, ['placeholder'])
    source.write_bytes(b'\xff\n'+chess.STARTING_FEN.encode()+b' | 0 | 0.5\n')
    Path(item['sidecar']).write_text(hashlib.md5(source.read_bytes()).hexdigest()+'  '+source.name+'\n')
    item = audit.freeze_plan([source])['sources'][0]
    item.update(expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), expected_data_rows=2)
    report = audit.scan_source(item)
    assert report['data_rows']==2 and report['invalid_rows']==1 and report['valid_rows']==1


@pytest.mark.parametrize('value', [0, -1, True, 1.5])
def test_invalid_row_limits_refused_before_reading(value):
    with pytest.raises(ValueError, match='positive integer'):
        audit.scan_source({}, max_rows=value)


@pytest.mark.parametrize('partition,partitions', [(0,0),(0,3),(2,2),(True,2),(0,True)])
def test_invalid_partition_refused_before_reference_read(partition, partitions):
    with pytest.raises(ValueError, match='partitions'):
        audit.make_plan([], partition=partition, partitions=partitions)


def test_partition_plans_are_disjoint_and_prefix_is_explicit(tmp_path, monkeypatch):
    import report_corpus
    reference = []
    for number in (3,4,5):
        source=tmp_path/f'forge_selfplay_{number:03}.txt'
        source.write_text(chess.STARTING_FEN+' | 0 | 0.5\n')
        Path(str(source)+'.md5').write_text(hashlib.md5(source.read_bytes()).hexdigest()+'  '+source.name+'\n')
        item=audit.freeze_plan([source])['sources'][0]
        reference.append({'path':str(source), 'source_identity':item['identity'],
                          'sidecar_sha256':item['sidecar_sha256'], 'data_rows':1,
                          'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    monkeypatch.setattr(report_corpus,'combine',lambda _: {'sources':reference,'profile_inputs':[]})
    groups=[audit.make_plan([],partition=index,partitions=2) for index in (0,1)]
    first,second=[{row['path'] for row in plan['sources']} for plan in groups]
    assert not first&second and first|second=={row['path'] for row in reference}
    assert all(plan['complete_reference_set'] is False for plan in groups)
    pilot=audit.make_plan([],max_sources=1)
    assert len(pilot['sources'])==1 and pilot['complete_reference_set'] is False


def test_strict_audit_publication_and_validator_drift(tmp_path, monkeypatch):
    source, item = item_for(tmp_path, [f'{chess.STARTING_FEN} | 0 | 0.5'])
    plan = {'schema':1, 'sources':[item], 'reference_profiles':[], 'complete_reference_set':False}
    result = audit.run(plan, tmp_path/'passed')
    assert result['status'] == 'PASS' and result['training_ready'] is False
    assert result['complete_reference_set'] is False
    assert result['validator_files']
    with pytest.raises(FileExistsError):audit.run(plan, tmp_path/'passed')
    original = audit.validator_identity
    calls = 0
    def drift():
        nonlocal calls
        calls += 1
        return original() if calls == 1 else {'changed': '0'*64}
    monkeypatch.setattr(audit, 'validator_identity', drift)
    with pytest.raises(ValueError, match='validator'):
        audit.run(plan, tmp_path/'drift')
    assert not (tmp_path/'drift').exists()


def test_invalid_rows_leave_only_failed_partial_evidence(tmp_path):
    source, item = item_for(tmp_path, ['broken'])
    plan = {'schema':1, 'sources':[item], 'reference_profiles':[], 'complete_reference_set':False}
    with pytest.raises(ValueError, match='admission'):
        audit.run(plan, tmp_path/'invalid')
    assert not (tmp_path/'invalid').exists()
    report=json.loads((tmp_path/'invalid.partial/SUMMARY.json').read_text())
    assert report['status']=='FAIL' and report['total_invalid_rows']==1


def test_lone_cr_comment_boundary_matches_actual_filter_reader(tmp_path):
    from records import read_records
    source, item = item_for(tmp_path, ['placeholder'])
    source.write_bytes(b'# comment\rbroken\n'+chess.STARTING_FEN.encode()+b' | 0 | 0.5\n')
    Path(item['sidecar']).write_text(hashlib.md5(source.read_bytes()).hexdigest()+'  '+source.name+'\n')
    item = audit.freeze_plan([source])['sources'][0]
    item.update(expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), expected_data_rows=2)
    with pytest.raises(ValueError):list(read_records(source,'selfplay'))
    report=audit.scan_source(item)
    assert report['status']=='FAIL' and report['invalid_rows']==1 and report['data_rows']==2
    assert report['invalid_examples'][0]['source_row']==2


def test_unbound_complete_reference_claim_is_refused(tmp_path):
    source,item=item_for(tmp_path,[chess.STARTING_FEN+' | 0 | 0.5'])
    plan={'schema':1,'sources':[item],'reference_profiles':[],'complete_reference_set':True}
    with pytest.raises(ValueError,match='reference'):
        audit.run(plan,tmp_path/'false_complete')
    assert not (tmp_path/'false_complete').exists()


def test_truncated_plan_cannot_retain_complete_claim(tmp_path,monkeypatch):
    import report_corpus
    source,item=item_for(tmp_path,[chess.STARTING_FEN+' | 0 | 0.5'])
    reference=tmp_path/'reference.json';reference.write_text('{}')
    inputs=[{'path':str(reference),'sha256':hashlib.sha256(reference.read_bytes()).hexdigest()}]
    report={'path':str(source),'sha256':item['expected_sha256'],'data_rows':1,
            'source_identity':item['identity'],'sidecar_sha256':item['sidecar_sha256'],
            'expected_md5':item['expected_md5']}
    missing={**report,'path':str(tmp_path/'forge_selfplay_004.txt')}
    monkeypatch.setattr(report_corpus,'combine',lambda _: {'sources':[report,missing],'profile_inputs':inputs})
    plan={'schema':1,'sources':[item],'reference_profiles':inputs,'complete_reference_set':True}
    with pytest.raises(ValueError,match='reference'):
        audit.run(plan,tmp_path/'truncated')
    assert not (tmp_path/'truncated').exists()


@pytest.mark.parametrize('comment_length', [8190,8191,8192,8193,16383])
def test_universal_newlines_and_full_hash_across_buffer_boundaries(tmp_path,comment_length):
    from records import read_records
    source,item=item_for(tmp_path,['placeholder'])
    valid=chess.STARTING_FEN.encode()+b' | 0 | 0.5'
    source.write_bytes(b'\xef\xbb\xbf#'+b'x'*comment_length+b'\r\n'+valid+b'\r'+valid)
    Path(item['sidecar']).write_text(hashlib.md5(source.read_bytes()).hexdigest()+'  '+source.name+'\n')
    item=audit.freeze_plan([source])['sources'][0]
    item.update(expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),expected_data_rows=2)
    expected=list(read_records(source,'selfplay'))
    report=audit.scan_source(item)
    assert len(expected)==report['valid_rows']==2 and report['invalid_rows']==0
    assert report['sha256']==item['expected_sha256'] and report['complete_scan']
