"""QA fix 7 (CR delta LOW-N1): perm-v1 order depends on numpy's Generator stream, which numpy does not
guarantee across versions. The sampler state stores numpy.__version__ and a pass-1 order hash; a resume
on a numpy that differs in version or in stream fails closed instead of silently reordering rows."""
import hashlib
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROWS, SEED = 999953, 61101
# numpy 2.5.4 (box and grok-pc), sha256 of default_rng([seed, 1]).permutation(999953)[:64] as int64 LE
GOLDEN = {61101: '351680240568d58aa7138309d8b2c46befa000acf3aa8752125c64eedc7e9c4f',
          61102: 'cfed8c9e97f798ad216f6363d88dee063c17158be8d0fff82d8c484811bf35c9'}

def independent_check(seed, count):
    head = np.random.default_rng([seed, 1]).permutation(count)[:64]
    return hashlib.sha256(np.ascontiguousarray(head, dtype='<i8').tobytes()).hexdigest()

def test_state_carries_numpy_version_and_pass1_order_hash():
    from npt_adapter import Sampler
    st = Sampler(ROWS, SEED, 'm').state_dict()
    assert st['numpy_version'] == np.__version__
    assert st['order_check'] == independent_check(SEED, ROWS)
    if np.__version__ == '2.5.4':
        for seed, want in GOLDEN.items():
            assert Sampler(ROWS, seed, 'm').state_dict()['order_check'] == want

def test_resume_roundtrip_and_order_check_does_not_disturb_order():
    from npt_adapter import Sampler
    a, ref = Sampler(50, SEED, 'm'), Sampler(50, SEED, 'm')
    first = a.take(73); st = a.state_dict(); rest = a.take(80)
    assert ref.take(153) == first + rest
    b = Sampler(50, SEED, 'm'); b.load_state_dict(st)
    assert b.cursor == 73 and b.take(80) == rest

@pytest.mark.parametrize('mutate', [
    lambda st: dict(st, numpy_version='1.26.4'),
    lambda st: {k: v for k, v in st.items() if k != 'numpy_version'},
    lambda st: dict(st, order_check='0' * 64),
    lambda st: {k: v for k, v in st.items() if k != 'order_check'},
])
def test_resume_fails_closed_on_numpy_or_order_mismatch(mutate):
    from npt_adapter import Sampler
    a = Sampler(50, SEED, 'm'); a.take(10)
    b = Sampler(50, SEED, 'm')
    with pytest.raises(ValueError):
        b.load_state_dict(mutate(a.state_dict()))
    assert b.cursor == 0

def test_resume_fails_closed_when_same_version_has_a_different_stream(monkeypatch):
    from npt_adapter import Sampler
    a = Sampler(50, SEED, 'm'); a.take(10); st = a.state_dict()
    real = np.random.default_rng
    monkeypatch.setattr(np.random, 'default_rng', lambda seq: real([seq[0] + 1, seq[1]]))  # same __version__, other stream
    b = Sampler(50, SEED, 'm')
    with pytest.raises(ValueError, match='order_check'):
        b.load_state_dict(st)
    assert b.cursor == 0
