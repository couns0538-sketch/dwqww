#!/usr/bin/env python3
"""Streaming Forge-768 NNUE trainer: DirectML, ROCm, or CPU.

Default shape: shared 768->256 accumulator, two SCReLU perspectives, 512->1.
--shape H[,L2,...] changes the architecture. Only --shape H can export the
supplied Forge C++ format; other shapes require your engine's own exporter.
Scores in input are STM cp; results in input are WHITE POV.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import random
import re
import signal
import sys
import time
import uuid

import chess
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, IterableDataset, get_worker_info

FEATURES = 768
SCALE = 4096.0


def feature_indices(board):
    """Exactly forge::nnue::feature_index, including kings; a1=0, h8=63."""
    result = []
    for perspective in (board.turn, not board.turn):
        indices = []
        for square, piece in board.piece_map().items():
            relative_color = 0 if piece.color == perspective else 1
            relative_square = square if perspective == chess.WHITE else square ^ 56
            indices.append((relative_color * 6 + piece.piece_type - 1) * 64 + relative_square)
        result.append(indices)
    return result


def parse_sample(line, blend, sigmoid_k):
    fen, score, result = (part.strip() for part in line.split("|"))
    cp, white_result = int(score), float(result)
    if white_result not in (0.0, 0.5, 1.0) or len(fen.split()) != 6:
        raise ValueError("Expected full FEN | integer STM cp | White result 0.0/0.5/1.0")
    board = chess.Board(fen)
    if not board.is_valid():
        raise ValueError(f"Invalid board: {fen}")
    stm_result = white_result if board.turn == chess.WHITE else 1.0 - white_result
    teacher = 1.0 / (1.0 + math.exp(-max(-40, min(40, cp * sigmoid_k / 400))))
    target = blend * teacher + (1.0 - blend) * stm_result
    return feature_indices(board), target


class TextPositions(IterableDataset):
    """Each loader reads a different byte range of EVERY file, once per epoch.

    The shuffle buffer is bounded. No full dataset or line index is loaded.
    Position-hash splitting keeps the same FEN out of both train and validation.
    """
    def __init__(self, files, validation, fraction, blend, sigmoid_k, buffer_size, seed):
        self.files = files  # [(absolute path, immutable size snapshot), ...]
        self.validation = validation
        self.fraction, self.blend, self.sigmoid_k = fraction, blend, sigmoid_k
        self.buffer_size, self.seed = buffer_size, seed

    def __iter__(self):
        info = get_worker_info()
        worker_id, workers = (info.id, info.num_workers) if info else (0, 1)
        rng = random.Random(self.seed + worker_id)
        files = self.files.copy()
        if not self.validation:
            rng.shuffle(files)
        buffer = []
        for path, size in files:
            begin, end = size * worker_id // workers, size * (worker_id + 1) // workers
            with open(path, "rb") as src:
                if begin:
                    src.seek(begin - 1)
                    if src.read(1) != b"\n":
                        src.readline()
                while src.tell() < end:
                    offset = src.tell()
                    raw = src.readline()
                    if not raw:
                        break
                    if not raw.endswith(b"\n"):
                        raise ValueError(f"Unterminated record at {path}, byte {offset}")
                    line = raw.decode("ascii").strip()
                    if not line:
                        continue
                    fen = line.split("|", 1)[0].strip()
                    key = " ".join(fen.split()[:4]).encode("ascii")
                    value = int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(), "little")
                    is_validation = value < int(self.fraction * (1 << 64))
                    if is_validation != self.validation:
                        continue
                    if self.validation or self.buffer_size == 0:
                        yield parse_sample(line, self.blend, self.sigmoid_k)
                    elif len(buffer) < self.buffer_size:
                        buffer.append(line)
                    else:
                        index = rng.randrange(len(buffer))
                        old, buffer[index] = buffer[index], line
                        yield parse_sample(old, self.blend, self.sigmoid_k)
        rng.shuffle(buffer)
        for line in buffer:
            yield parse_sample(line, self.blend, self.sigmoid_k)


def collate(samples):
    # Dense matmul avoids sparse/custom CUDA ops that DirectML may not support.
    x = np.zeros((len(samples), 2, FEATURES), dtype=np.float32)
    y = np.empty((len(samples), 1), dtype=np.float32)
    for i, (perspectives, target) in enumerate(samples):
        for p in (0, 1):
            x[i, p, perspectives[p]] = 1.0
        y[i, 0] = target
    # Send plain arrays through loader queues: no CUDA/DirectML tensors or
    # platform-specific tensor-sharing service is needed in loader workers.
    return x, y


def loader_init(worker_id):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    torch.set_num_threads(1)


class NNUE(nn.Module):
    def __init__(self, shape, qat=True):
        super().__init__()
        self.shape, self.qat = list(shape), qat
        self.ft = nn.Linear(FEATURES, shape[0])
        sizes = [2 * shape[0]] + list(shape[1:]) + [1]
        self.tail = nn.ModuleList(nn.Linear(a, b) for a, b in zip(sizes, sizes[1:]))
        nn.init.normal_(self.ft.weight, std=0.02)
        nn.init.zeros_(self.ft.bias)
        for layer in self.tail:
            nn.init.zeros_(layer.bias)

    def linear(self, x, layer):
        def quantized(p):
            if not self.qat:
                return p
            scaled = p * SCALE
            rounded = torch.sign(scaled) * torch.floor(torch.abs(scaled) + 0.5)
            q = torch.clamp(rounded, -32767, 32767) / SCALE
            return p + (q - p).detach()  # Straight-through gradient.
        return F.linear(x, quantized(layer.weight), quantized(layer.bias))

    def forward(self, x):
        h = torch.clamp(self.linear(x, self.ft), 0.0, 1.0).square()
        h = h.reshape(-1, 2 * self.shape[0])  # STM first, opponent second.
        for i, layer in enumerate(self.tail):
            h = self.linear(h, layer)
            if i + 1 < len(self.tail):
                h = torch.clamp(h, 0.0, 1.0).square()
        return h  # Logit; cp = logit * 400 / 2.25 for the supplied engine.

    @torch.no_grad()
    def project_weights(self):
        for parameter in self.parameters():
            parameter.clamp_(-32767 / SCALE, 32767 / SCALE)


def cpu_copy(value):
    if torch.is_tensor(value):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {k: cpu_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [cpu_copy(v) for v in value]
    if isinstance(value, tuple):
        return tuple(cpu_copy(v) for v in value)
    return value


def atomic_write(path, write):
    """Exclusive publication; old checkpoints/exports are never replaced."""
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with open(temp, "xb") as dst:
            write(dst)
            dst.flush()
            os.fsync(dst.fileno())
        if sys.platform == "win32":
            os.rename(temp, path)  # Windows never replaces an existing target.
        else:
            os.link(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def export_forge(model, stem, sigmoid_k):
    if len(model.shape) != 1 or sigmoid_k != 2.25:
        raise ValueError("Forge export needs --shape H and --sigmoid-k 2.25; use --export checkpoint otherwise")
    # C++ stores feature-major w1[768][H], then b1, STM/opponent w2, b2.
    hidden = model.shape[0]
    arrays = [model.ft.weight.detach().cpu().t().contiguous().numpy().ravel(),
              model.ft.bias.detach().cpu().numpy(),
              model.tail[0].weight.detach().cpu().numpy().ravel(),
              model.tail[0].bias.detach().cpu().numpy()]
    if not all(np.isfinite(values).all() for values in arrays):
        raise RuntimeError("Non-finite parameters; refusing to export")
    quantized = []
    for values in arrays:
        scaled = values.astype(np.float64) * SCALE
        # Same half-away-from-zero rounding as C++ std::lround.
        rounded = np.sign(scaled) * np.floor(np.abs(scaled) + 0.5)
        if (np.abs(rounded) > 32767).any():
            raise ValueError("Weights exceed the engine's int16 range")
        quantized.append(rounded.astype(np.int16))
    lines = ["// Generated by train_nnue.py; standalone Forge-768 network.",
             "#include <cstdint>", "#define FORGE_NNUE_RESIDUAL 0",
             f"static_assert(forge::nnue::InputCount == 768 && forge::nnue::HiddenSize == {hidden},",
             '              "NNUE shape mismatch; rebuild with the correct FORGE_NNUE_HIDDEN");',
             'static_assert(forge::nnue::SigmoidK == 2.25F, "NNUE output scale mismatch");',
             'static_assert(forge::nnue::WeightScale == 4096.0F && forge::nnue::OutputScale == 4096.0F,',
             '              "NNUE quantization scale mismatch");']
    for name, values in zip(("NnueW1", "NnueB1", "NnueW2"), quantized[:3]):
        lines.append(f"static const std::int16_t {name}[{len(values)}] = {{")
        lines.extend("  " + ", ".join(map(str, values[i:i + 24])) + ","
                     for i in range(0, len(values), 24))
        lines.append("};")
    lines.append(f"static const std::int16_t NnueB2 = {int(quantized[3][0])};")
    atomic_write(stem.with_suffix(".inc"), lambda dst: dst.write(("\n".join(lines) + "\n").encode("ascii")))
    # Raw float32 file is compatible with Forge 6.2's C++ trainer --load.
    raw = b"".join(np.asarray(values, dtype="<f4").tobytes() for values in arrays)
    atomic_write(stem.with_suffix(".bin"), lambda dst: dst.write(raw))
    return {"inputs": 768, "accumulator": hidden, "perspectives": 2,
            "output_inputs": 2 * hidden, "activation": "clamp(x,0,1)^2",
            "weight_scale": SCALE, "cp_per_logit": 400 / sigmoid_k,
            "raw_float32_bytes": len(raw), "runtime_loader": False,
            "integration": "Copy .inc to Forge src/nnue_weights.inc and rebuild."}


def device_for(name, index, requested_name="7900 XT"):
    def choose(names):
        if index is not None:
            if index >= len(names):
                raise ValueError("GPU device index is out of range")
            return index
        pattern = re.compile(r"\b" + re.escape(requested_name) + r"\b", re.IGNORECASE)
        matches = [i for i, value in enumerate(names) if pattern.search(value)]
        if not matches:
            raise ValueError(f"GPU {requested_name!r} not found; available: {names}. "
                             "Choose --device-name or --device-index explicitly.")
        return matches[0]

    if name == "directml":
        try:
            import torch_directml
        except ImportError as exc:
            raise RuntimeError("Install torch-directml in this Python environment; see README.txt") from exc
        index = choose([torch_directml.device_name(i) for i in range(torch_directml.device_count())])
        print(f"DirectML GPU {index}: {torch_directml.device_name(index)}", flush=True)
        return torch_directml.device(index)
    if name == "rocm":
        if not torch.version.hip or not torch.cuda.is_available():
            raise RuntimeError("ROCm is unavailable: install the supported WSL2 Radeon/PyTorch stack")
        index = choose([torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())])
        print(f"ROCm GPU {index}: {torch.cuda.get_device_name(index)}", flush=True)
        return torch.device(f"cuda:{index}")  # ROCm intentionally uses torch.cuda.
    return torch.device("cpu")


def file_snapshot(patterns, require_md5):
    paths = set()
    for pattern in patterns:
        paths.update(str(Path(path).resolve()) for path in glob.glob(pattern))
    result = []
    for name in sorted(paths):
        path = Path(name)
        if not path.is_file() or path.suffix != ".txt":
            continue
        if require_md5 and not path.with_suffix(".txt.md5").is_file():
            continue
        if path.stat().st_size:
            result.append((name, path.stat().st_size))
    if not result:
        raise ValueError("No finished nonempty .txt data files matched (finished files have .txt.md5).")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", nargs="+", required=True, help="Quoted file/glob paths")
    p.add_argument("--device", choices=["directml", "rocm", "cpu"], default="directml")
    p.add_argument("--device-index", type=int, help="Override automatic GPU name selection")
    p.add_argument("--device-name", default="7900 XT", help="Select this GPU by name; avoids using an integrated GPU")
    p.add_argument("--shape", help="Accumulator width and optional dense widths, e.g. 256 or 256,32,32")
    p.add_argument("--export", choices=["forge", "checkpoint"], default="forge")
    p.add_argument("--batch-size", type=int, default=1024)
    p.add_argument("--loader-workers", type=int, default=2)
    p.add_argument("--shuffle-buffer", type=int, default=8192, help="Raw records per loader worker")
    p.add_argument("--epochs", type=int, default=10, help="Total epoch target, including resumed epochs")
    p.add_argument("--steps-per-epoch", type=int, default=0, help="0 = stream all training records")
    p.add_argument("--validation-batches", type=int, default=100)
    p.add_argument("--validation-fraction", type=float, default=0.05)
    p.add_argument("--blend", type=float, help="Teacher fraction; remaining fraction is game result (default .75)")
    p.add_argument("--sigmoid-k", type=float, help="Default 2.25, as in Forge's source")
    p.add_argument("--no-qat", action="store_true", help="Disable int16 fake quantization during training")
    p.add_argument("--lr", type=float)
    p.add_argument("--cpu-threads", type=int, default=4)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--run-dir", default="forge-training")
    p.add_argument("--resume", help="Your own .pt checkpoint; a partial epoch is replayed on resume")
    p.add_argument("--allow-unsealed", action="store_true", help="Allow external .txt files without MD5 markers")
    a = p.parse_args()
    if (min(a.batch_size, a.epochs, a.validation_batches, a.cpu_threads) < 1
            or min(a.loader_workers, a.shuffle_buffer, a.steps_per_epoch) < 0
            or (a.device_index is not None and a.device_index < 0)
            or not 0 <= a.validation_fraction < 1 or (a.lr is not None and (not math.isfinite(a.lr) or a.lr <= 0))):
        p.error("Invalid positive/nonnegative numeric setting or validation fraction")
    torch.set_num_threads(a.cpu_threads)
    random.seed(a.seed)
    torch.manual_seed(a.seed)
    checkpoint = torch.load(a.resume, map_location="cpu", weights_only=True) if a.resume else None
    previous = checkpoint["config"] if checkpoint else {}
    shape = [int(v) for v in a.shape.split(",")] if a.shape else previous.get("shape", [256])
    blend = a.blend if a.blend is not None else previous.get("blend", 0.75)
    sigmoid_k = a.sigmoid_k if a.sigmoid_k is not None else previous.get("sigmoid_k", 2.25)
    qat = False if a.no_qat else previous.get("qat", True)
    if not shape or min(shape) <= 0 or not 0 <= blend <= 1 or not math.isfinite(sigmoid_k) or sigmoid_k <= 0:
        p.error("Invalid shape, blend or sigmoid-k")
    if a.export == "forge" and (len(shape) != 1 or shape[0] % 16 or sigmoid_k != 2.25):
        p.error("Forge export needs --shape H with H a multiple of 16 and --sigmoid-k 2.25")
    config = {"features": "forge768-relative-pieces-rank-flip", "shape": shape,
              "blend": blend, "sigmoid_k": sigmoid_k, "qat": qat}
    if previous and (previous["shape"] != shape or previous["features"] != config["features"]
                     or previous["sigmoid_k"] != sigmoid_k):
        p.error("Checkpoint architecture/features/output scale do not match")
    # Validate paths before creating a run or touching the GPU.
    files = file_snapshot(a.data, not a.allow_unsealed)
    run_dir = Path(a.run_dir).resolve()
    device = device_for(a.device, a.device_index, a.device_name)
    model = NNUE(shape, qat).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=a.lr or 0.001, foreach=False)
    next_epoch, step = 0, 0
    if checkpoint:
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        next_epoch, step = checkpoint["next_epoch"], checkpoint["step"]
        if a.lr is not None:
            for group in optimizer.param_groups:
                group["lr"] = a.lr
    if checkpoint:
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
    print(f"Shape: (768->{shape[0]}) x 2 -> {shape[1:] + [1]}; "
          f"device={device}; files={len(files)}; teacher blend={blend}; QAT={qat}", flush=True)
    print("Input scores: STM cp; game results are converted White -> STM before loss.", flush=True)
    stopping = False

    def interrupt(signum, frame):
        nonlocal stopping
        stopping = True

    previous_handler = signal.signal(signal.SIGINT, interrupt)
    started, last_log = time.monotonic(), time.monotonic()
    current_epoch, resume_epoch = next_epoch, next_epoch
    trained, loss_sum = 0, 0.0
    saved_steps = -1

    def save(epoch_to_resume, tag):
        nonlocal saved_steps
        stem = run_dir / f"{tag}-step{step:09d}-{time.time_ns()}"
        payload = {"config": config, "model": cpu_copy(model.state_dict()),
                   "optimizer": cpu_copy(optimizer.state_dict()),
                   "next_epoch": epoch_to_resume, "step": step}
        atomic_write(stem.with_suffix(".pt"), lambda dst: torch.save(payload, dst))
        metadata = dict(config)
        if a.export == "forge":
            metadata.update(export_forge(model, stem, sigmoid_k))
        atomic_write(stem.with_suffix(".json"),
                     lambda dst: dst.write((json.dumps(metadata, indent=2) + "\n").encode()))
        saved_steps = step
        print(f"Saved {stem.name} (.pt" + (", .inc, .bin, .json)" if a.export == "forge" else ", .json)"), flush=True)

    def make_loader(validation, epoch):
        dataset = TextPositions(files, validation, a.validation_fraction, blend, sigmoid_k,
                                0 if validation else a.shuffle_buffer, a.seed + epoch * 100003)
        return DataLoader(dataset, batch_size=a.batch_size, num_workers=a.loader_workers,
                          collate_fn=collate, worker_init_fn=loader_init, pin_memory=False,
                          persistent_workers=False,
                          multiprocessing_context="spawn" if a.loader_workers else None)

    try:
        for current_epoch in range(next_epoch, a.epochs):
            resume_epoch = current_epoch
            model.train()
            epoch_count = epoch_steps = 0
            epoch_loss = 0.0
            loader = make_loader(False, current_epoch)
            for x, target in loader:
                if stopping:
                    break
                x, target = torch.from_numpy(x).to(device), torch.from_numpy(target).to(device)
                optimizer.zero_grad(set_to_none=True)
                prediction = torch.sigmoid(model(x))
                loss = F.mse_loss(prediction, target)
                value = float(loss.detach().cpu())  # Synchronizes DirectML/ROCm.
                if not math.isfinite(value):
                    raise RuntimeError("Non-finite training loss; checkpoint not updated")
                loss.backward()
                optimizer.step()
                model.project_weights()
                count = len(x)
                step += 1
                epoch_steps += 1
                trained += count
                epoch_count += count
                loss_sum += value * count
                epoch_loss += value * count
                now = time.monotonic()
                if now - last_log >= 30:
                    print(f"Epoch {current_epoch + 1} step {step:,}: "
                          f"MSE={loss_sum / trained:.6f}, "
                          f"{trained / max(now - started, .001):,.0f} positions/s", flush=True)
                    last_log = now
                if a.steps_per_epoch and epoch_steps >= a.steps_per_epoch:
                    break
            del loader
            if stopping:
                break
            if epoch_count == 0:
                raise ValueError("No training samples; check data and validation-fraction")
            model.eval()
            validation_loss, validation_count = 0.0, 0
            if a.validation_fraction:
                with torch.no_grad():
                    loader = make_loader(True, current_epoch)
                    for i, (x, target) in enumerate(loader):
                        if stopping:
                            break
                        x, target = torch.from_numpy(x).to(device), torch.from_numpy(target).to(device)
                        value = float(F.mse_loss(torch.sigmoid(model(x)), target).cpu())
                        validation_loss += value * len(x)
                        validation_count += len(x)
                        if i + 1 >= a.validation_batches:
                            break
                    del loader
            val_text = f"{validation_loss / validation_count:.6f}" if validation_count else "no validation samples"
            print(f"Epoch {current_epoch + 1}: train MSE={epoch_loss / epoch_count:.6f}; "
                  f"validation MSE={val_text}", flush=True)
            resume_epoch = current_epoch + 1
            save(resume_epoch, f"epoch{current_epoch + 1:03d}")
            if stopping:
                break
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            if stopping and step != saved_steps:
                save(resume_epoch, "interrupted")
        finally:
            signal.signal(signal.SIGINT, previous_handler)
    print(f"Finished: {trained:,} positions processed this run, total step {step:,}.", flush=True)
    return 130 if stopping else 0


if __name__ == "__main__":
    mp.freeze_support()
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
