"""Original bounded adapter calling installed npt APIs; no npt code copied. UNPROVEN."""
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
from array import array

NPT = Path(os.environ.get('ASTRA_NPT_ROOT', 'F:/opus_scratch/r6/nnue-pytorch-amd')).resolve()
sys.path.insert(0, str(NPT))
os.environ.setdefault('NNUE_DATA_LOADER_LIB', str(NPT/'build/libtraining_data_loader.dll'))
import torch
import data_loader
from model.nnue import NNUE
from model.lambda_utils import LambdaController
from records import validate_record
from filter_positions import input_identity, sha256

def single_process():
    if int(os.environ.get('WORLD_SIZE', '1')) != 1 or int(os.environ.get('RANK', '0')) != 0 or int(os.environ.get('LOCAL_RANK','0')) != 0 or torch.utils.data.get_worker_info() is not None:
        raise ValueError('adapter supports one process/device and zero loader workers only')
    if torch.distributed.is_available() and torch.distributed.is_initialized() and torch.distributed.get_world_size() != 1:
        raise ValueError('distributed adapter execution unsupported')


def native_fen(row):
    """Admit full state and canonicalize only the installed ABI's FEN argument."""
    validate_record(row)
    fields = row['fen'].split()
    if (row['score_type'] != 'cp' or not -32768 <= row['score_stm'] <= 32767
            or not 0 <= row['ply'] <= 65534 or not 0 <= int(fields[4]) <= 255):
        raise ValueError('native score/ply/halfmove range or type unsupported')
    # The native parser requires single spaces, uint8 rule-50, and uint16
    # internal ply (one greater than our zero-based metadata ply).
    return ' '.join(fields[:4] + [str(int(value)) for value in fields[4:]])


def make_batch(rows, feature_name, recipe):
    single_process()
    if recipe not in ('filtered_eval_v1', 'filtered_wdl_v1'):
        raise ValueError('unknown recipe')
    if not rows or len(rows) > 16384:
        raise ValueError('batch must contain 1..16384 rows')
    fens = [native_fen(row) for row in rows]
    native = data_loader.get_sparse_batch_from_fens(
        feature_name, fens, [r['score_stm'] for r in rows],
        [r['ply'] for r in rows], [r['result_stm'] if r['has_result'] else 0 for r in rows])
    if not native:
        raise ValueError('native feature batch unavailable')
    try:
        borrowed = native.contents.get_tensors('cpu', use_pinned_memory=False)
        if len(borrowed) != 8:
            raise ValueError('expected eight native tensors')
        owned = tuple(t.clone() for t in borrowed)
    finally:
        data_loader.destroy_sparse_batch(native)
    metadata = {key: [r[key] for r in rows] for key in ('source','source_row','source_kind','has_result','result_stm','fen','ply')}
    # Native ABI has no unknown-result sentinel. Its dummy 0 is never a semantic draw:
    # the separate mask forces lambda=1 and retains null in result_stm.
    metadata['lambda'] = [0.8 if recipe == 'filtered_wdl_v1' and r['source_kind'] == 'selfplay' and r['has_result'] else 1.0 for r in rows]
    return (*owned, metadata)

class RowLambda(LambdaController):
    def __init__(self):
        super().__init__()
        self.pending = None

    def forward(self, loss_params, current_step, max_steps, is_training, scorenet):
        value = self.pending
        if value is None:
            raise ValueError('missing per-row lambda')
        if value.shape != scorenet.shape or value.ndim != 2 or value.shape[1] != 1:
            raise ValueError('lambda shape must be [batch, 1]')
        if value.device != scorenet.device or value.dtype != scorenet.dtype:
            raise ValueError('lambda device/dtype must match score')
        return value

class MaskedNNUE(NNUE):
    adapter_context = None

    def __init__(self, *args, **kwargs):
        single_process()
        super().__init__(*args, **kwargs)
        self.lambda_scheduler = RowLambda()
        self._metadata = None

    def compute_loss(self, batch, current_step):
        if len(batch) != 9:
            raise ValueError('masked batch requires provenance')
        self._metadata = batch[8]
        try:
            return super().compute_loss(batch[:8], current_step)
        finally:
            self._metadata = None
            self.lambda_scheduler.pending = None

    def compute_loss_with_scorenet(self, scorenet, batch, current_step):
        metadata = batch[8] if len(batch) == 9 else self._metadata
        try:
            keys = ('lambda','source','source_row','source_kind','has_result','result_stm','fen','ply')
            if metadata is None or any(len(metadata[key]) != batch[5].shape[0] for key in keys):
                raise ValueError('missing or misaligned row metadata')
            for mask, lam in zip(metadata['has_result'], metadata['lambda']):
                if (not mask and lam != 1.0) or lam not in (0.8, 1.0):
                    raise ValueError('invalid result mask/lambda')
            self.lambda_scheduler.pending = batch[5].new_tensor(metadata['lambda']).reshape(-1, 1)
            return super().compute_loss_with_scorenet(scorenet, batch[:8], current_step)
        finally:
            self.lambda_scheduler.pending = None

    def on_save_checkpoint(self, checkpoint):
        super().on_save_checkpoint(checkpoint)
        if self.adapter_context is None:
            raise ValueError('adapter checkpoint context missing')
        checkpoint['astra_data'] = self.adapter_context.state_dict()

    def on_load_checkpoint(self, checkpoint, resuming):
        if self.adapter_context is None or 'astra_data' not in checkpoint:
            raise ValueError('checkpoint has no pinned adapter manifest')
        self.adapter_context.load_state_dict(checkpoint['astra_data'])
        self.lambda_scheduler.pending = None
        self._metadata = None
        super().on_load_checkpoint(checkpoint, resuming)

class Sampler:
    """O(1) state affine permutations; exact deterministic resume, not a fast loader."""
    def __init__(self, count, seed, manifest):
        if count < 1:
            raise ValueError('empty dataset')
        self.count, self.seed, self.manifest, self.cursor = count, seed, manifest, 0

    def next(self):
        epoch, offset = divmod(self.cursor, self.count)
        rng = random.Random(self.seed + epoch)
        multiplier = rng.randrange(1, self.count + 1)
        while math.gcd(multiplier, self.count) != 1:
            multiplier = multiplier % self.count + 1
        shift = rng.randrange(self.count)
        index = (multiplier * offset + shift) % self.count
        self.cursor += 1
        return index

    def state_dict(self):
        return dict(count=self.count, seed=self.seed, manifest=self.manifest, cursor=self.cursor, algorithm='affine-v1')

    def load_state_dict(self, state):
        expected = self.state_dict()
        if any(state.get(k) != expected[k] for k in ('count','seed','manifest','algorithm')) or type(state.get('cursor')) is not int or state['cursor'] < 0:
            raise ValueError('sampler identity mismatch')
        self.cursor = state['cursor']

class RowFile:
    def __init__(self, path, expected_hash):
        self.path = Path(path).absolute()
        self.identity = input_identity(self.path)
        if self.identity['sha256'] != expected_hash:
            raise ValueError('record hash mismatch')
        self.offsets = array('Q')
        with open(self.path, 'rb') as fh:
            self._check_identity(fh)
            while True:
                offset = fh.tell()
                if not fh.readline():
                    break
                self.offsets.append(offset)
            self._check_identity(fh)
        if input_identity(self.path) != self.identity:
            raise ValueError('records changed while indexing')

    def _check_identity(self, handle=None):
        if str(self.path.resolve()) != self.identity['path']:
            raise ValueError('record path identity changed after pinning')
        observations = [(self.path.stat(), False)]
        if handle is not None:
            observations.append((os.fstat(handle.fileno()), True))
        fields = (('device', 'st_dev'), ('inode', 'st_ino'), ('bytes', 'st_size'),
                  ('mtime_ns', 'st_mtime_ns'), ('ctime_ns', 'st_ctime_ns'))
        for observed, is_handle in observations:
            for key, field in fields:
                # Windows Python can report birth time for path stat but change
                # time for fstat. Keep the full path pin; compare the handle's
                # device/file ID, size and mtime without conflating those clocks.
                if is_handle and os.name == 'nt' and key == 'ctime_ns':
                    continue
                if getattr(observed, field) != self.identity[key]:
                    raise ValueError('record file/handle identity changed after pinning')

    def fetch(self, indices):
        self._check_identity()
        with open(self.path, 'rb') as fh:
            self._check_identity(fh)
            rows = []
            for i in indices:
                fh.seek(self.offsets[i]); rows.append(validate_record(json.loads(fh.readline())))
            self._check_identity(fh)
        return rows

class BatchStream:
    def __init__(self, row_file, sampler, batches, batch_size, feature, recipe, validation=False):
        self.rows, self.sampler, self.batches = row_file, sampler, batches
        self.batch_size, self.feature, self.recipe, self.validation = batch_size, feature, recipe, validation
        self.dataset = self

    def get_unique_stats(self):
        raise NotImplementedError('bounded Python adapter does not measure HLL unique counts')

    def get_hll_state(self):
        # Installed logger explicitly skips HLL reporting for empty state.
        return b''

    def __len__(self):
        return self.batches

    def __iter__(self):
        single_process()
        sampler = Sampler(self.sampler.count,self.sampler.seed,self.sampler.manifest) if self.validation else self.sampler
        for _ in range(self.batches):
            indices = [sampler.next() for _ in range(self.batch_size)]
            yield make_batch(self.rows.fetch(indices), self.feature, self.recipe)

def runtime_identity():
    paths = {str(Path(m.__file__).resolve()) for m in list(sys.modules.values())
             if getattr(m, '__file__', None) and Path(m.__file__).resolve().is_relative_to(NPT)}
    paths.add(str(Path(os.environ['NNUE_DATA_LOADER_LIB']).resolve()))
    paths.update(str(Path(__file__).resolve().parent/name) for name in ('npt_adapter.py','train_adapter.py','records.py'))
    return dict(python=sys.version, torch=torch.__version__, files={p:sha256(p) for p in sorted(paths)})
