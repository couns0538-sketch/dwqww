#!/usr/bin/env python3
"""Supplemental CPU PyTorch smoke for the exact Forge AL1 residual architecture.

This does NOT run Bullet training. It exercises real FPOS/FHCE data, a complete
epoch over a bounded saved slice, and the lock export interchange. The matching
Bullet GPU graph is separate. No strength or generalization claim follows from
training loss on these same rows. Original code grounded in AL1 294dbed3's
nnue.hpp/nnue.cpp; format I/O reuses this project's forge_pos.py.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'data'))
from forge_pos import PosReader, PosWriter, file_hash, match_fen
import lock_export

LOCK_COMMIT = '294dbed3a15dfd821aaf9d4edc6e5f62832fd460'
HCE_COMMIT = '926c55f33227bc4a030d7ce5b1140528aeba75af'
K_OVER_400 = 2.25 / 400
SCALE = 4096
PROVENANCE = ('SUPPLEMENTAL_PYTORCH_CPU_SMOKE_NOT_BULLET_TRAINED: original Forge AL1 '
              '768->256 shared dual-perspective SCReLU residual graph; one bounded epoch; '
              'Bullet GPU training is blocked by unavailable CUDA/HIP devices and backend.')


def write_json(path: Path, value) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def artifact(path: Path) -> dict:
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': file_hash(path)}


def select_rows(pos: Path, hce: Path, fen: Path, out: Path, *, start: int, count: int) -> dict:
    """Save a contiguous, explicitly indexed slice with full sidecar alignment."""
    if type(start) is not int or start < 0 or type(count) is not int or not 1 <= count <= 65536:
        raise ValueError('start must be nonnegative and slice size must be 1..65536')
    codes = np.empty((count, 64), dtype=np.int64)
    stm = np.empty(count, dtype=np.int64)
    scores = np.empty(count, dtype=np.float32)
    hces = np.empty(count, dtype=np.float32)
    source_indices = list(range(start, start + count))
    with PosReader(pos, hce) as reader, fen.open(encoding='utf-8') as sidecar:
        if start + count > reader.n:
            raise ValueError('requested slice exceeds source row count')
        source_count = reader.n
        for _ in range(start):
            if not sidecar.readline():
                raise ValueError('FEN sidecar ends before selected slice')
        with PosWriter(out, 'subset', True, with_fen=True) as writer:
            for local, source in enumerate(source_indices):
                row = reader.row(source)
                line = sidecar.readline()
                if not line:
                    raise ValueError('FEN sidecar ends inside selected slice')
                normalized = match_fen(row, line)
                writer.append(row, normalized)
                packed = np.frombuffer(row.board, dtype=np.uint8)
                codes[local, 0::2], codes[local, 1::2] = packed & 15, packed >> 4
                stm[local], scores[local], hces[local] = row.meta & 1, row.score, row.hce
    return {'codes': codes, 'stm': stm, 'score': scores, 'hce': hces,
            'source_indices': source_indices, 'source_rows': source_count}


def dense_features(codes: np.ndarray, stm: np.ndarray) -> tuple[torch.Tensor, torch.Tensor]:
    """Board code and perspective mapping exactly follow nnue::feature_index."""
    codes = np.asarray(codes)
    stm = np.asarray(stm)
    if codes.ndim != 2 or codes.shape[1] != 64 or stm.shape != (len(codes),):
        raise ValueError('expected codes[N,64] and side-to-move[N]')
    if np.any((codes < 0) | (codes > 12)) or np.any((stm < 0) | (stm > 1)):
        raise ValueError('invalid piece code or side to move')
    rows, squares = np.nonzero(codes)
    occupied = codes[rows, squares] - 1
    colors, types = occupied // 6, occupied % 6
    result = []
    for perspective in (stm, 1 - stm):
        relative = colors != perspective[rows]
        oriented = squares ^ (56 * perspective[rows])
        features = (relative.astype(np.int64) * 6 + types) * 64 + oriented
        dense = np.zeros((len(codes), 768), dtype=np.float32)
        dense[rows, features] = 1
        result.append(torch.from_numpy(dense))
    return result[0], result[1]


def quantized_ste(value: torch.Tensor) -> torch.Tensor:
    """Int16/4096 QAT, matching export's f32->f64 ties-away quantization."""
    scaled = value.to(torch.float64) * SCALE
    quantized = torch.sign(scaled) * torch.floor(torch.abs(scaled) + .5)
    quantized = (quantized.clamp(-32767, 32767) / SCALE).to(torch.float32)
    return value + (quantized - value).detach()


class LockNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.ftw = nn.Parameter(torch.randn(768, 256) * .02)
        self.ftb = nn.Parameter(torch.zeros(256))
        self.outw = nn.Parameter(torch.zeros(2, 256))
        self.outb = nn.Parameter(torch.zeros(1))

    def residual(self, ours: torch.Tensor, theirs: torch.Tensor) -> torch.Tensor:
        w, b = quantized_ste(self.ftw), quantized_ste(self.ftb)
        own = (ours @ w + b).clamp(0, 1).square()
        opponent = (theirs @ w + b).clamp(0, 1).square()
        output = quantized_ste(self.outw)
        terms = own * output[0] + opponent * output[1]
        # Match AL1's sixteen fixed lanes, then ordered output-bias reduction.
        lanes = torch.zeros((len(ours), 16), dtype=torch.float32)
        for start in range(0, 256, 16):
            lanes = lanes + terms[:, start:start + 16]
        result = quantized_ste(self.outb).expand(len(ours))
        for lane in range(16):
            result = result + lanes[:, lane]
        return result

    def forward(self, ours, theirs, hce_cp):
        return self.residual(ours, theirs) + hce_cp * K_OVER_400

    @torch.no_grad()
    def project(self):
        for parameter in self.parameters():
            parameter.clamp_(-32767 / SCALE, 32767 / SCALE)

    def arrays(self):
        return {key: value.detach().cpu().numpy().copy() for key, value in self.state_dict().items()}


@torch.no_grad()
def measure(model, ours, theirs, hce, score, batch_size):
    total, residuals = 0., []
    for start in range(0, len(score), batch_size):
        part = slice(start, start + batch_size)
        residual = model.residual(ours[part], theirs[part])
        probability = torch.sigmoid(residual + hce[part] * K_OVER_400)
        target = torch.sigmoid(score[part] * K_OVER_400)
        total += float((probability - target).square().double().sum())
        residuals.append(residual.cpu().numpy())
    residuals = np.concatenate(residuals)
    return {'mse': total / len(score), 'rows': len(score),
            'residual_logit_min': float(residuals.min()), 'residual_logit_max': float(residuals.max()),
            'residual_logit_mean': float(residuals.astype(np.float64).mean())}


def train_epoch(model, ours, theirs, hce, score, *, batch_size, seed, learning_rate):
    if batch_size < 1 or not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError('positive batch size and finite positive learning rate required')
    generator = torch.Generator(device='cpu').manual_seed(seed)
    order = torch.randperm(len(score), generator=generator)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    batches, losses = [], []
    started = time.monotonic()
    for start in range(0, len(score), batch_size):
        if time.monotonic() - started > 600:
            raise RuntimeError('bounded CPU smoke exceeded ten-minute training budget')
        indices = order[start:start + batch_size]
        optimizer.zero_grad(set_to_none=True)
        prediction = torch.sigmoid(model(ours[indices], theirs[indices], hce[indices]))
        target = torch.sigmoid(score[indices] * K_OVER_400)
        loss = (prediction - target).square().mean()
        if not torch.isfinite(loss):
            raise ValueError('nonfinite training loss')
        loss.backward()
        if any(p.grad is None or not torch.isfinite(p.grad).all() for p in model.parameters()):
            raise ValueError('missing or nonfinite gradient')
        optimizer.step()
        model.project()
        batches.append(len(indices))
        losses.append(float(loss.detach()))
    return {'epochs_completed': 1, 'row_order': order.tolist(), 'batch_sizes': batches,
            'batch_losses': losses, 'optimizer_steps': len(batches), 'rows_seen': sum(batches),
            'tail_dropped': 0, 'training_seconds': time.monotonic() - started}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pos', 'hce', 'fen', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--rows', type=int, default=8192)
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--seed', type=int, default=20261030)
    parser.add_argument('--batch-size', type=int, default=128)
    parser.add_argument('--learning-rate', type=float, default=.003)
    parser.add_argument('--threads', type=int, choices=(1, 2), default=1)
    args = parser.parse_args(argv)
    if args.batch_size < 1 or not math.isfinite(args.learning_rate) or args.learning_rate <= 0:
        parser.error('positive batch size and finite positive learning rate required')
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(args.seed)
    command = [sys.executable, str(Path(__file__).resolve()), *(sys.argv[1:] if argv is None else argv)]
    write_json(args.out / 'command.json', {'argv': command, 'cwd': str(Path.cwd())})
    source_files = {name: artifact(getattr(args, name)) for name in ('pos', 'hce', 'fen')}
    print(json.dumps({'event': 'source_hashed', 'sources': source_files}), flush=True)
    selected = select_rows(args.pos, args.hce, args.fen, args.out, start=args.start, count=args.rows)
    write_json(args.out / 'selection.json', {
        'policy': 'contiguous source rows, zero-based; no score/HCE/result modification',
        'source_rows': selected['source_rows'], 'selected_rows': args.rows,
        'source_indices': selected['source_indices'], 'source_files': source_files,
        'scope': 'Complete one epoch only over this saved bounded slice, not all 10M input rows.'})
    ours, theirs = dense_features(selected['codes'], selected['stm'])
    hce, score = torch.from_numpy(selected['hce']), torch.from_numpy(selected['score'])
    model = LockNet()
    lock_export.write_checkpoint(args.out / 'initial', model.arrays(), PROVENANCE + ' Initial state.')
    initial = measure(model, ours, theirs, hce, score, args.batch_size)
    if initial['residual_logit_min'] != 0 or initial['residual_logit_max'] != 0:
        raise ValueError('residual initial state is not exactly HCE')
    print(json.dumps({'event': 'initial_loss', **initial}), flush=True)
    epoch = train_epoch(model, ours, theirs, hce, score, batch_size=args.batch_size,
                        seed=args.seed, learning_rate=args.learning_rate)
    final = measure(model, ours, theirs, hce, score, args.batch_size)
    write_json(args.out / 'epoch.json', epoch)
    manifest = lock_export.write_checkpoint(args.out / 'trained', model.arrays(), PROVENANCE)
    torch.save({'state_dict': model.state_dict(), 'architecture': lock_export.ARCH,
                'config': {'seed': args.seed, 'learning_rate': args.learning_rate, 'batch_size': args.batch_size,
                           'epochs': 1, 'rows': args.rows, 'threads': args.threads, 'residual': True},
                'provenance': PROVENANCE}, args.out / 'trained' / 'state.pt')
    q = lock_export.load_quantized(args.out / 'trained/weights.bin', args.out / 'trained/manifest.json')
    with (args.out / 'sample.inc').open('xb') as stream:
        stream.write(lock_export.render_include(q))
    implementation = [Path(__file__), ROOT / 'tools/bullet/lock_export.py',
                      ROOT / 'tools/bullet/export_forge.py', ROOT / 'tools/data/forge_pos.py']
    hce_paths = ['src/eval.cpp', 'include/forge/eval.hpp', 'src/eval_params.cpp',
                 'src/eval_params_table.inc', 'include/forge/eval_params.hpp']
    diff = subprocess.run(['git', '-C', str(ROOT), 'diff', LOCK_COMMIT, HCE_COMMIT, '--', *hce_paths],
                          capture_output=True, text=True, check=True)
    with (args.out / 'hce_source_diff.txt').open('x', encoding='utf-8') as stream:
        stream.write(diff.stdout)
    result = {
        'status': 'SUPPLEMENTAL_CPU_SMOKE_COMPLETE_NOT_BULLET_TRAINING', 'provenance': PROVENANCE,
        'architecture': lock_export.ARCH, 'lock_commit': LOCK_COMMIT, 'hce_source_commit': HCE_COMMIT,
        'hce_identity_scope': 'Relevant evaluation source diff saved; native AL1 subset HCE parity is a separate receipt.',
        'bullet_training': {'executed': False, 'status': 'BLOCKED_NO_SUPPORTED_GPU_BACKEND',
                            'bullet_commit': lock_export.common.BULLET_COMMIT},
        'device': 'cpu', 'torch': torch.__version__, 'numpy': np.__version__, 'python': sys.version,
        'platform': platform.platform(), 'threads': args.threads, 'seed': args.seed,
        'optimizer': 'Adam', 'learning_rate': args.learning_rate, 'batch_size': args.batch_size,
        'loss': 'MSE(sigmoid(HCE_cp*2.25/400 + residual), sigmoid(original_STM_score_cp*2.25/400))',
        'target_result_blend': 0, 'quantization': 'all four tensors: int16 scale4096 nearest_ties_away, QAT straight-through',
        'weight_projection': 'symmetric [-32767/4096,32767/4096]',
        'initial': initial, 'final': final, 'mse_delta': final['mse'] - initial['mse'],
        'epochs_completed_on_saved_slice': 1, 'rows_seen': epoch['rows_seen'], 'unique_rows_seen': len(set(epoch['row_order'])),
        'filtered_source_rows': selected['source_rows'],
        'full_original_sample_epoch': False, 'holdout_evaluation': False, 'elo_claim': False,
        'training_seconds': epoch['training_seconds'], 'total_seconds': time.monotonic() - started,
        'finished_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'checkpoint_sha256': manifest['checkpoint_sha256'],
        'implementation': [artifact(path) for path in implementation],
        'files': [artifact(path) for path in sorted(args.out.rglob('*')) if path.is_file()],
    }
    write_json(args.out / 'metrics.json', result)
    print(json.dumps({'event': 'completed', 'initial_mse': initial['mse'], 'final_mse': final['mse'],
                      'rows_seen': epoch['rows_seen'], 'status': result['status'],
                      'checkpoint_sha256': manifest['checkpoint_sha256']}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
