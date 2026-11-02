"""A descriptive source audit cannot silently certify malformed or changed data."""
import hashlib
import json

import chess
import pytest

import profile_corpus as profile


def plan_for(tmp_path, rows):
    source = tmp_path / 'forge_selfplay_003.txt'
    source.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    sidecar = source.with_suffix('.txt.md5')
    sidecar.write_text(hashlib.md5(source.read_bytes()).hexdigest() + '  ' + source.name + '\n')
    plan = profile.freeze_plan([source])
    return source, plan


def test_exact_counts_and_result_orientation(tmp_path):
    rows = []
    for turn, score, white in [('w', 100, '1'), ('b', -100, '1'),
                               ('w', -100, '0'), ('b', 100, '0'),
                               ('w', 0, '0.5'), ('b', 12000, '?')]:
        rows.append(f'{chess.STARTING_FEN.replace(" w ", " " + turn + " ")} | {score} | {white}')
    source, plan = plan_for(tmp_path, rows)
    result = profile.run(plan, tmp_path / 'profile', mirror_stride=1, sample_rows=6)
    report = result['sources'][0]
    assert report['data_rows'] == report['valid_rows'] == 6
    assert report['invalid_rows'] == 0
    assert report['known_results'] == 5
    assert report['unknown_results'] == 1
    assert report['pearson_stm_score_result'] == pytest.approx(1.0)
    assert report['mirror_checks'] == 6
    assert report['complete_scan'] is True
    assert report['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert result['training_ready'] is False


def test_invalid_rows_are_counted_and_never_reported_pass(tmp_path):
    source, plan = plan_for(tmp_path, [f'{chess.STARTING_FEN} | 0 | 0.5',
                                      'broken | 1 | 1', f'{chess.STARTING_FEN} | 3 | 0.7'])
    result = profile.run(plan, tmp_path / 'profile', mirror_stride=1)
    report = result['sources'][0]
    assert result['status'] == 'FAIL'
    assert report['data_rows'] == 3 and report['valid_rows'] == 1 and report['invalid_rows'] == 2
    assert len(report['invalid_examples']) == 2
    assert report['pearson_stm_score_result'] is None


def test_source_mismatch_keeps_output_unpublished(tmp_path):
    source, plan = plan_for(tmp_path, [f'{chess.STARTING_FEN} | 0 | 0.5'])
    source.write_text(f'{chess.STARTING_FEN} | 10 | 1\n')
    with pytest.raises(ValueError, match='source'):
        profile.run(plan, tmp_path / 'profile')
    assert not (tmp_path / 'profile').exists()


def test_changed_producer_sidecar_refused(tmp_path):
    source, plan = plan_for(tmp_path, [f'{chess.STARTING_FEN} | 0 | 0.5'])
    source.with_suffix('.txt.md5').write_text('0'*32 + '  ' + source.name + '\n')
    with pytest.raises(ValueError, match='sidecar'):
        profile.run(plan, tmp_path / 'profile')


def test_duplicate_sources_and_holdouts_refused(tmp_path):
    source, _ = plan_for(tmp_path, [f'{chess.STARTING_FEN} | 0 | 0.5'])
    with pytest.raises(ValueError, match='duplicate'):
        profile.freeze_plan([source, source])
    with pytest.raises(ValueError, match='holdout'):
        profile.freeze_plan([tmp_path / 'forge_selfplay_013.txt'])


def test_bounded_prefix_is_explicit_and_entire_file_hash_checked(tmp_path):
    source, plan = plan_for(tmp_path, [f'{chess.STARTING_FEN} | {n} | 0.5' for n in range(10)])
    result = profile.run(plan, tmp_path / 'profile', max_rows=3)
    report = result['sources'][0]
    assert report['data_rows'] == 3 and report['complete_scan'] is False
    assert report['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert result['training_ready'] is False


def test_output_refusal_and_sample_limit(tmp_path):
    source, plan = plan_for(tmp_path, [f'{chess.STARTING_FEN} | {n} | 1' for n in range(10)])
    output = tmp_path / 'profile'
    result = profile.run(plan, output, sample_rows=2)
    samples = (output / '000.sample.jsonl').read_text().splitlines()
    assert len(samples) == 2
    with pytest.raises(FileExistsError):
        profile.run(plan, output)
    assert json.loads((output / 'SUMMARY.json').read_text()) == result


def test_complete_digest_rejects_same_metadata_change(tmp_path, monkeypatch):
    source, plan = plan_for(tmp_path, [f'{chess.STARTING_FEN} | 10 | 1'])
    original = plan['sources'][0]['identity']
    source.write_text(f'{chess.STARTING_FEN} | 20 | 1\n')
    monkeypatch.setattr(profile, 'stat_key', lambda path: original)
    with pytest.raises(ValueError, match='producer MD5'):
        profile.run(plan, tmp_path / 'profile')
    assert not (tmp_path / 'profile').exists()


def test_rule_and_native_boundary_counts(tmp_path):
    source, plan = plan_for(tmp_path, [
        '4k3/8/8/8/8/8/4r3/4K3 w - - 0 1 | -400 | 0',
        f'{chess.STARTING_FEN} | 32000 | 1',
        f'{chess.STARTING_FEN.replace(" 0 1", " 0 82")} | 0 | 0.5',
        f'{chess.STARTING_FEN} | 40000 | 1',
    ])
    report = profile.run(plan, tmp_path / 'profile')['sources'][0]
    assert report['in_check'] == 1 and report['mate_score'] == 2
    assert report['default_keep'] == 1 and report['ply_gt160'] == 1
    assert report['native_score_or_ply_out_of_range'] == 1


def test_empty_source_never_reports_pass(tmp_path):
    source, plan = plan_for(tmp_path, ['# empty audit input'])
    result = profile.run(plan, tmp_path / 'profile')
    assert result['status'] == 'FAIL'
    assert result['sources'][0]['data_rows'] == 0


def test_bad_utf8_rows_count_once(tmp_path):
    source, plan = plan_for(tmp_path, [f'{chess.STARTING_FEN} | 0 | 0.5'])
    source.write_bytes(b'\xff\n' + source.read_bytes() + b'\xff\n')
    source.with_suffix('.txt.md5').write_text(hashlib.md5(source.read_bytes()).hexdigest() + '  ' + source.name + '\n')
    plan = profile.freeze_plan([source])
    report = profile.run(plan, tmp_path / 'profile')['sources'][0]
    assert report['data_rows'] == 3 and report['invalid_rows'] == 2 and report['valid_rows'] == 1
