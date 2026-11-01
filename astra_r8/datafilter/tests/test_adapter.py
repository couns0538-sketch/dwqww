import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chess
from records import record

def rows():
    return [record(chess.STARTING_FEN, 100, 'cp', 1, 'fixture', 1, 'selfplay'),
            record(chess.STARTING_FEN.replace(' w ', ' b '), -200, 'cp', None, 'fixture', 2, 'selfplay'),
            record(chess.STARTING_FEN, 300, 'cp', None, 'fixture', 3, 'lichess')]

def test_native_batch_lifetime_and_mask():
    import torch
    from npt_adapter import make_batch
    b = make_batch(rows(), 'K32H3', 'filtered_wdl_v1')
    tensors, meta = b[:8], b[8]
    assert len(tensors) == 8 and all(t.device.type == 'cpu' for t in tensors)
    assert tensors[4].flatten().tolist() == [1, 0.5, 0.5]
    assert tensors[5].flatten().tolist() == [100, -200, 300]
    assert meta['has_result'] == [True, False, False]
    assert meta['source_kind'] == ['selfplay', 'selfplay', 'lichess']
    assert meta['lambda'] == [0.8, 1.0, 1.0]
    copies = [x.clone() for x in tensors]
    for _ in range(8):
        make_batch(rows()[::-1], 'K32H3', 'filtered_eval_v1')
    assert all(torch.equal(a, b) for a, b in zip(tensors, copies))

def test_sampler_resume():
    from npt_adapter import Sampler
    a = Sampler(17, 5108, 'manifest-a')
    first = [a.next() for _ in range(17)]
    assert sorted(first) == list(range(17))
    state = a.state_dict()
    b = Sampler(17, 5108, 'manifest-a'); b.load_state_dict(state)
    assert [a.next() for _ in range(40)] == [b.next() for _ in range(40)]
    with pytest.raises(ValueError):
        Sampler(17, 5108, 'manifest-b').load_state_dict(state)

def test_masked_loss_parity_and_reset():
    import torch
    from npt_adapter import MaskedNNUE, RowLambda, make_batch
    from model.config import NNUEConfig
    from model.nnue import NNUE, calculate_sf_loss
    # Exercise installed loss/scaling without allocating the ~GB L1024 feature transformer.
    from types import SimpleNamespace
    model = MaskedNNUE.__new__(MaskedNNUE)
    torch.nn.Module.__init__(model)
    model.model = SimpleNamespace(quantization=SimpleNamespace(nnue2score=600.0))
    model.config = NNUEConfig()
    model.max_steps = 10
    model.optimizer_wrapper = None
    model.lambda_scheduler = RowLambda()
    model._sf_loss_fn = calculate_sf_loss
    batch = make_batch(rows(), 'K32H3', 'filtered_wdl_v1')
    prediction = torch.tensor([[0.1], [-0.3], [0.2]])
    actual = model.compute_loss_with_scorenet(prediction, batch, 0)
    expected = torch.stack([calculate_sf_loss(prediction[i:i+1]*600, batch[5][i:i+1], batch[4][i:i+1], model.config.loss_params, batch[8]['lambda'][i]) for i in range(3)]).mean()
    assert torch.allclose(actual, expected, atol=1e-8)
    assert model.lambda_scheduler.pending is None
    model.eval()
    val = make_batch(rows(), 'K32H3', 'filtered_eval_v1')
    assert torch.allclose(model.compute_loss_with_scorenet(prediction,val,0), calculate_sf_loss(prediction*600,val[5],val[4],model.config.loss_params,1.0))
    assert model.lambda_scheduler.pending is None
    model._sf_loss_fn = lambda *args: (_ for _ in ()).throw(RuntimeError('injected loss failure'))
    with pytest.raises(RuntimeError, match='injected'):
        model.compute_loss_with_scorenet(prediction,batch,0)
    assert model.lambda_scheduler.pending is None

def test_row_lambda_shape_rejection():
    import torch
    from npt_adapter import RowLambda
    from model.config import LossParams
    controller = RowLambda(); controller.pending = torch.ones(3)
    with pytest.raises(ValueError, match='shape'):
        controller(LossParams(),0,10,True,torch.ones(3,1))
