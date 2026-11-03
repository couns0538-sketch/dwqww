import hashlib
import json
from pathlib import Path

import pytest

from r14_scan import parse_row, iter_rows, final_verdict, guard_selection, load_pins

START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


def test_three_keys_and_exact_clock_preservation():
    a = parse_row((START + ' | 2 | 0.5\n').encode())
    b = parse_row((START.replace('0 1', '4 8') + ' | -2 | 0.5\r\n').encode())
    assert a.fen == START
    assert a.ply == 0 and b.ply == 14
    assert a.keys['six_field'] != b.keys['six_field']
    assert a.keys['four_field'] == b.keys['four_field']
    assert a.keys['board_stm'] == b.keys['board_stm']


def test_raw_ep_changes_four_field_not_board():
    a = parse_row(b'4k3/8/8/3p4/8/8/8/4K3 w - d6 0 2 | 0 | 1.0\n')
    b = parse_row(b'4k3/8/8/3p4/8/8/8/4K3 w - - 0 2 | 0 | 1.0\n')
    assert a.keys['four_field'] != b.keys['four_field']
    assert a.keys['board_stm'] == b.keys['board_stm']


@pytest.mark.parametrize('bad', [b'', b'\n', b'x | 0 | 0.5', (START+' | nope | 0.5').encode(),
                                (START+' | 0 | 0.6').encode(), (START.replace(' w ', ' ? ')+' | 0 | 1').encode()])
def test_invalid_row_is_not_a_key(bad):
    with pytest.raises(ValueError):
        parse_row(bad)


def test_stream_hash_and_invalid_row_coverage(tmp_path):
    path = tmp_path / 'rows.txt'
    payload = (START+' | 0 | 0.5\ninvalid\n').encode()
    path.write_bytes(payload)
    receipt = {}
    rows = list(iter_rows(path, hashlib.md5(payload).hexdigest(), receipt))
    assert len(rows) == 2 and rows[0][1] is not None and rows[1][1] is None
    assert receipt['rows'] == 2 and receipt['valid_key_rows'] == 1
    assert receipt['parse_failures'] == 1 and receipt['key_fill_rate'] == .5
    assert receipt['actual_md5'] == hashlib.md5(payload).hexdigest()


def test_changed_input_hash_refused(tmp_path):
    path = tmp_path / 'rows.txt'
    path.write_text(START+' | 0 | 0.5\n')
    with pytest.raises(ValueError, match='hash'):
        list(iter_rows(path, '0'*32, {}))


def test_long_line_is_one_invalid_row(tmp_path):
    path = tmp_path / 'long.txt'
    payload = b'x'*10000+b'\n'+(START+' | 0 | .5\n').encode()
    path.write_bytes(payload)
    receipt = {}
    rows = list(iter_rows(path, hashlib.md5(payload).hexdigest(), receipt))
    assert [n for n, _ in rows] == [1, 2]
    assert receipt['parse_failures'] == 1


def test_missing_authentic_identity_always_blocks():
    assert final_verdict(authenticated=False, complete=True, overlaps=0, unknowns=0) == 'UNVERIFIED'
    assert final_verdict(authenticated=True, complete=True, overlaps=0, unknowns=0) == 'PASS'
    assert final_verdict(authenticated=True, complete=True, overlaps=1, unknowns=0) == 'FAIL'
    assert final_verdict(authenticated=True, complete=False, overlaps=0, unknowns=0) == 'UNVERIFIED'


def test_guard_band_counts_plies_not_row_distance():
    # Boundary between row2/row3: sparse original plies must not turn a guard into K rows.
    rows = [(1, 2), (2, 20), (3, 1), (4, 15)]
    kept, dropped = guard_selection(rows, boundary=2, k=8)
    assert kept == [1, 4]
    assert dropped == [2, 3]


def test_pin_manifest_requires_successful_full_digest(tmp_path):
    pins = tmp_path / 'pins.jsonl'
    pins.write_text(json.dumps(dict(path=str(tmp_path/'x'),match=False,actual_md5='a'*32,expected_md5='a'*32))+'\n')
    with pytest.raises(ValueError):
        load_pins(pins)


def test_consecutive_fen_digits_are_parse_failures(tmp_path):
    bad = b'4k3/8/8/8/8/8/8/4K111 w - - 0 1 | 0 | 0.5\n'
    with pytest.raises(ValueError):
        parse_row(bad)
    path = tmp_path / 'bad.txt'
    path.write_bytes(bad)
    receipt = {}
    list(iter_rows(path, hashlib.md5(bad).hexdigest(), receipt))
    assert receipt['valid_key_rows'] == 0 and receipt['parse_failures'] == 1


@pytest.mark.parametrize('rows', [[(2,5),(1,100),(3,1),(4,15)], [(1,5),(1,6),(2,1)], [(0,5),(1,6)], [(1,True),(2,1)]])
def test_guard_rejects_unordered_or_invalid_rows(rows):
    with pytest.raises(ValueError):
        guard_selection(rows, boundary=1, k=8)


def test_abandoned_iterator_never_claims_complete(tmp_path):
    path = tmp_path / 'rows.txt'
    data = ((START+' | 0 | 0.5\n')*2).encode()
    path.write_bytes(data)
    receipt = {}
    iterator = iter_rows(path, hashlib.md5(data).hexdigest(), receipt)
    next(iterator)
    iterator.close()
    assert receipt['complete'] is False and receipt['key_fill_rate'] is None


def test_long_final_line_without_newline(tmp_path):
    data = b'x'*10000
    path = tmp_path / 'long.txt'
    path.write_bytes(data)
    receipt = {}
    assert list(iter_rows(path, hashlib.md5(data).hexdigest(), receipt)) == [(1, None)]
    assert receipt['actual_md5'] == hashlib.md5(data).hexdigest()
    assert receipt['complete'] is True and receipt['parse_failures'] == 1
