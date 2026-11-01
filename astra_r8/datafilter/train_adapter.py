"""Crew-owned training entry point. This job invokes only --check. UNPROVEN."""
import argparse
import json
import os
from pathlib import Path
import sys
from npt_adapter import (BatchStream, MaskedNNUE, RowFile, Sampler, NPT,
                         runtime_identity, single_process, torch)
from filter_positions import sha256, low_priority

def resume_epoch(global_step, sampler_cursor):
    if sampler_cursor != global_step * 16384:
        raise ValueError('checkpoint sampler cursor differs from completed steps')
    if global_step % 9307:
        raise ValueError('only epoch-boundary training resume is supported')
    return global_step // 9307

class Context:
    def __init__(self, manifest_path, recipe):
        self.manifest_path = Path(manifest_path).resolve()
        self.manifest = json.loads(self.manifest_path.read_text(encoding='utf-8'))
        self.recipe = recipe
        self.digest = sha256(self.manifest_path)
        self.train_rows = RowFile(self.manifest['train']['path'], self.manifest['train']['sha256'])
        self.val_rows = RowFile(self.manifest['validation']['path'], self.manifest['validation']['sha256'])
        self.sampler = Sampler(len(self.train_rows.offsets), 5108, self.digest)
        self.runtime = None

    def state_dict(self):
        return dict(manifest=self.digest, recipe=self.recipe, sampler=self.sampler.state_dict(), runtime=self.runtime)

    def load_state_dict(self, state):
        if state.get('manifest') != self.digest or state.get('recipe') != self.recipe or state.get('runtime') != self.runtime:
            raise ValueError('checkpoint manifest/recipe/runtime mismatch')
        self.sampler.load_state_dict(state['sampler'])

    def loaders(self, train_filenames, val_filenames, feature_name, num_workers,
                batch_size, config, io_config, epoch_size, val_size, pin_memory,
                queue_size_limit, prefetch_device=None, rank=0, world_size=1):
        single_process()
        if rank != 0 or world_size != 1 or num_workers != 0 or batch_size > 16384:
            raise ValueError('unsupported worker/device/batch configuration')
        if list(map(str, train_filenames)) != [str(self.manifest_path)] or list(map(str,val_filenames or [])) != [str(self.manifest_path)]:
            raise ValueError('unexpected dataset arguments')
        train = BatchStream(self.train_rows,self.sampler,max(1,epoch_size//batch_size),batch_size,feature_name,self.recipe)
        val_sampler = Sampler(len(self.val_rows.offsets),5108,self.digest)
        val = BatchStream(self.val_rows,val_sampler,max(1,val_size//batch_size),batch_size,feature_name,self.recipe,validation=True)
        return train, val

def command(manifest, output, device, resume=None):
    if device not in ('cpu','cuda:0'):
        raise ValueError('only cpu or logical cuda:0 is supported')
    args = [str(NPT/'train.py'), str(manifest), '--validation-datasets', str(manifest),
            '--default-root-dir', str(output), '--features', 'K32H3^', '--l1', '1024',
            '--batch-size', '16384', '--epoch-size', '152500000', '--max-epochs', '8',
            '--lr', '0.000875', '--gamma', '0.72', '--seed', '5108', '--num-workers', '0',
            '--threads', '2', '--validation-size', '16384', '--swa-start-epoch', '-1',
            '--network-save-period', '2', '--save-top-k', '2', '--lambda', '1.0',
            '--accelerator', 'cpu' if device == 'cpu' else 'cuda']
    if device != 'cpu':
        args += ['--gpus',device[5:]]
    if resume:
        args += ['--resume-from-checkpoint',str(resume)]
    return args

def make_trainer_class(base, context):
    class AdapterTrainer(base):
        def load_checkpoint(self, path):
            raw = torch.load(path,map_location='cpu',weights_only=False)
            states=raw.get('lr_schedulers')
            if not isinstance(states,list) or len(states)!=len(self._schedulers) or len(states)!=1:
                raise ValueError('missing or mismatched scheduler state')
            if 'last_epoch' not in states[0]:
                raise ValueError('malformed scheduler state')
            checkpoint = super().load_checkpoint(path)
            self.current_epoch = resume_epoch(self.global_step,context.sampler.cursor)
            # Installed CheckpointManager saves at epoch end before StepLR advances.
            for scheduler in self._schedulers:
                if not isinstance(scheduler,torch.optim.lr_scheduler.StepLR):
                    raise ValueError('only pinned StepLR recipe resume is supported')
                if scheduler.last_epoch == self.current_epoch-1:
                    scheduler.step()
                elif scheduler.last_epoch != self.current_epoch:
                    raise ValueError('checkpoint scheduler/epoch mismatch')
            return checkpoint
    return AdapterTrainer

def install(context, train):
    MaskedNNUE.adapter_context = context
    train.M.NNUE = MaskedNNUE
    train.make_data_loaders = context.loaders
    train.SimpleTrainer = make_trainer_class(train.SimpleTrainer,context)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--recipe',choices=['filtered_eval_v1','filtered_wdl_v1'],required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--device',default='cpu')
    p.add_argument('--resume',type=Path)
    p.add_argument('--check',action='store_true')
    a = p.parse_args()
    single_process(); low_priority()
    context = Context(a.manifest,a.recipe)
    if context.manifest.get('training_ready') is not True:
        raise ValueError('manifest has no full holdout clearance; training blocked')
    import train
    context.runtime = runtime_identity()
    if context.runtime != context.manifest['runtime']:
        raise ValueError('installed npt runtime changed from manifest')
    args = command(a.manifest.resolve(), a.output.resolve(),a.device,a.resume)
    if a.check:
        print(json.dumps(dict(status='PASS', command=args, identity=context.state_dict()),indent=2))
        return
    if a.resume is None and a.output.exists():
        raise FileExistsError('refusing existing training output')
    if a.resume is not None and not a.resume.is_file():
        raise ValueError('missing checkpoint')
    # Runtime hooks are confined to this interpreter. Installed files stay unchanged.
    install(context,train)
    sys.argv = args
    train.main()

if __name__ == '__main__':
    main()
