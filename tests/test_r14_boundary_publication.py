import importlib.util
import json
from pathlib import Path
import sys
import time

import chess
import pytest

TOOLS = Path('D:/a14/tools')
sys.path.insert(0,str(TOOLS))


@pytest.fixture(scope='module')
def module():
    spec = importlib.util.spec_from_file_location('r14_boundary_run',TOOLS/'r14_boundary_run.py')
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def records(module,source_id,count=1,wrong_clock=False):
    board = chess.Board()
    if source_id % 2:
        board.push_uci('e2e4')
        if wrong_clock:
            board.halfmove_clock = 1
    return [module.parse_endpoint((board.fen(en_passant='fen')+' | 0 | 0.5').encode(),source_id,index+1)
            for index in range(count)]


def resolved_reply(lines,positive=False):
    return [dict(id=line.split('\t')[0],status='REACHABLE' if positive else 'UNREACHABLE',
                 reason='legal_witness' if positive else 'exhaustive_no_path',nodes=2,
                 witness=['e2e4'] if positive else []) for line in lines]


@pytest.mark.parametrize('fail_close',[False,True])
def test_native_session_gate_including_sticky_late_close_failure(module,tmp_path,monkeypatch,fail_close):
    """Only synthetic endpoints and callbacks are used; no child is launched."""
    class FixtureGuard:
        def __init__(self,*args):
            self.deadline = time.monotonic()+60
            self.child = None
        def __call__(self):
            pass
    class LateCloseFailure:
        def __init__(self,*args):
            self.closed = False
        def query_many(self,lines):
            return resolved_reply(lines)
        def close(self):
            if fail_close and not self.closed:
                self.closed = True
                raise RuntimeError('fixture late native close failure')
            self.closed = True
    captured = []
    def fixture_window(path,pin,side,count,source_id,guard,progress,receipt):
        receipt.update(path=str(tmp_path/'synthetic-source'),complete=True,window_rows=1,
                       endpoint_key_fill_rate=1.0,endpoint_legal_state_fill_rate=1.0)
        return records(module,source_id,wrong_clock=True),receipt
    dependency = tmp_path/'synthetic-dependency.json'
    dependency.write_text('{}')
    native = tmp_path/'synthetic-native.identity'
    native.write_text('synthetic identity only; no executable')
    pins = {str(Path(f'D:/grok-pc-data/selfplay_out/forge_selfplay_{number:03}.txt').resolve()).casefold():'0'*32
            for number in (12,13,14,15)}
    monkeypatch.setattr(module,'Guard',FixtureGuard)
    monkeypatch.setattr(module,'Native',LateCloseFailure)
    monkeypatch.setattr(module,'resource_guard',lambda *args,**kwargs: None)
    monkeypatch.setattr(module,'validate_qualification',lambda *args: None)
    monkeypatch.setattr(module,'validate_filter_qualification',lambda *args: None)
    monkeypatch.setattr(module,'load_pins',lambda *args: pins)
    monkeypatch.setattr(module,'read_window',fixture_window)
    monkeypatch.setattr(module,'_publish',lambda path,report: captured.append(json.loads(json.dumps(report))))
    digest = module.hashes(dependency)['md5']
    result = module.main(['--out',str(tmp_path/'output'),'--pins',str(dependency),
                          '--qualification',str(dependency),'--qualification-md5',digest,
                          '--filter-qualification',str(dependency),'--filter-qualification-md5',digest,
                          '--native',str(native),'--cpu','3'])
    assert len(captured) == 1
    if not fail_close:
        assert result == 0 and captured[0]['complete'] is True
        assert len(captured[0]['seams']) == 2
        assert all(seam['native_session_success'] and seam['bounded_no_link_status'] == 'PASS' for seam in captured[0]['seams'])
        return
    assert result == 2
    seam = captured[0]['seams'][0]
    assert seam['search']['complete'] is True
    assert seam['bounded_no_link_status'] == 'UNVERIFIED'
    assert seam['native_session_success'] is False
    assert seam['complete'] is False


def test_failed_close_with_closed_handle_cannot_be_retried_as_success(module,tmp_path):
    class CloseFailure:
        def __init__(self,stream):
            self.stream = stream
        def __getattr__(self,name):
            return getattr(self.stream,name)
        def close(self):
            self.stream.close()
            raise OSError('fixture close failed after closing handle')
    writer = module.ReceiptWriter(tmp_path/'parts',lambda: None)
    left,right = records(module,12)[0],records(module,13)[0]
    writer.query(left,right,1,1,module.PairEvidence(None,None,3,1))
    writer.opened['queries']['stream'] = CloseFailure(writer.opened['queries']['stream'])
    with pytest.raises(OSError,match='close failed'):
        writer.close()
    assert writer.opened['queries']['stream'].closed
    with pytest.raises(OSError,match='close|seal'):
        writer.close()
    assert not writer.artifacts
    assert not list((tmp_path/'parts').glob('*.bin'))
    writer.abort()


@pytest.mark.parametrize('positive',[False,True])
def test_receipt_failure_preserves_classification_and_marks_unrecorded_attempts(module,positive):
    class FailingReceipts:
        def query(self,*args):
            raise OSError('fixture query receipt failure')
        def positive(self,*args):
            raise AssertionError('positive receipt cannot precede failed query receipt')
    left = module.Population(records(module,12))
    right = module.Population(records(module,13,count=2,wrong_clock=not positive))
    first,report = module.count_candidates(left,right),{}
    with pytest.raises(OSError,match='query receipt'):
        module.search_candidates(left,right,first,lambda lines: resolved_reply(lines,positive),FailingReceipts(),report)
    assert report['attempted_pairs'] == 2 and report['query_attempts'] == 2
    assert sum(report['final_counts'].values()) == report['attempted_pairs']
    assert report['unqueried_pairs'] == 0 and report['unrecorded_query_attempts'] == 2
    assert report['receipt_accounting_complete'] is False and report['complete'] is False
    assert module.seam_verdict(first,report,receipts_complete=True,native_session_success=True) == 'UNVERIFIED'
