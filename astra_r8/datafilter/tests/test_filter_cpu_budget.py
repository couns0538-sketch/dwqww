"""The coordinating parser/writer counts toward the two-compute-process limit."""
import chess
import pytest

import filter_positions as filtering
from records import dumps, record


@pytest.mark.parametrize('budget', [1, 2])
def test_parent_and_pool_stay_within_the_requested_budget(tmp_path, monkeypatch, budget):
    observed = []
    class RecordingPool:
        def __init__(self, *, max_workers, initializer):
            observed.append(max_workers)
            assert 1+max_workers <= budget, 'parent parsing/writing plus pool exceeds CPU budget'
        def map(self, function, jobs):
            return map(function, jobs)
        def shutdown(self, **kwargs):
            pass
    monkeypatch.setattr(filtering, 'ProcessPoolExecutor', RecordingPool)
    source = tmp_path/'input.jsonl'
    row = record(chess.STARTING_FEN, 30, 'cp', 1, 'fixture', 1, 'selfplay')
    source.write_text(dumps(row)+'\n')
    result = filtering.run_filter(source, tmp_path/'output', workers=budget)
    assert result['kept'] == 1
    assert result['coordinator_workers'] == 1
    assert result['pool_workers'] == budget-1
    assert observed == ([] if budget == 1 else [1])
