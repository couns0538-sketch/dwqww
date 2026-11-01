"""Original bounded adapter calling installed npt APIs; no npt code copied. UNPROVEN."""
import hashlib
import json
import os
from pathlib import Path
import sys
from array import array
import numpy as np

# Installed npt (GPL; never vendored here). Location from ASTRA_NPT_ROOT (train_adapter --npt-root),
# default a D: install; no dependency on any agent scratch tree.
DEFAULT_NPT_ROOT = 'D:/grok-pc-data/npt/nnue-pytorch-amd'
NPT = Path(os.environ.get('ASTRA_NPT_ROOT') or DEFAULT_NPT_ROOT).resolve()
if not (NPT / 'train.py').is_file():
    raise ImportError(f'installed npt not found at {NPT}; set ASTRA_NPT_ROOT or pass --npt-root')
sys.path.insert(0, str(NPT))
os.environ.setdefault('NNUE_DATA_LOADER_LIB', str(NPT/'build/libtraining_data_loader.dll'))
import torch
import data_loader
from model.nnue import NNUE
from model.lambda_utils import LambdaController
from records import validate_record
from filter_positions import sha256

def single_process():
    if int(os.environ.get('WORLD_SIZE', '1')) != 1 or int(os.environ.get('RANK', '0')) != 0 or int(os.environ.get('LOCAL_RANK','0')) != 0 or torch.utils.data.get_worker_info() is not None:
        raise ValueError('adapter supports one process/device and zero loader workers only')
    if torch.distributed.is_available() and torch.distributed.is_initialized() and torch.distributed.get_world_size() != 1:
        raise ValueError('distributed adapter execution unsupported')

COLUMNS = ('fen', 'score_stm', 'ply', 'result_stm', 'has_result', 'source', 'source_row', 'source_kind')

def check_native_row(r):
    """Full validation of one row; run once per row (at load for RowFile)."""
    validate_record(r)
    if r['score_type'] != 'cp' or not -32768 <= r['score_stm'] <= 32767 or not 0 <= r['ply'] <= 65535:
        raise ValueError('native score/ply range or type unsupported')

def make_batch(rows, feature_name, recipe):
    single_process()
    if not rows or len(rows) > 16384:
        raise ValueError('batch must contain 1..16384 rows')
    for r in rows:
        check_native_row(r)
    return make_batch_validated({key: [r[key] for r in rows] for key in COLUMNS}, feature_name, recipe)

def make_batch_validated(cols, feature_name, recipe):
    """Batch from already-validated column lists (see RowFile); no per-row revalidation."""
    single_process()
    if recipe not in ('filtered_eval_v1', 'filtered_wdl_v1'):
        raise ValueError('unknown recipe')
    n = len(cols['fen'])
    if not n or n > 16384 or any(len(cols[key]) != n for key in COLUMNS):
        raise ValueError('batch must contain 1..16384 aligned rows')
    native = data_loader.get_sparse_batch_from_fens(
        feature_name, cols['fen'], cols['score_stm'], cols['ply'],
        [res if known else 0 for res, known in zip(cols['result_stm'], cols['has_result'])])
    if not native:
        raise ValueError('native feature batch unavailable')
    try:
        borrowed = native.contents.get_tensors('cpu', use_pinned_memory=False)
        if len(borrowed) != 8:
            raise ValueError('expected eight native tensors')
        owned = tuple(t.clone() for t in borrowed)
    finally:
        data_loader.destroy_sparse_batch(native)
    metadata = {key: list(cols[key]) for key in ('source','source_row','source_kind','has_result','result_stm','fen','ply')}
    # Native ABI has no unknown-result sentinel. Its dummy 0 is never a semantic draw:
    # the separate mask forces lambda=1 and retains null in result_stm.
    metadata['lambda'] = [0.8 if recipe == 'filtered_wdl_v1' and kind == 'selfplay' and known else 1.0
                          for kind, known in zip(cols['source_kind'], cols['has_result'])]
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
    """Seeded per-pass full permutation ('perm-v1'); exact deterministic resume.
    Pass p (0-based, p = cursor // count) visits every row exactly once in the order
    numpy.random.default_rng([seed, p]).permutation(count); one pass is cached (8 bytes/row).
    Replaces the affine lattice ('affine-v1', CR N-1: later passes were same-game clusters).
    Not bit-identical to 7a8e22e8/81a44e65 batches: same rows and per-pass coverage, different order."""
    ALGORITHM = 'perm-v1'

    def __init__(self, count, seed, manifest):
        if count < 1:
            raise ValueError('empty dataset')
        if type(seed) is not int or seed < 0:
            raise ValueError('sampler seed must be a nonnegative int')
        self.count, self.seed, self.manifest, self.cursor = count, seed, manifest, 0
        self._pass = None

    def pass_order(self, p):
        if self._pass is None or self._pass[0] != p:
            self._pass = (p, np.random.default_rng([self.seed, p]).permutation(self.count))
        return self._pass[1]

    def next(self):
        p, offset = divmod(self.cursor, self.count)
        self.cursor += 1
        return int(self.pass_order(p)[offset])

    def take(self, n):
        parts = []
        while n > 0:
            p, offset = divmod(self.cursor, self.count)
            k = min(n, self.count - offset)
            parts.append(self.pass_order(p)[offset:offset + k])
            self.cursor += k; n -= k
        return np.concatenate(parts).tolist() if parts else []

    def order_check(self):
        """sha256 of pass 1's first 64 entries (int64 little-endian), from this numpy's Generator stream.
        Generator streams are not guaranteed across numpy versions (CR LOW-N1), so this is stored in the
        checkpoint and a resume whose stream differs fails closed. Computed once; does not touch the pass cache."""
        if getattr(self, '_order_check', None) is None:
            head = np.random.default_rng([self.seed, 1]).permutation(self.count)[:64]
            self._order_check = hashlib.sha256(np.ascontiguousarray(head, dtype='<i8').tobytes()).hexdigest()
        return self._order_check

    def state_dict(self):
        return dict(count=self.count, seed=self.seed, manifest=self.manifest, cursor=self.cursor, algorithm=self.ALGORITHM,
                    numpy_version=np.__version__, order_check=self.order_check())

    def load_state_dict(self, state):
        expected = self.state_dict()
        if any(state.get(k) != expected[k] for k in ('count','seed','manifest','algorithm')) or type(state.get('cursor')) is not int or state['cursor'] < 0:
            raise ValueError('sampler identity mismatch')
        if state.get('numpy_version') != expected['numpy_version']:
            raise ValueError(f"sampler numpy mismatch: checkpoint {state.get('numpy_version')!r}, running {expected['numpy_version']!r} (perm-v1 order is numpy-stream dependent; refusing to resume)")
        if state.get('order_check') != expected['order_check']:
            raise ValueError('sampler order_check mismatch: this numpy does not reproduce the checkpoint pass order; refusing to resume')
        self.cursor = state['cursor']

class RowFile:
    """Pinned JSONL rows, each fully validated exactly once at load into column lists."""
    def __init__(self, path, expected_hash):
        self.path = Path(path)
        if sha256(self.path) != expected_hash:
            raise ValueError('record hash mismatch')
        self.offsets = array('Q')
        self.cols = {key: [] for key in COLUMNS}
        with open(self.path, 'rb') as fh:
            while True:
                offset = fh.tell()
                line = fh.readline()
                if not line:
                    break
                r = json.loads(line)
                check_native_row(r)
                self.offsets.append(offset)
                for key in COLUMNS:
                    self.cols[key].append(r[key])
        if sha256(self.path) != expected_hash:
            raise ValueError('records changed while loading')
        self.identity = (self.path.stat().st_size, self.path.stat().st_mtime_ns)

    def _check_identity(self):
        if (self.path.stat().st_size,self.path.stat().st_mtime_ns) != self.identity:
            raise ValueError('records changed after pinning')

    def columns(self, indices):
        self._check_identity()
        return {key: [col[i] for i in indices] for key, col in self.cols.items()}

    def fetch(self, indices):
        """Full original rows (re-read from the pinned file); kept for audits/tests."""
        self._check_identity()
        with open(self.path, 'rb') as fh:
            rows = []
            for i in indices:
                fh.seek(self.offsets[i]); rows.append(json.loads(fh.readline()))
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
            yield make_batch_validated(self.rows.columns(sampler.take(self.batch_size)), self.feature, self.recipe)

def runtime_identity():
    paths = {str(Path(m.__file__).resolve()) for m in list(sys.modules.values())
             if getattr(m, '__file__', None) and Path(m.__file__).resolve().is_relative_to(NPT)}
    paths.add(str(Path(os.environ['NNUE_DATA_LOADER_LIB']).resolve()))
    paths.update(str(Path(__file__).resolve().parent/name) for name in ('npt_adapter.py','train_adapter.py','records.py'))
    return dict(python=sys.version, torch=torch.__version__, files={p:sha256(p) for p in sorted(paths)})
