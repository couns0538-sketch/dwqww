"""CPU construction/checkpoint tests. Never invoke a training step or optimizer update."""
import json
import sys
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from test_adapter import rows

def context(tmp_path):
    from records import dumps
    from filter_positions import sha256
    from train_adapter import Context
    p=tmp_path/'rows.jsonl'; p.write_text('\n'.join(map(dumps,rows()))+'\n')
    m=tmp_path/'manifest.json'; m.write_text(json.dumps({'train':{'path':str(p),'sha256':sha256(p)},'validation':{'path':str(p),'sha256':sha256(p)}}))
    return Context(m,'filtered_wdl_v1')

def test_installed_entrypoint_constructs_without_training(tmp_path,monkeypatch):
    import torch
    import train
    import model
    from npt_adapter import MaskedNNUE
    from train_adapter import command,install
    ctx=context(tmp_path)
    original_nnue=model.NNUE; original_loader=train.make_data_loaders; original_trainer=train.SimpleTrainer
    class ConstructionComplete(Exception): pass
    class NoTraining(original_trainer):
        def fit(self,train_loader,val_loader):
            batch=next(iter(train_loader))
            assert len(batch)==9 and batch[5].shape==(2,1)
            self.callbacks[0].on_train_epoch_end(self)
            assert len(next(iter(val_loader)))==9
            raise ConstructionComplete()
    monkeypatch.setattr(train,'SimpleTrainer',NoTraining)
    try:
        install(ctx,train)
        args=command(ctx.manifest_path,tmp_path/'run','cpu')
        for flag,value in [('--l1','8'),('--batch-size','2'),('--epoch-size','4'),('--validation-size','4'),('--threads','1')]:
            args[args.index(flag)+1]=value
        args+=['--async-checkpoint-save','False']
        monkeypatch.setattr(sys,'argv',args)
        with pytest.raises(ConstructionComplete):
            train.main()
    finally:
        model.NNUE=original_nnue; train.make_data_loaders=original_loader; train.SimpleTrainer=original_trainer
        MaskedNNUE.adapter_context=None

def build_trainer(ctx,tmp_path):
    import torch
    import train
    from npt_adapter import MaskedNNUE
    from model.config import NNUEConfig
    from trainer.engine import SimpleTrainer
    from train_adapter import make_trainer_class
    cfg=NNUEConfig(); cfg.features='K32H3^'; cfg.model_config.L1=8
    cfg.optimizer_config.gamma=0.72
    m=MaskedNNUE(cfg,max_epoch=8,num_batches_per_epoch=9307)
    m.adapter_context=ctx
    opt,sch=train._normalize_optimizer_and_schedulers(m.configure_optimizers())
    cls=make_trainer_class(SimpleTrainer,ctx)
    return cls(model=m,optimizer=opt,schedulers=sch,max_epochs=8,check_val_every_n_epoch=1,
               gradient_clip_val=2.0,log_every_n_steps=1,default_root_dir=str(tmp_path),
               callbacks=[],logger=[],device=torch.device('cpu'),rank=0,world_size=1,local_rank=0)

@pytest.mark.parametrize('already_stepped',[False,True])
def test_real_checkpoint_sampler_lr_restore(tmp_path,already_stepped):
    import torch
    ctx=context(tmp_path); ctx.runtime={'pin':'fixture'}
    t=build_trainer(ctx,tmp_path)
    t.current_epoch=0; t.global_step=9307; ctx.sampler.cursor=9307*16384
    if already_stepped:
        with pytest.warns(UserWarning): t._schedulers[0].step()
    ckpt=tmp_path/'checkpoint.pt'; t.save_checkpoint(str(ckpt))
    state=ctx.sampler.state_dict(); ctx.sampler.cursor=0
    restored=build_trainer(ctx,tmp_path)
    restored.load_checkpoint(str(ckpt))
    assert restored.current_epoch==1 and ctx.sampler.state_dict()==state
    assert restored._schedulers[0].last_epoch==1
    assert restored.optimizer.param_groups[0]['lr']==pytest.approx(0.000875*0.72)
    assert restored.model.lambda_scheduler.pending is None
    raw=torch.load(ckpt,weights_only=False); raw.pop('lr_schedulers')
    bad=tmp_path/'bad.pt'; torch.save(raw,bad)
    with pytest.raises(ValueError,match='scheduler'):
        restored.load_checkpoint(str(bad))
    raw['lr_schedulers']=[{}]; torch.save(raw,tmp_path/'malformed.pt')
    with pytest.raises(ValueError,match='scheduler'):
        restored.load_checkpoint(str(tmp_path/'malformed.pt'))
