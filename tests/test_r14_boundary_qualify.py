import importlib.util
from pathlib import Path
import sys

import chess
import pytest

TOOLS = Path('D:/a14/tools')
sys.path.insert(0,str(TOOLS))


@pytest.fixture(scope='module')
def module():
    spec = importlib.util.spec_from_file_location('r14_boundary_qualify',TOOLS/'r14_boundary_qualify.py')
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


class CaptureMate:
    def choice(self,moves):
        chosen = chess.Move.from_uci('h5f7')
        assert chosen in moves
        return chosen


def source_position():
    source = chess.Board()
    for token in ('e2e4','e7e5','f1c4','b8c6','d1h5','g8f6'):
        source.push_uci(token)
    return source


def test_discarded_partial_path_cannot_expose_completed_feature_coverage(module):
    source = source_position()
    original = source.fen()
    target = source.copy()
    assert target.is_capture(chess.Move.from_uci('h5f7'))
    target.push_uci('h5f7')
    assert target.is_checkmate()
    assert module.random_path(source,2,CaptureMate()) is None
    assert source.fen() == original


def test_completed_capture_path_retains_its_own_feature_counts(module):
    source = source_position()
    target,witness,features = module.random_path(source,1,CaptureMate())
    assert target.is_checkmate() and witness == ['h5f7']
    assert features == {'random_capture_moves':1}
    assert module.check_path(source,target)
