#!/usr/bin/env python3
"""Actual C++ inference versus the shared Python trainer; no search or games.

Run with --probe BUILD/forge_nnue_probe --out NEW_DIRECTORY. Original streams,
input FENs and failure controls are retained. Integer-cp tolerance is fixed at1.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys

import chess
import numpy as np
import torch

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from include_parser import load_include


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def trainer_module(path):
    spec = importlib.util.spec_from_file_location("forge_original_nnue_trainer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def corpus(sample, count, seed):
    records, seen = [], set()
    origins = {}

    def add(board, origin):
        if not board.is_valid():
            raise ValueError("Invalid parity board: " + board.fen(en_passant="fen"))
        key = " ".join(board.fen(en_passant="fen").split()[:4])
        if key in seen or len(records) == count:
            return False
        seen.add(key)
        records.append(board.fen(en_passant="fen"))
        origins[origin] = origins.get(origin, 0) + 1
        return True

    for line in sample.read_text(encoding="ascii").splitlines():
        if line.strip():
            add(chess.Board(line.split("|", 1)[0].strip()), "bundled_sample")
    starts = [
        chess.STARTING_FEN,
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
        "4k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1",
        "7k/6Q1/5K2/8/8/8/8/8 b - - 0 1",
        "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
    ]
    boards = [chess.Board(fen) for fen in starts]
    boards += [board.mirror() for board in boards.copy()]
    special = {"castles": 0, "en_passant": 0, "promotions": 0, "captures": 0}
    for board in boards:
        add(board, "special_start")
        for move in sorted(board.legal_moves, key=lambda move: move.uci()):
            child = board.copy(stack=False)
            child.push(move)
            if add(child, "special_first_move"):
                special["castles"] += int(board.is_castling(move))
                special["en_passant"] += int(board.is_en_passant(move))
                special["promotions"] += int(bool(move.promotion))
                special["captures"] += int(board.is_capture(move))
    rng = random.Random(seed)
    for walk in range(256):
        if len(records) == count:
            break
        board = boards[walk % len(boards)].copy(stack=False)
        for _ in range(256):
            add(board, "legal_walk")
            moves = list(board.legal_moves)
            if not moves or len(records) == count:
                break
            board.push(moves[rng.randrange(len(moves))])
    if len(records) != count:
        raise ValueError(f"Only generated {len(records)} of {count} unique parity positions")
    return records, origins, special


def run_probe(probe, args, payload, out, stem):
    (out / (stem + ".stdin")).write_bytes(payload)
    command = [str(probe), *args]
    try:
        completed = subprocess.run(command, input=payload, capture_output=True, timeout=90, check=False)
    except subprocess.TimeoutExpired as error:
        # subprocess.run kills/reaps its child before raising, but does not
        # expose the resulting return code. Keep that observation unknown.
        stdout, stderr = error.stdout or b"", error.stderr or b""
        (out / (stem + ".stdout")).write_bytes(stdout)
        (out / (stem + ".stderr")).write_bytes(stderr)
        (out / (stem + ".command.json")).write_text(json.dumps({
            "command": command, "returncode": None, "timed_out": True,
            "stdin_sha256": hashlib.sha256(payload).hexdigest(),
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        }, indent=2) + "\n")
        raise
    (out / (stem + ".stdout")).write_bytes(completed.stdout)
    (out / (stem + ".stderr")).write_bytes(completed.stderr)
    (out / (stem + ".command.json")).write_text(json.dumps({
        "command": command, "returncode": completed.returncode, "timed_out": False,
        "stdin_sha256": hashlib.sha256(payload).hexdigest(),
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }, indent=2) + "\n")
    return completed


def run(args):
    args.out.mkdir(parents=True, exist_ok=False)
    frozen = {str(path.resolve()): sha(path) for path in (
        args.probe, args.trainer, args.weights, args.sample,
        Path(__file__), HERE / "engine_probe.cpp", HERE / "include_parser.py")}
    module = trainer_module(args.trainer)
    weights = load_include(args.weights)
    hidden = weights["hidden"]
    torch.set_num_threads(2)
    model = module.NNUE([hidden], qat=True).cpu().eval()
    with torch.no_grad():
        model.ft.weight.copy_(torch.from_numpy(weights["w1"].T.copy()))
        model.ft.bias.copy_(torch.from_numpy(weights["b1"].copy()))
        model.tail[0].weight.copy_(torch.from_numpy(weights["w2"].reshape(1, -1).copy()))
        model.tail[0].bias.fill_(weights["b2"])
    fens, origins, special = corpus(args.sample, args.positions, args.seed)
    payload = ("\n".join(fens) + "\n").encode("ascii")
    completed = run_probe(args.probe, [], payload, args.out, "actual-engine")
    if completed.returncode != 0 or completed.stderr:
        raise ValueError("Actual engine probe failed; original streams retained")
    rows = [json.loads(line) for line in completed.stdout.splitlines()]
    if len(rows) != args.positions:
        raise ValueError("Actual engine probe row count differs")
    integer_errors, continuous_errors = [], []
    feature_mismatches = []
    input_saturation = {"below_zero": 0, "at_zero": 0, "between": 0, "at_one": 0, "above_one": 0}
    differences = []
    for start in range(0, len(fens), 128):
        selected = fens[start:start + 128]
        x = np.zeros((len(selected), 2, 768), dtype=np.float32)
        for offset, fen in enumerate(selected):
            index = start + offset
            board = chess.Board(fen)
            expected = module.feature_indices(board)
            row = rows[index]
            if row["index"] != index or row["hidden_size"] != hidden or row["residual_mode"] != weights["residual"]:
                raise ValueError("Engine index, architecture or residual flag differs")
            if row["hce_only"] or not row["nnue_available"]:
                raise ValueError("Full probe did not evaluate its compiled network")
            if len(row["features"]) != 2 or any(sorted(row["features"][p]) != sorted(expected[p]) for p in (0, 1)):
                feature_mismatches.append(index)
            legal = list(board.legal_moves)
            terminal = not legal or board.is_insufficient_material() or board.halfmove_clock >= 100
            tactical = any(board.is_capture(move) or move.promotion or board.gives_check(move) for move in legal)
            if (row["in_check"] != board.is_check() or row["terminal"] != terminal
                    or row["has_tactical_legal_move"] != tactical):
                raise ValueError(f"Actual legal/filter flags differ at position {index}")
            for perspective in (0, 1):
                x[offset, perspective, expected[perspective]] = 1.0
        with torch.no_grad():
            tensor = torch.from_numpy(x)
            accumulator = model.linear(tensor, model.ft)
            a = accumulator.numpy()
            input_saturation["below_zero"] += int(np.count_nonzero(a < 0))
            input_saturation["at_zero"] += int(np.count_nonzero(a == 0))
            input_saturation["between"] += int(np.count_nonzero((a > 0) & (a < 1)))
            input_saturation["at_one"] += int(np.count_nonzero(a == 1))
            input_saturation["above_one"] += int(np.count_nonzero(a > 1))
            logits = model(tensor).numpy().reshape(-1)
        continuous = logits * np.float32(400.0) / np.float32(2.25)
        predicted = np.trunc(np.clip(continuous, -30000, 30000)).astype(np.int64)
        for offset, (cp, raw) in enumerate(zip(predicted, continuous)):
            index = start + offset
            expected_cp = rows[index]["nnue_cp_stm"]
            error = abs(int(cp) - expected_cp)
            integer_errors.append(error)
            continuous_errors.append(abs(float(np.clip(raw, -30000, 30000)) - expected_cp))
            if error:
                differences.append({"index": index, "engine_cp": expected_cp, "trainer_cp": int(cp), "error_cp": error})
    controls = []
    for name, bad in [("missing_king", b"8/8/8/8/8/8/8/4K3 w - - 0 1\n"),
                      ("extra_field", (fens[0] + " unexpected\n").encode("ascii")),
                      ("empty", b"")]:
        rejected = run_probe(args.probe, [], bad, args.out, "invalid-" + name)
        controls.append({"name": name, "rejected": rejected.returncode != 0 and bool(rejected.stderr)})
    hce = run_probe(args.probe, ["--hce-only"], payload, args.out, "hce-only")
    hce_rows = [json.loads(line) for line in hce.stdout.splitlines()]
    hce_equal = (hce.returncode == 0 and not hce.stderr and len(hce_rows) == len(rows)
                 and all({k: v for k, v in a.items() if k not in ("nnue_cp_stm", "hce_only")}
                         == {k: v for k, v in b.items() if k not in ("nnue_cp_stm", "hce_only")}
                         and b["nnue_cp_stm"] is None and b["hce_only"] is True
                         for a, b in zip(rows, hce_rows)))
    changed_inputs = [name for name, expected in frozen.items() if sha(name) != expected]
    passed = (not feature_mismatches and max(integer_errors) <= 1 and hce_equal and not changed_inputs
              and all(c["rejected"] for c in controls) and all(special.values()))
    result = {
        "status": "PASS" if passed else "FAIL", "utc": datetime.now(timezone.utc).isoformat(),
        "positions": len(fens), "seed": args.seed, "hidden_size": hidden, "residual_mode": weights["residual"],
        "integer_cp_tolerance": 1, "maximum_integer_cp_error": max(integer_errors),
        "maximum_continuous_cp_vs_engine_integer_error": max(continuous_errors),
        "exact_integer_matches": sum(error == 0 for error in integer_errors),
        "within_one_cp": sum(error <= 1 for error in integer_errors),
        "feature_mismatch_count": len(feature_mismatches), "feature_mismatch_indices": feature_mismatches,
        "filter_flags_match_python_chess": True, "hce_only_records_match": hce_equal,
        "invalid_input_controls": controls, "corpus_origins": origins,
        "special_first_moves_included_before_walk": special, "activation_categories": input_saturation,
        "different_integer_rows": differences, "probe_sha256": sha(args.probe),
        "frozen_inputs_sha256": frozen, "changed_inputs": changed_inputs,
        "weights_sha256": weights["sha256"], "trainer_sha256": sha(args.trainer),
        "probe_source_sha256": sha(HERE / "engine_probe.cpp"),
        "sample_sha256": sha(args.sample), "fen_input_sha256": hashlib.sha256(payload).hexdigest(),
        "torch_version": torch.__version__, "numpy_version": np.__version__, "python_chess_version": chess.__version__,
        "scope": "Trainer versus unchanged actual C++ static inference and legal/filter flags only; no loss, speed, training, search or Elo conclusion.",
    }
    (args.out / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k in ("status", "positions", "maximum_integer_cp_error", "exact_integer_matches", "feature_mismatch_count", "hce_only_records_match")}, indent=2))
    return 0 if passed else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probe", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--weights", type=Path, default=REPO / "src/nnue_weights.inc")
    p.add_argument("--trainer", type=Path, default=HERE / "train_nnue.py")
    p.add_argument("--sample", type=Path, default=HERE / "examples/forge_sample.txt")
    p.add_argument("--positions", type=int, default=2048)
    p.add_argument("--seed", type=int, default=20261023)
    args = p.parse_args()
    if not 1000 <= args.positions <= 10000:
        p.error("--positions must be between1000 and10000")
    args.probe = args.probe.resolve()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
