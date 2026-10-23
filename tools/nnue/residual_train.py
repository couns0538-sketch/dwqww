"""Train Forge's existing residual NNUE against immutable prepared game splits.

Search and the shipped network are never modified. The shared legacy model and
exporter remain the only architecture/serialization implementation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
import torch
import torch.nn.functional as F

from include_parser import load_include
from train_nnue import NNUE, atomic_write, cpu_copy, export_forge

K = 2.25
CP_SCALE = 400.0
# search.hpp: MateValue32000 - MaxPly128 - 1; no search source is changed.
COMBINED_CP_LIMIT = 31871
ARRAY_NAMES = {"features", "hce", "score", "result_stm"}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def residual_logit_target(score_cp, hce_cp):
    return (score_cp - hce_cp) * K / CP_SCALE


def predicted_probability(residual_logit, hce_cp):
    return torch.sigmoid(hce_cp * K / CP_SCALE + residual_logit)


def engine_centipawns(residual_logit, hce_cp):
    """The two distinct clamps/truncation in nnue.cpp and Worker evaluation."""
    correction = torch.trunc(torch.clamp(residual_logit * CP_SCALE / K, -30000, 30000))
    combined = torch.clamp(hce_cp + correction, -COMBINED_CP_LIMIT, COMBINED_CP_LIMIT)
    return correction, combined


def residual_probability_target(score_cp, hce_cp, result_stm, weight):
    if not math.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError("Result weight must be finite and in [0,1]")
    teacher = predicted_probability(residual_logit_target(score_cp, hce_cp), hce_cp)
    return (1 - weight) * teacher + weight * result_stm


def target_spec(weight):
    """Portable identity of the probability target, independent of a model."""
    if not math.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError("Result weight must be finite and in [0,1]")
    return {"kind": "teacher_probability_game_result_blend", "result_weight": weight,
            "sigmoid_k": K, "cp_scale": CP_SCALE}


def fixed_probability_target(score_cp, result_stm, weight):
    """Independent teacher probability: no HCE subtraction/addition rounding."""
    target_spec(weight)
    teacher = torch.sigmoid(score_cp * K / CP_SCALE)
    return (1 - weight) * teacher + weight * result_stm


def load_protocol(path, weight, epochs=None, include_initial=None):
    """Bind a preregistered fixed target and epoch rule before any model read."""
    path = Path(path).resolve()
    raw = path.read_bytes()
    protocol = json.loads(raw)
    if (not isinstance(protocol, dict) or type(protocol.get("schema_version")) is not int
            or protocol["schema_version"] != 1 or protocol.get("target") != target_spec(weight)):
        raise ValueError("Frozen protocol target blend/schema differs")
    training = protocol.get("training")
    if (not isinstance(training, dict) or type(training.get("epochs")) is not int or training["epochs"] < 1
            or training.get("selection_metric") != "target_mse_combined"
            or type(training.get("include_initial")) is not bool
            or (epochs is not None and training["epochs"] != epochs)
            or (include_initial is not None and training["include_initial"] != include_initial)):
        raise ValueError("Frozen protocol epoch selection rule differs")
    return protocol, {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}


def verify_prepared_protocol(manifest, protocol):
    if protocol is not None and manifest.get("protocol_sha256") != protocol["sha256"]:
        raise ValueError("Prepared data frozen protocol SHA-256 differs or is absent")


def verify_training_qualification(manifest, baseline_only=False):
    """Partial independent-teacher data and the final audit cannot optimize."""
    if manifest.get("provenance_format") != "independent_teacher_v1" or baseline_only:
        return
    if manifest.get("training_permitted") is not True:
        raise ValueError("Independent-teacher data is not qualified for training")
    minimum, retained = manifest.get("minimum_positions"), manifest.get("retained_total_positions")
    if (type(minimum) is not int or minimum < 5000000
            or type(retained) is not int or retained < minimum):
        raise ValueError("Independent-teacher positions do not meet the integer minimum of at least 5000000")
    if manifest.get("dataset_role") != "training_and_selection":
        raise ValueError("Independent-teacher dataset role must allow training and selection; final audit is excluded")


def _progress(epoch, epochs):
    if type(epochs) is not int or epochs < 1 or type(epoch) is not int or not 0 <= epoch < epochs:
        raise ValueError("Require zero-based epoch in a positive epoch count")
    return epoch / (epochs - 1) if epochs > 1 else 0.0


def result_weight(epoch, epochs, start, end):
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in (start, end)):
        raise ValueError("Result weights must be finite and in [0,1]")
    return start + (end - start) * _progress(epoch, epochs)


def learning_rate(epoch, epochs, initial, minimum):
    if not math.isfinite(initial) or not math.isfinite(minimum) or not 0 <= minimum <= initial or initial <= 0:
        raise ValueError("Require finite 0 <= minimum LR <= positive initial LR")
    return minimum + (initial - minimum) * (1 + math.cos(math.pi * _progress(epoch, epochs))) / 2


def _game_ids(split, key, allow_empty=False):
    value = split.get(key)
    if (not isinstance(value, list) or (not value and not allow_empty)
            or any(not isinstance(v, str) or not v.strip() for v in value)
            or len(set(value)) != len(value)):
        raise ValueError("Missing or invalid game identities: " + key)
    return set(value)


def _hash_binding(path, expected, label):
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Invalid SHA-256 binding for " + label)
    if not Path(path).is_file() or sha256(path) != expected:
        raise ValueError("Missing or changed input: " + label)


def load_prepared_data(data_dir):
    """Read v1 NPZ arrays and authenticate the preparer's declared provenance."""
    data_dir = Path(data_dir).resolve()
    manifest_path = data_dir / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if (type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1
            or manifest.get("hidden_size") != 128
            or manifest.get("score_pov") != "side_to_move" or manifest.get("result_pov") != "side_to_move"):
        raise ValueError("Prepared data architecture, schema or score/result POV differs")
    split = manifest.get("split")
    if not isinstance(split, dict) or type(split.get("seed")) is not int:
        raise ValueError("Missing game split identity/seed")
    policy = split.get("policy")
    unknown = split.get("legacy_training_game_ids_unknown")
    if type(unknown) is not bool or policy not in ("game_hash", "legacy_train_only_with_new_heldout_games"):
        raise ValueError("Unsupported or incomplete game split provenance")
    if unknown and policy != "legacy_train_only_with_new_heldout_games":
        raise ValueError("Unknown legacy game IDs may only occur in explicitly training-only data")
    train_games = _game_ids(split, "train_game_ids", allow_empty=unknown)
    validation_games = _game_ids(split, "validation_game_ids")
    if train_games & validation_games:
        raise ValueError("Training/validation game IDs overlap")
    filters = manifest.get("filters")
    if (not isinstance(filters, dict) or type(filters.get("max_abs_score")) is not int
            or filters["max_abs_score"] < 1 or filters.get("no_in_check") is not True
            or filters.get("tactical_bestmove_filter") is not True):
        raise ValueError("Prepared position filters are absent or incomplete")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Original source identities are required")
    for entry in sources:
        if (not isinstance(entry, dict) or not isinstance(entry.get("path"), str)
                or not isinstance(entry.get("kind"), str) or not entry["kind"]):
            raise ValueError("Invalid original source identity")
        path = Path(entry["path"])
        if not path.is_absolute():
            path = data_dir / path
        _hash_binding(path, entry.get("sha256"), str(path))
    records = manifest.get("files")
    if not isinstance(records, dict) or set(records) != {"train.npz", "validation.npz"}:
        raise ValueError("Exactly train.npz and validation.npz must be bound")
    loaded = []
    for name in ("train.npz", "validation.npz"):
        record = records[name]
        if not isinstance(record, dict) or type(record.get("rows")) is not int or record["rows"] <= 0:
            raise ValueError("Missing positive prepared row count: " + name)
        path = data_dir / name
        _hash_binding(path, record.get("sha256"), name)
        with np.load(path, allow_pickle=False) as archive:
            if set(archive.files) != ARRAY_NAMES:
                raise ValueError("Prepared NPZ array names differ: " + name)
            data = {key: archive[key] for key in ARRAY_NAMES}
        count = record["rows"]
        if data["features"].dtype != np.int16 or data["features"].shape != (count, 2, 32):
            raise ValueError("Prepared features must be int16[N,2,32]")
        if any(data[key].dtype != np.int32 or data[key].shape != (count,) for key in ("hce", "score")):
            raise ValueError("Prepared HCE/search scores must be int32[N]")
        if data["result_stm"].dtype != np.float32 or data["result_stm"].shape != (count,):
            raise ValueError("Prepared STM results must be float32[N]")
        for begin in range(0, count, 4096):
            features = data["features"][begin:begin + 4096]
            if ((features < -1) | (features >= 768)).any():
                raise ValueError("Prepared feature index is outside -1/0..767")
            ordered = np.sort(features, axis=2)
            if ((ordered[:, :, 1:] == ordered[:, :, :-1]) & (ordered[:, :, 1:] >= 0)).any():
                raise ValueError("Duplicate active piece-square feature")
            if not np.array_equal((features[:, 0] >= 0).sum(1), (features[:, 1] >= 0).sum(1)):
                raise ValueError("Perspective feature counts differ")
        if np.any(np.abs(data["score"].astype(np.int64)) > filters["max_abs_score"]):
            raise ValueError("Prepared search score exceeds its declared cap")
        if not np.isin(data["result_stm"], (0.0, 0.5, 1.0)).all():
            raise ValueError("Prepared STM outcomes must be 0, 0.5 or 1")
        loaded.append(data)
    return (*loaded, manifest, hashlib.sha256(manifest_bytes).hexdigest())


def _dense_features(features):
    indices = torch.from_numpy(features.astype(np.int64, copy=False))
    active = indices >= 0
    dense = torch.zeros((len(features), 2, 768), dtype=torch.float32)
    dense.scatter_add_(2, indices.clamp_min(0), active.to(torch.float32))
    return dense


def verify_unchanged_inputs(data_dir, manifest, manifest_sha):
    """Rehash the frozen files without allocating a second copy of the NPZs."""
    data_dir = Path(data_dir).resolve()
    _hash_binding(data_dir / "manifest.json", manifest_sha, "manifest.json")
    for name, record in manifest["files"].items():
        _hash_binding(data_dir / name, record["sha256"], name)
    for entry in manifest["sources"]:
        path = Path(entry["path"])
        if not path.is_absolute():
            path = data_dir / path
        _hash_binding(path, entry["sha256"], str(path))


@torch.no_grad()
def evaluate(model, data, batch_size, result_weight=0.0, fixed_target=False):
    """Evaluate every held-out row with engine-style correction cp truncation."""
    if batch_size < 1 or len(data["score"]) < 1:
        raise ValueError("Evaluation needs a positive batch size and nonempty rows")
    target_spec(result_weight)
    names = ("teacher_mse_hce", "teacher_mse_combined", "teacher_mse_net_only",
             "target_mse_hce", "target_mse_combined", "target_mse_net_only")
    sums = dict.fromkeys(names, 0.0)
    was_training = model.training
    model.eval()
    try:
        for begin in range(0, len(data["score"]), batch_size):
            end = begin + batch_size
            hce = torch.from_numpy(data["hce"][begin:end].astype(np.float32))
            score = torch.from_numpy(data["score"][begin:end].astype(np.float32))
            outcome = torch.from_numpy(data["result_stm"][begin:end])
            logits = model(_dense_features(data["features"][begin:end])).reshape(-1)
            if not torch.isfinite(logits).all():
                raise RuntimeError("Non-finite network inference during validation")
            correction, combined_cp = engine_centipawns(logits, hce)
            teacher = torch.sigmoid(score * K / CP_SCALE)
            target = (fixed_probability_target(score, outcome, result_weight) if fixed_target
                      else residual_probability_target(score, hce, outcome, result_weight))
            hce_probability = torch.sigmoid(hce * K / CP_SCALE)
            combined_probability = torch.sigmoid(combined_cp * K / CP_SCALE)
            net_probability = torch.sigmoid(correction * K / CP_SCALE)
            pairs = ((hce_probability, teacher), (combined_probability, teacher), (net_probability, teacher),
                     (hce_probability, target), (combined_probability, target), (net_probability, target))
            for name, (prediction, expected) in zip(names, pairs):
                sums[name] += float(((prediction.double() - expected.double()) ** 2).sum())
    finally:
        model.train(was_training)
    count = len(data["score"])
    return {"count": count, **{name: value / count for name, value in sums.items()}}


def _json(path, data):
    atomic_write(Path(path), lambda stream: stream.write((json.dumps(data, indent=2, allow_nan=False) + "\n").encode()))


def _load_initial(model, path):
    net = load_include(path, expected_hidden=128)
    if not net["residual"]:
        raise ValueError("An initial residual checkpoint must declare FORGE_NNUE_RESIDUAL 1")
    with torch.no_grad():
        model.ft.weight.copy_(torch.from_numpy(net["w1"].T.copy()))
        model.ft.bias.copy_(torch.from_numpy(net["b1"]))
        model.tail[0].weight.copy_(torch.from_numpy(net["w2"].reshape(1, -1)))
        model.tail[0].bias.fill_(net["b2"])
    return {"path": str(Path(path).resolve()), "sha256": net["sha256"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--min-lr", type=float, default=0.00001)
    parser.add_argument("--result-start", type=float, default=0.0)
    parser.add_argument("--result-end", type=float, default=0.1)
    parser.add_argument("--fixed-result-weight", type=float,
                        help="Use one result blend for training, validation and epoch selection; overrides the schedule")
    parser.add_argument("--exclude-initial-from-selection", action="store_true",
                        help="Select only among completed trained epochs; initial remains a diagnostic/baseline")
    parser.add_argument("--protocol", type=Path, help="Frozen JSON target and epoch-selection protocol")
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--initial-net", type=Path)
    args = parser.parse_args(argv)
    if args.batch_size < 1 or not 1 <= args.threads <= 4:
        raise ValueError("Batch size must be positive and CPU threads in 1..4")
    learning_rate(0, args.epochs, args.lr, args.min_lr)
    result_weight(0, args.epochs, args.result_start, args.result_end)
    validation_weight = args.fixed_result_weight if args.fixed_result_weight is not None else 0.0
    selection_target = target_spec(validation_weight)
    selection_metric = "target_mse_combined" if args.fixed_result_weight is not None else "teacher_mse_combined"
    protocol, protocol_identity = None, None
    if args.protocol is not None:
        if args.fixed_result_weight is None:
            raise ValueError("A frozen protocol requires --fixed-result-weight")
        protocol, protocol_identity = load_protocol(args.protocol, validation_weight, args.epochs,
                                                   not args.exclude_initial_from_selection)
    train, validation, manifest, manifest_sha = load_prepared_data(args.data_dir)
    verify_prepared_protocol(manifest, protocol_identity)
    verify_training_qualification(manifest, args.baseline_only)
    run_dir = args.run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "checkpoints").mkdir()
    (run_dir / "exports").mkdir()
    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    model = NNUE([128], qat=True)
    initial_net = None
    if args.initial_net:
        initial_net = _load_initial(model, args.initial_net)
    else:
        with torch.no_grad():
            model.tail[0].weight.zero_()
            model.tail[0].bias.zero_()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, foreach=False)
    config = {**vars(args), "data_dir": str(args.data_dir.resolve()), "run_dir": str(run_dir),
              "initial_net": initial_net, "hidden": 128, "residual": True, "sigmoid_k": K,
              "selection_target": selection_target, "selection_metric": selection_metric,
              "protocol": protocol_identity,
              "selection_include_initial": not args.exclude_initial_from_selection,
              "validation_metric": "complete held-out " + selection_metric + " after engine-style correction truncation"}
    initial = evaluate(model, validation, args.batch_size, result_weight=validation_weight,
                       fixed_target=args.fixed_result_weight is not None)

    def best_record(epoch, metrics, stem):
        return {"epoch": epoch, "teacher_mse_combined": metrics["teacher_mse_combined"],
                "target_mse_combined": metrics["target_mse_combined"],
                "selection_metric": selection_metric, "selection_mse": metrics[selection_metric],
                "improves_hce": metrics[selection_metric] < initial[selection_metric.replace("combined", "hce")],
                "stem": stem}

    summary = {"status": "running", "utc": datetime.now(timezone.utc).isoformat(),
               "training_count": len(train["score"]), "validation_count": len(validation["score"]),
               "epochs_completed": 0, "manifest_sha256": manifest_sha,
               "hce_baseline": initial[selection_metric.replace("combined", "hce")], "initial": initial, "config": config,
               "best": None if args.exclude_initial_from_selection else best_record(0, initial, "initial"),
               "epochs": [], "elo_claim": None}

    def save(stem, epoch, metrics):
        checkpoint = {"schema_version": 1, "epoch": epoch, "config": config,
                      "model": cpu_copy(model.state_dict()), "optimizer": cpu_copy(optimizer.state_dict()),
                      "torch_rng_state": torch.get_rng_state(), "manifest_sha256": manifest_sha, "metrics": metrics}
        atomic_write(run_dir / "checkpoints" / (stem + ".pt"), lambda stream: torch.save(checkpoint, stream))
        export_stem = run_dir / "exports" / stem
        metadata = export_forge(model, export_stem, K, residual=True)
        _json(export_stem.with_suffix(".json"), {**metadata, "epoch": epoch, "metrics": metrics,
                                               "manifest_sha256": manifest_sha,
                                               "selection_target": selection_target, "selection_metric": selection_metric,
                                               "protocol": protocol_identity,
                                               "inc_sha256": sha256(export_stem.with_suffix(".inc")),
                                               "bin_sha256": sha256(export_stem.with_suffix(".bin"))})

    save("initial", 0, initial)
    _json(run_dir / "initial-report.json", summary)
    _json(run_dir / "input-manifest.json", manifest)
    if protocol is not None:
        _json(run_dir / "protocol.json", protocol)
    try:
        if not args.baseline_only:
            for epoch in range(args.epochs):
                lr = learning_rate(epoch, args.epochs, args.lr, args.min_lr)
                weight = (args.fixed_result_weight if args.fixed_result_weight is not None
                          else result_weight(epoch, args.epochs, args.result_start, args.result_end))
                optimizer.param_groups[0]["lr"] = lr
                model.train()
                order = np.random.default_rng(args.seed + epoch).permutation(len(train["score"]))
                loss_sum = 0.0
                for begin in range(0, len(order), args.batch_size):
                    indices = order[begin:begin + args.batch_size]
                    hce = torch.from_numpy(train["hce"][indices].astype(np.float32))
                    score = torch.from_numpy(train["score"][indices].astype(np.float32))
                    outcome = torch.from_numpy(train["result_stm"][indices])
                    logits = model(_dense_features(train["features"][indices])).reshape(-1)
                    target = (fixed_probability_target(score, outcome, weight) if args.fixed_result_weight is not None
                              else residual_probability_target(score, hce, outcome, weight))
                    loss = F.mse_loss(predicted_probability(logits, hce), target)
                    if not torch.isfinite(loss):
                        raise RuntimeError("Non-finite training loss")
                    optimizer.zero_grad(set_to_none=True)
                    loss.backward()
                    optimizer.step()
                    model.project_weights()
                    loss_sum += float(loss.detach()) * len(indices)
                metrics = evaluate(model, validation, args.batch_size, result_weight=weight,
                                   fixed_target=args.fixed_result_weight is not None)
                record = {"epoch": epoch + 1, "lr": lr, "result_weight": weight,
                          "training_target_mse": loss_sum / len(order), **metrics}
                stem = f"epoch-{epoch + 1:04d}"
                save(stem, epoch + 1, metrics)
                summary["epochs_completed"] = epoch + 1
                summary["epochs"].append(record)
                if summary["best"] is None or metrics[selection_metric] < summary["best"]["selection_mse"]:
                    summary["best"] = best_record(epoch + 1, metrics, stem)
                _json(run_dir / f"epoch-{epoch + 1:04d}-report.json", {**summary, "latest": record})
                print(json.dumps({"epoch": epoch + 1, "lr": lr, "result_weight": weight,
                                  "teacher_mse_hce": metrics["teacher_mse_hce"],
                                  "teacher_mse_combined": metrics["teacher_mse_combined"],
                                  "target_mse_combined": metrics["target_mse_combined"], "count": metrics["count"]}), flush=True)
        # Reauthenticate original raw files and prepared bytes after the run.
        verify_unchanged_inputs(args.data_dir, manifest, manifest_sha)
        if initial_net and sha256(initial_net["path"]) != initial_net["sha256"]:
            raise ValueError("Initial network changed during training")
        if protocol_identity is not None:
            _hash_binding(protocol_identity["path"], protocol_identity["sha256"], "frozen protocol")
        summary["status"] = "baseline_only" if args.baseline_only else "completed"
        summary["input_integrity"] = "passed"
    except KeyboardInterrupt:
        save(f"interrupted-after-{summary['epochs_completed']:04d}", summary["epochs_completed"],
             evaluate(model, validation, args.batch_size, result_weight=validation_weight,
                      fixed_target=args.fixed_result_weight is not None))
        summary["status"] = "interrupted"
        _json(run_dir / "summary.json", summary)
        raise
    except BaseException as error:
        summary.update(status="failed", error=repr(error))
        _json(run_dir / "summary.json", summary)
        raise
    _json(run_dir / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "hce_baseline": summary["hce_baseline"], "best": summary["best"]}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print("Error: " + str(error), file=sys.stderr)
        raise SystemExit(1)
