import importlib.util
from pathlib import Path
import sys

import chess
import pytest

TOOLS = Path('D:/a14/tools')
sys.path.insert(0, str(TOOLS))


@pytest.fixture(scope='module')
def module():
    spec = importlib.util.spec_from_file_location('r14_boundary_run', TOOLS / 'r14_boundary_run.py')
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def population(module, after=False, count=1):
    board = chess.Board()
    if after:
        board.push_uci('e2e4')
    return module.Population([module.parse_endpoint((board.fen(en_passant='fen')+' | 0 | 0.5').encode(),
                              13 if after else 12, index+1) for index in range(count)])


class Sink:
    def __init__(self):
        self.queries = []
        self.positives = []
    def query(self, left, right, depth, attempt, evidence):
        self.queries.append((left.line,right.line,depth,attempt,evidence.code))
    def positive(self, left, right, depth, evidence):
        self.positives.append((left.line,right.line,depth,evidence.witness))


def positive(lines):
    return [dict(id=line.split('\t')[0],status='REACHABLE',reason='legal_witness',
                 nodes=2,witness=['e2e4']) for line in lines]


def negative(lines):
    return [dict(id=line.split('\t')[0],status='UNREACHABLE',reason='exhaustive_no_path',
                 nodes=1,witness=[]) for line in lines]


def test_cross_window_straddle_fails_narrow_no_link_claim(module):
    left, right, sink = population(module,count=2), population(module,True,count=3), Sink()
    first = module.count_candidates(left,right)
    report = {}
    module.search_candidates(left,right,first,positive,sink,report)
    assert report['complete'] and report['attempted_pairs'] == 6
    assert report['final_counts']['REACHABLE'] == 6 and len(sink.positives) == 6
    assert module.no_link_verdict(first,report) == 'FAIL'


def test_resolved_negative_population_can_pass_narrow_claim(module):
    left,right,sink = population(module),population(module,True),Sink()
    first,report = module.count_candidates(left,right),{}
    module.search_candidates(left,right,first,negative,sink,report)
    assert module.no_link_verdict(first,report) == 'PASS'


def test_node_limit_unknown_is_retried_and_remains_unverified(module):
    def unknown(lines):
        return [dict(id=line.split('\t')[0],status='UNKNOWN',reason='node_limit',
                     nodes=int(line.split('\t')[-1]),witness=[]) for line in lines]
    left,right,sink = population(module),population(module,True),Sink()
    first,report = module.count_candidates(left,right),{}
    module.search_candidates(left,right,first,unknown,sink,report)
    assert report['attempted_pairs'] == 1 and report['query_attempts'] == 2
    assert report['final_counts']['UNKNOWN'] == 1
    assert [row[3] for row in sink.queries] == [1,2]
    assert module.no_link_verdict(first,report) == 'UNVERIFIED'


def test_transport_truncation_preserves_unknown_population(module):
    left,right,sink = population(module,count=2),population(module,True,count=3),Sink()
    first,report = module.count_candidates(left,right),{}
    with pytest.raises(module.TransportFailure):
        module.search_candidates(left,right,first,lambda lines: [],sink,report)
    assert not report['complete'] and report['final_counts']['UNKNOWN'] == 6
    assert module.no_link_verdict(first,report) == 'UNVERIFIED'


def test_unqueried_survivors_cannot_pass(module):
    left,right = population(module),population(module,True)
    first = module.count_candidates(left,right)
    report = dict(complete=False,attempted_pairs=0,final_counts={},unqueried_pairs=1)
    assert module.no_link_verdict(first,report) == 'UNVERIFIED'


def test_invalid_endpoint_population_cannot_pass(module):
    left = module.Population([None])
    right = population(module,True)
    first,report = module.count_candidates(left,right),{}
    module.search_candidates(left,right,first,positive,Sink(),report)
    assert report['complete'] and report['attempted_pairs'] == 0
    assert module.no_link_verdict(first,report) == 'UNVERIFIED'


def test_empty_window_cannot_pass(module):
    first = module.count_candidates(module.Population([]),population(module,True))
    assert module.no_link_verdict(first,dict(complete=True,attempted_pairs=0,final_counts={},unqueried_pairs=0)) == 'UNVERIFIED'


def test_binary_query_receipts_are_bounded_and_sealed(module,tmp_path):
    writer = module.ReceiptWriter(tmp_path/'parts',lambda: None,chunk_bytes=30)
    left,right = population(module).valid[0],population(module,True).valid[0]
    evidence = module.PairEvidence(None,None,3,1)
    for _ in range(3):
        writer.query(left,right,1,1,evidence)
    writer.close()
    assert module.QUERY_STRUCT.size == 15
    assert [item['records'] for item in writer.artifacts] == [2,1]
    assert [item['bytes'] for item in writer.artifacts] == [30,15]


def test_writer_hard_stop_abort_does_not_flush_tail(module,tmp_path):
    writer = module.ReceiptWriter(tmp_path/'parts',lambda: None)
    left,right = population(module).valid[0],population(module,True).valid[0]
    writer.query(left,right,1,1,module.PairEvidence(None,None,3,1))
    writer.abort()
    assert not writer.artifacts
    assert sum(path.stat().st_size for path in (tmp_path/'parts').glob('*')) == 0


def filter_report(module,tmp_path):
    path = tmp_path/'core.txt'
    path.write_text('synthetic identity fixture')
    identity = module.hashes(path)
    report = dict(schema=1,scope='boundary_filter_qualification',status='PASS',complete=True,
                  requested_random_pairs=100000,resolved_random_pairs=100000,rejected_legal_pairs=0,
                  special_pairs=12,special_failures=0,popcount_checks=100000,popcount_disagreements=0,
                  core=identity,tool_identities=[identity])
    return report,identity


def test_filter_qualification_gate_requires_resolved_foundation(module,tmp_path):
    report,identity = filter_report(module,tmp_path)
    report['resolved_random_pairs'] = 99999
    with pytest.raises(ValueError,match='resolved'):
        module.validate_filter_qualification(report,identity)


def test_filter_qualification_gate_rejects_smoke(module,tmp_path):
    report,identity = filter_report(module,tmp_path)
    report['scope'] = 'boundary_filter_smoke'
    with pytest.raises(ValueError,match='production'):
        module.validate_filter_qualification(report,identity)


def test_filter_qualification_gate_rejects_popcount_disagreement(module,tmp_path):
    report,identity = filter_report(module,tmp_path)
    report['popcount_disagreements'] = 1
    with pytest.raises(ValueError,match='failures'):
        module.validate_filter_qualification(report,identity)


def test_filter_qualification_gate_binds_dependency_bytes(module,tmp_path):
    report,identity = filter_report(module,tmp_path)
    Path(identity['path']).write_text('changed after qualification')
    with pytest.raises(ValueError,match='identity mismatch'):
        module.validate_filter_qualification(report,identity)


def test_receipt_seal_can_resume_after_guard_failure_with_closed_stream(module,tmp_path):
    writer = None
    refused = False
    def guard():
        nonlocal refused
        if writer is not None and not refused and any(item['stream'].closed for item in writer.opened.values()):
            refused = True
            raise TimeoutError('fixture interruption after close')
    writer = module.ReceiptWriter(tmp_path/'parts',guard)
    left,right = population(module).valid[0],population(module,True).valid[0]
    writer.query(left,right,1,1,module.PairEvidence(None,None,3,1))
    with pytest.raises(TimeoutError,match='after close'):
        writer.close()
    assert not writer.artifacts
    writer.close()
    assert len(writer.artifacts) == 1 and writer.artifacts[0]['records'] == 1


def test_unsealed_receipts_cannot_yield_per_seam_pass(module):
    left,right,sink = population(module),population(module,True),Sink()
    first,report = module.count_candidates(left,right),{}
    module.search_candidates(left,right,first,negative,sink,report)
    assert module.seam_verdict(first,report,receipts_complete=False,native_session_success=True) == 'UNVERIFIED'
    assert module.seam_verdict(first,report,receipts_complete=True,native_session_success=True) == 'PASS'
