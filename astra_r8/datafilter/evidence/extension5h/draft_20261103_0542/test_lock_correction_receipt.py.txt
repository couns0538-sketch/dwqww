"""A parsed native transcript must match every corrected pin exactly once."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

DRIVER=Path(__file__).resolve().parents[1]/'evidence/extension5h/verify_lock_correction.py'
spec=importlib.util.spec_from_file_location('lock_correction_receipt',DRIVER)
correction=importlib.util.module_from_spec(spec)
spec.loader.exec_module(correction)


def healthy():
    return ('uciok\nreadyok\n'+''.join(f'nodes {nodes}\n' for nodes in correction.PERFT)
            +''.join(f'bench depth {depth} nodes {nodes}\n' for depth,nodes in correction.PINS))


def test_complete_corrected_transcript_passes():
    result=correction.check_reply(healthy(),0)
    assert result['perft5_actual']==[4865609,193690690]
    assert result['bench_actual']==[(11,312866),(13,862329),(16,3024920),(20,12389307),(22,34048354)]


@pytest.mark.parametrize('original,replacement',[
    ('312866','273845'),('862329','718758'),('3024920','3028212'),
    ('4865609','4865608'),('193690690','193690689'),('uciok\n',''),('readyok\n',''),
    ('bench depth 22 nodes 34048354\n',''),
    ('nodes 4865609\n','nodes 4865609\nnodes 4865609\n'),
    ('bench depth 11 nodes 312866\n','bench depth 11 nodes 312866\nbench depth 11 nodes 312866\n')])
def test_wrong_missing_or_duplicate_native_counts_fail(original,replacement):
    with pytest.raises(ValueError):correction.check_reply(healthy().replace(original,replacement),0)


def test_nonzero_engine_exit_cannot_pass_correct_counts():
    with pytest.raises(ValueError):correction.check_reply(healthy(),1)


def test_protected_manifest_change_before_snapshot_cannot_become_baseline(tmp_path,monkeypatch):
    real_hash=correction.sha256
    monkeypatch.setattr(correction,'sha256',lambda path:
        correction.LOCK if Path(path)==correction.ENGINE else
        correction.V7_SHA if Path(path)==correction.V7/'manifest.json' else real_hash(path))
    monkeypatch.setattr(correction,'storage_guard',lambda *args,**kwargs:None)
    monkeypatch.setattr(correction,'low_priority',lambda:None)
    monkeypatch.setattr(correction,'fingerprint_tree',lambda root:{'manifest.json':'0'*64})
    monkeypatch.setattr(correction,'compare_streams',lambda *args:[])
    calls=[]
    def engine(*args,**kwargs):
        calls.append(args)
        return SimpleNamespace(stdout=healthy(),stderr='',returncode=0)
    monkeypatch.setattr(correction.subprocess,'run',engine)
    with pytest.raises(ValueError,match='protected v7 snapshot'):
        correction.run(tmp_path/'proof')
    assert not calls
    assert json.loads((tmp_path/'proof/REPORT.json').read_text())['status']=='FAIL'
