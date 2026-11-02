"""QA fix 5 (CR N-1 MED): seeded per-pass full permutation instead of the clustered affine lattice."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROWS, SEED, BATCH = 999953, 61101, 16384

def cluster_fraction(idx):
    """Share of in-batch sorted neighbours <= 3 source rows apart (CR N-1 metric; random ~5%)."""
    s = np.sort(np.asarray(idx, dtype=np.int64))
    return float(np.mean(np.diff(s) <= 3))

def test_no_same_game_clustering_seed61101_first_three_passes():
    from npt_adapter import Sampler
    s = Sampler(ROWS, SEED, 'm')
    for p in range(3):
        s.cursor = p * ROWS
        worst = max(cluster_fraction(s.take(BATCH)) for _ in range(61))
        assert worst < 0.10, f'pass {p}: worst batch {worst:.3f} of neighbours within 3 rows'

def test_every_row_exactly_once_per_pass():
    from npt_adapter import Sampler
    for count in (1, 2, 17, 50, ROWS):
        s = Sampler(count, SEED, 'm')
        for p in range(3):
            assert np.array_equal(np.bincount(s.take(count), minlength=count), np.ones(count, dtype=np.int64))
        assert s.cursor == 3 * count

def test_deterministic_and_seed_pass_dependent():
    from npt_adapter import Sampler
    a, b = Sampler(ROWS, SEED, 'm'), Sampler(ROWS, SEED, 'm')
    x, y = a.take(2 * ROWS + 100), b.take(2 * ROWS + 100)
    assert x == y
    assert x[:ROWS] != x[ROWS:2 * ROWS]                       # passes differ
    assert Sampler(ROWS, SEED + 1, 'm').take(1000) != x[:1000]  # seeds differ
    c = Sampler(ROWS, SEED, 'm'); c.cursor = ROWS - 5          # mid-run resume across a pass boundary
    assert c.take(10) == x[ROWS - 5:ROWS + 5]

def test_take_equals_next_and_state_algorithm():
    from npt_adapter import Sampler
    a, b = Sampler(50, SEED, 'm'), Sampler(50, SEED, 'm')
    assert a.take(137) == [b.next() for _ in range(137)]
    st = a.state_dict(); assert st['algorithm'] == 'perm-v1'
    with pytest.raises(ValueError):
        Sampler(50, SEED, 'm').load_state_dict(dict(st, algorithm='affine-v1'))
    with pytest.raises(ValueError):
        Sampler(50, -1, 'm')
