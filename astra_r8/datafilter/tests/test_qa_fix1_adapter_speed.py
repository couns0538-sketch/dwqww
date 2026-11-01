"""QA fix 1: validate each row once at load, cached per-pass affine permutation, bit-identical batches."""
import json
import math
import random
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def rows_file(tmp_path, n=50):
    from records import dumps
    from filter_positions import sha256
    src = Path(__file__).resolve().parents[1] / 'sample/positions.jsonl'
    lines = src.read_text(encoding='utf-8').splitlines()[:n]
    p = tmp_path / 'rows.jsonl'; p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return p, sha256(p)

import functools

@functools.lru_cache(maxsize=4)
def _reference_pass(count, seed, p):
    import numpy as np
    return np.random.default_rng([seed, p]).permutation(count).tolist()

def reference_next(count, seed, cursor):
    """Independent perm-v1 reference (QA fix 5 replaced the affine order; see test_qa_fix5_sampler_perm.py)."""
    p, offset = divmod(cursor, count)
    return _reference_pass(count, seed, p)[offset]

@pytest.mark.parametrize('count', [1, 17, 50, 999953])
def test_take_matches_reference_order_across_passes(count):
    from npt_adapter import Sampler
    s = Sampler(count, 61101, 'm')
    span = min(3 * count + 5, 40000)
    got = s.take(span)
    assert got == [reference_next(count, 61101, c) for c in range(span)]
    assert s.cursor == span
    t = Sampler(count, 61101, 'm'); t.cursor = 7
    assert t.take(5) == [reference_next(count, 61101, c) for c in range(7, 12)]

def test_each_row_validated_once(tmp_path, monkeypatch):
    import npt_adapter as a
    calls = []
    real = a.validate_record
    monkeypatch.setattr(a, 'validate_record', lambda r: (calls.append(1), real(r))[1])
    p, h = rows_file(tmp_path)
    f = a.RowFile(p, h)
    assert len(calls) == 50
    stream = a.BatchStream(f, a.Sampler(50, 61101, 'm'), 7, 16, 'K32H3', 'filtered_wdl_v1')
    batches = list(stream)
    assert len(batches) == 7 and len(calls) == 50

def test_batches_bit_identical_to_row_path(tmp_path):
    """Column path == an independent row path built straight from the JSON lines and the native API
    (not through make_batch/make_batch_validated, CR caveat), for the same sampler indices."""
    import torch
    import npt_adapter as a
    from records import validate_record
    p, h = rows_file(tmp_path)
    f = a.RowFile(p, h)
    new = list(a.BatchStream(f, a.Sampler(50, 61101, 'm'), 7, 16, 'K32H3', 'filtered_wdl_v1'))
    lines = p.read_bytes().splitlines()
    cursor = 0
    for b in new:
        idx = [reference_next(50, 61101, c) for c in range(cursor, cursor + 16)]; cursor += 16
        rows = [validate_record(json.loads(lines[i])) for i in idx]
        nat = a.data_loader.get_sparse_batch_from_fens('K32H3', [r['fen'] for r in rows], [r['score_stm'] for r in rows],
                                                      [r['ply'] for r in rows], [r['result_stm'] if r['has_result'] else 0 for r in rows])
        try:
            ref = tuple(t.clone() for t in nat.contents.get_tensors('cpu', use_pinned_memory=False))
        finally:
            a.data_loader.destroy_sparse_batch(nat)
        assert all(torch.equal(x, y) for x, y in zip(ref, b[:8]))
        assert b[8]['source_row'] == [r['source_row'] for r in rows] and b[8]['fen'] == [r['fen'] for r in rows]
        assert b[8] == a.make_batch(rows, 'K32H3', 'filtered_wdl_v1')[8]

def test_invalid_row_rejected_at_load(tmp_path):
    import npt_adapter as a
    from filter_positions import sha256
    p, _ = rows_file(tmp_path, 3)
    r = json.loads(p.read_text().splitlines()[1]); r['result_stm'] = -r['result_stm'] or 1
    bad = tmp_path / 'bad.jsonl'
    bad.write_text(p.read_text().splitlines()[0] + '\n' + json.dumps(r) + '\n')
    with pytest.raises(ValueError):
        a.RowFile(bad, sha256(bad))
