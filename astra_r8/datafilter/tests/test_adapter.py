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

def test_native_cleanup_on_conversion_exception(monkeypatch):
    import npt_adapter as a
    native_get = a.data_loader.get_sparse_batch_from_fens
    native_free = a.data_loader.destroy_sparse_batch
    allocations, freed = [], []
    class Broken:
        @property
        def contents(self):
            raise RuntimeError('injected tensor conversion')
    def get(*args):
        allocations.append(native_get(*args)); return Broken()
    def free(ptr):
        freed.append(ptr); native_free(allocations[-1])
    monkeypatch.setattr(a.data_loader,'get_sparse_batch_from_fens',get)
    monkeypatch.setattr(a.data_loader,'destroy_sparse_batch',free)
    with pytest.raises(RuntimeError, match='injected'):
        a.make_batch(rows(),'K32H3','filtered_eval_v1')
    assert len(freed) == 1

def test_distributed_rejected(monkeypatch):
    from npt_adapter import make_batch
    monkeypatch.setenv('WORLD_SIZE','2')
    with pytest.raises(ValueError,match='one process'):
        make_batch(rows(),'K32H3','filtered_eval_v1')

def test_actual_feature_and_model_forward_contract():
    import torch
    from npt_adapter import MaskedNNUE, make_batch
    from model.config import NNUEConfig
    cfg = NNUEConfig(); cfg.features = 'K32H3^'; cfg.model_config.L1 = 8
    model = MaskedNNUE(cfg, max_epoch=8, num_batches_per_epoch=2)
    batch = make_batch(rows(), model.model.input_feature_name, 'filtered_wdl_v1')
    with torch.no_grad():
        loss = model.compute_loss(batch, 0)
    assert loss.ndim == 0 and torch.isfinite(loss)
    assert model._metadata is None and model.lambda_scheduler.pending is None

def test_command_contract():
    from train_adapter import command
    args = command('manifest.json','new-output','cpu')
    for key, value in [('--features','K32H3^'),('--l1','1024'),('--batch-size','16384'),('--epoch-size','152500000'),('--max-epochs','8'),('--lr','0.000875'),('--gamma','0.72'),('--seed','5108')]:
        assert args[args.index(key)+1] == value
    with pytest.raises(ValueError):
        command('manifest','out','cuda:0,1')

def test_native_black_result_and_mirror_features():
    import torch
    from npt_adapter import make_batch
    from records import selfplay_record
    fen='7k/8/8/8/4Q3/8/8/K7 b - - 17 81'
    r=selfplay_record(f'{fen} | -900 | 1','fixture',1)
    m=selfplay_record(f'{chess.Board(fen).mirror().fen()} | -900 | 0','fixture',2)
    a=make_batch([r],'K32H3','filtered_wdl_v1')
    b=make_batch([m],'K32H3','filtered_wdl_v1')
    assert a[4].item()==b[4].item()==0
    assert a[5].item()==b[5].item()==-900
    # Feature sums are permutation-invariant; board mirroring reverses enumeration.
    assert torch.equal(a[2].sort().values,b[3].sort().values) and torch.equal(a[3].sort().values,b[2].sort().values)

def test_validation_does_not_advance_training_sampler(tmp_path):
    from npt_adapter import RowFile,Sampler,BatchStream
    from records import dumps
    from filter_positions import sha256
    p=tmp_path/'rows.jsonl'; p.write_text('\n'.join(map(dumps,rows()))+'\n')
    f=RowFile(p,sha256(p)); s=Sampler(3,5108,'manifest')
    stream=BatchStream(f,s,2,2,'K32H3','filtered_wdl_v1',validation=True)
    first=list(stream); second=list(stream)
    assert s.cursor==0
    assert [b[8]['source_row'] for b in first]==[b[8]['source_row'] for b in second]

def test_checkpoint_identity_and_epoch_boundary():
    from train_adapter import resume_epoch
    assert resume_epoch(9307,9307*16384)==1
    with pytest.raises(ValueError,match='epoch-boundary'):
        resume_epoch(1,16384)
    with pytest.raises(ValueError,match='cursor'):
        resume_epoch(9307,0)

def test_native_logger_interface(tmp_path):
    from npt_adapter import BatchStream, RowFile, Sampler
    from records import dumps
    from filter_positions import sha256
    from trainer.callbacks import UniquePositionLogger
    from types import SimpleNamespace
    p=tmp_path/'rows.jsonl'; p.write_text('\n'.join(map(dumps,rows()))+'\n')
    stream=BatchStream(RowFile(p,sha256(p)),Sampler(3,5108,'manifest'),1,2,'K32H3','filtered_eval_v1')
    logger=UniquePositionLogger(stream.dataset)
    logger.on_train_epoch_end(SimpleNamespace())
    assert logger._merged_hll_state is None

def test_nonzero_device_rank_rejected(monkeypatch):
    from train_adapter import command
    from npt_adapter import single_process
    with pytest.raises(ValueError):
        command('manifest','out','cuda:1')
    monkeypatch.setenv('LOCAL_RANK','1')
    with pytest.raises(ValueError):
        single_process()
