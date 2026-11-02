"""Combine actual small profiler outputs without averaging shard correlations."""
import hashlib
import json
import math
from pathlib import Path

import chess
import pytest

import profile_corpus as profile
import report_corpus as report


def prepare(tmp_path, monkeypatch, *, flat=False, unknown=False):
    monkeypatch.setattr(report, 'EXPECTED_SOURCES', {'forge_selfplay_001.txt','forge_selfplay_002.txt'})
    groups = [[(100,'1'),(-100,'0'),(0,'0.5')], [(200,'1'),(100,'1'),(0,'0.5'),(-50,'1')]]
    if flat:
        groups = [[(0,'0.5')]*3, [(0,'0.5')]*4]
    if unknown:
        groups = [[(score,'?') for score,_ in rows] for rows in groups]
    paths = []
    for i, rows in enumerate(groups, 1):
        source = tmp_path/f'forge_selfplay_{i:03}.txt'
        source.write_text(''.join(f'{chess.STARTING_FEN} | {score} | {result}\n' for score,result in rows))
        Path(str(source)+'.md5').write_text(hashlib.md5(source.read_bytes()).hexdigest()+'  '+source.name+'\n')
        output = tmp_path/f'profile_{i}'
        profile.run(profile.freeze_plan([source]), output, mirror_stride=1, sample_rows=10)
        paths.append(output/'SUMMARY.json')
    return paths


def test_complete_aggregation_uses_position_weighted_moments(tmp_path, monkeypatch):
    paths = prepare(tmp_path, monkeypatch)
    actual = report.combine(paths)
    xs = [100,-100,0,200,100,0,-50]
    ys = [1,-1,0,1,1,0,1]
    ax, ay = sum(xs)/len(xs), sum(ys)/len(ys)
    expected = sum((x-ax)*(y-ay) for x,y in zip(xs,ys))/math.sqrt(
        sum((x-ax)**2 for x in xs)*sum((y-ay)**2 for y in ys))
    assert actual['totals']['data_rows'] == 7
    assert actual['pearson_stm_score_result'] == pytest.approx(expected)
    average = sum(r['pearson_stm_score_result'] for r in actual['sources'])/2
    assert abs(actual['pearson_stm_score_result']-average) > 0.01
    assert actual['training_ready'] is False and actual['strength'] == 'UNPROVEN'


@pytest.mark.parametrize('damage', ['prefix','missing','duplicate','sample','source','histogram'])
def test_incomplete_changed_or_overlapping_profile_rejected(tmp_path, monkeypatch, damage):
    paths = prepare(tmp_path, monkeypatch)
    if damage == 'missing':
        paths = paths[:1]
    elif damage == 'duplicate':
        paths.append(paths[0])
    elif damage == 'sample':
        paths[0].with_name('000.sample.jsonl').write_text('changed\n')
    elif damage == 'source':
        (tmp_path/'forge_selfplay_001.txt').write_text('changed\n')
    else:
        summary = json.loads(paths[0].read_text())
        if damage == 'prefix':
            summary['max_rows_per_source'] = 3
        else:
            summary['sources'][0]['histograms']['ply']['<=20'] = 99
            paths[0].with_name('000.json').write_text(json.dumps(summary['sources'][0]))
        paths[0].write_text(json.dumps(summary))
    with pytest.raises(ValueError):
        report.combine(paths)


@pytest.mark.parametrize('unknown', [False, True])
def test_undefined_correlation_is_explicit(tmp_path, monkeypatch, unknown):
    paths = prepare(tmp_path, monkeypatch, flat=True, unknown=unknown)
    result = report.combine(paths)
    assert result['pearson_stm_score_result'] is None
    assert 'undefined (insufficient variance)' in report.markdown(result)
    assert result['totals']['unknown_results'] == (7 if unknown else 0)


@pytest.mark.parametrize('damage', ['negative_square','negative_variance','zero_variance_covariance',
                                   'empty_known_moments','score_result_marginal'])
def test_reviewed_impossible_statistics_rejected(tmp_path, monkeypatch, damage):
    paths = prepare(tmp_path, monkeypatch, unknown=damage=='empty_known_moments')
    summary = json.loads(paths[0].read_text())
    source = summary['sources'][0]
    if damage == 'score_result_marginal':
        source['histograms']['score_result'] = {'<=0:None':source['data_rows']}
    else:
        source['pearson_stm_score_result'] = None
        if damage == 'negative_square':
            source['moments'][3] = -1
        elif damage == 'negative_variance':
            source['moments'][1] = 100
            source['moments'][3] = 1
        elif damage == 'zero_variance_covariance':
            source['moments'][1] = source['moments'][3] = 0
            source['moments'][5] = 1
        else:
            source['moments'][1] = 1
    paths[0].with_name('000.json').write_text(json.dumps(source))
    paths[0].write_text(json.dumps(summary))
    with pytest.raises(ValueError):
        report.combine(paths)


def test_new_outputs_are_deterministic_and_existing_outputs_refused(tmp_path, monkeypatch):
    paths = prepare(tmp_path, monkeypatch)
    report.run(paths, tmp_path/'a')
    report.run(paths, tmp_path/'b')
    for name in ('corpus_report.json','DATA_PROFILE.md'):
        assert (tmp_path/'a'/name).read_bytes() == (tmp_path/'b'/name).read_bytes()
    with pytest.raises(FileExistsError):
        report.run(paths, tmp_path/'a')
