"""Compare frozen residual networks on identical, authenticated held-out games.

The paired bootstrap resamples represented games, preserving every sampled
game's full row count. These are held-out probability losses, never Elo.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys

import chess
import numpy as np
import torch

from prepare_residual_data import position_key, validate_record
from residual_train import (CP_SCALE, K, NNUE, _dense_features, _hash_binding,
                            _json, _load_initial, engine_centipawns, evaluate,
                            load_prepared_data, sha256, verify_unchanged_inputs)
from train_nnue import atomic_write, feature_indices


def cluster_bootstrap(reference, candidate, game_ids, draws=2000, seed=20261023):
    """Paired game-cluster bootstrap of ratios of summed losses to row counts."""
    reference, candidate = np.asarray(reference, dtype=np.float64), np.asarray(candidate, dtype=np.float64)
    if (reference.ndim != 1 or reference.shape != candidate.shape or not len(reference)
            or len(game_ids) != len(reference) or any(not isinstance(g, str) or not g.strip() for g in game_ids)
            or not np.isfinite(reference).all() or not np.isfinite(candidate).all()
            or (reference < 0).any() or (candidate < 0).any()):
        raise ValueError("Finite nonnegative paired row losses and authentic game IDs are required")
    if type(draws) is not int or draws < 1 or type(seed) is not int or seed < 0:
        raise ValueError("Positive bootstrap draws and nonnegative integer seed required")
    games = sorted(set(game_ids))
    if len(games) < 2:
        raise ValueError("At least two represented held-out games are needed for an interval")
    indices = {game: index for index, game in enumerate(games)}
    inverse = np.asarray([indices[game] for game in game_ids])
    counts = np.bincount(inverse, minlength=len(games))
    a = np.bincount(inverse, weights=reference, minlength=len(games))
    b = np.bincount(inverse, weights=candidate, minlength=len(games))
    rng = np.random.default_rng(seed)
    absolute = np.empty(draws, dtype=np.float64)
    relative = np.full(draws, np.nan, dtype=np.float64)
    for draw in range(draws):
        selected = rng.integers(0, len(games), size=len(games))
        rows = counts[selected].sum()
        ref_sum, candidate_sum = a[selected].sum(), b[selected].sum()
        absolute[draw] = (ref_sum - candidate_sum) / rows
        if ref_sum > 0:
            relative[draw] = (ref_sum - candidate_sum) / ref_sum
    reference_mean, candidate_mean = float(reference.mean()), float(candidate.mean())
    ci = lambda values: np.quantile(values, [0.025, 0.975], method="linear").tolist()
    relative_defined = bool(np.isfinite(relative).all())
    return {
        "rows": len(reference), "games": len(games), "draws": draws, "seed": seed,
        "reference_mse": reference_mean, "candidate_mse": candidate_mean,
        "improvement_abs": reference_mean - candidate_mean,
        "improvement_relative": (reference_mean - candidate_mean) / reference_mean if reference_mean > 0 else None,
        "ci95_abs": ci(absolute), "ci95_relative": ci(relative) if relative_defined else None,
        "relative_zero_reference_draws": int((~np.isfinite(relative)).sum()),
        "relative_interval_status": "defined" if relative_defined else "undefined_zero_reference_resample_no_draws_dropped",
        "method": "paired represented-game cluster bootstrap; ratio(sum loss / sum rows); percentile linear",
        "clusters": [{"game_id": game, "rows": int(counts[index]),
                      "reference_loss_sum": float(a[index]), "candidate_loss_sum": float(b[index])}
                     for index, game in enumerate(games)],
    }


def validate_validation_provenance(data_dir, manifest, data):
    """Replay producer-defined source-line recipes against actual held-out arrays."""
    data_dir = Path(data_dir).resolve()
    count = len(data["score"])
    artifacts = manifest.get("artifacts")
    binding = artifacts.get("validation-provenance.jsonl") if isinstance(artifacts, dict) else None
    if not isinstance(binding, dict) or type(binding.get("rows")) is not int or binding["rows"] != count:
        raise ValueError("Missing or mismatched held-out provenance artifact binding")
    path = data_dir / "validation-provenance.jsonl"
    _hash_binding(path, binding.get("sha256"), "validation-provenance.jsonl")
    if manifest.get("files", {}).get("validation.npz", {}).get("rows") != count:
        raise ValueError("Prepared validation/provenance row counts differ")
    split = manifest.get("split")
    if not isinstance(split, dict) or not isinstance(split.get("validation_game_ids"), list):
        raise ValueError("Authentic validation game membership is absent")
    known = split["validation_game_ids"]
    if not known or len(set(known)) != len(known) or any(not isinstance(g, str) or not g.strip() for g in known):
        raise ValueError("Invalid validation game identities")
    known = set(known)
    if known & set(split.get("train_game_ids", [])):
        raise ValueError("Training and validation game IDs overlap")
    engine_sha = manifest.get("generation_engine_sha256")
    if not isinstance(engine_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", engine_sha):
        raise ValueError("Frozen generating-engine identity is absent")
    source_bindings = {}
    for entry in manifest.get("sources", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("Malformed source binding")
        original = Path(entry["path"])
        resolved = original if original.is_absolute() else data_dir / original
        resolved = resolved.resolve()
        if resolved in source_bindings:
            raise ValueError("Duplicate source binding")
        source_bindings[resolved] = entry
    rows, requests = [], {}
    seen_identities = set()
    required = {"fen", "game_id", "ply", "source_path", "source_line", "legacy_game_identity_unknown"}
    with path.open() as stream:
        for line in stream:
            if not line.endswith("\n"):
                raise ValueError("Truncated held-out provenance row")
            row = json.loads(line)
            if not isinstance(row, dict) or set(row) != required:
                raise ValueError("Producer provenance row schema differs")
            if row["legacy_game_identity_unknown"] is not False or row["game_id"] not in known:
                raise ValueError("Missing genuine held-out game identity or wrong game membership")
            if (type(row["source_line"]) is not int or row["source_line"] < 1
                    or type(row["ply"]) is not int or row["ply"] < 0 or not isinstance(row["source_path"], str)):
                raise ValueError("Invalid source line/ply identity")
            source = Path(row["source_path"])
            source = (source if source.is_absolute() else data_dir / source).resolve()
            entry = source_bindings.get(source)
            if entry is None or entry.get("kind") != "authenticated_game_data_or_manifest":
                raise ValueError("Held-out row source is not bound authentic game data")
            identity = (row["game_id"], row["ply"])
            source_rows = requests.setdefault(source, {})
            if identity in seen_identities or row["source_line"] in source_rows:
                raise ValueError("Duplicate held-out game/ply or source-line identity")
            seen_identities.add(identity)
            source_rows[row["source_line"]] = len(rows)
            rows.append(row)
    if len(rows) != count:
        raise ValueError("Held-out recipe count differs from NPZ row count")
    replayed = 0
    for source, requested in requests.items():
        entry = source_bindings[source]
        _hash_binding(source, entry.get("sha256"), str(source))
        with source.open() as stream:
            for line_number, line in enumerate(stream, 1):
                if line_number not in requested:
                    continue
                index = requested[line_number]
                recipe = rows[index]
                original = validate_record(json.loads(line), manifest["filters"]["max_abs_score"])
                if (original["fen"] != recipe["fen"] or original["game_id"] != recipe["game_id"]
                        or original["ply"] != recipe["ply"] or original["engine_sha256"] != engine_sha
                        or original["score_cp_stm"] != int(data["score"][index])
                        or original["result_stm"] != float(data["result_stm"][index])):
                    raise ValueError("Held-out row order, label or original game provenance differs")
                expected = feature_indices(chess.Board(original["fen"]))
                for perspective in (0, 1):
                    active = data["features"][index, perspective]
                    active = active[active >= 0].tolist()
                    if len(active) != len(set(active)) or sorted(active) != sorted(expected[perspective]):
                        raise ValueError("Held-out feature set/count differs from the ordered source FEN")
                replayed += 1
    if replayed != count:
        raise ValueError("An original source line was not observed")
    game_ids = [row["game_id"] for row in rows]
    return {"rows": count, "game_ids": game_ids, "position_keys": [position_key(row["fen"]) for row in rows],
            "represented_game_ids": sorted(set(game_ids)), "listed_validation_games": len(known),
            "source_lines_replayed": replayed, "recipe_sha256": binding["sha256"],
            "scope": "Original source game/ply/FEN/score/result replayed; unordered perspective feature sets checked. HCE authenticated by prepared NPZ hash and probe identity; no native HCE rerun."}


@torch.no_grad()
def per_row_losses(model, data, batch_size=1024):
    if batch_size < 1 or not len(data["score"]):
        raise ValueError("Positive batch size and nonempty rows required")
    count = len(data["score"])
    losses = {key: np.empty(count, dtype=np.float64) for key in ("hce", "combined", "net_only")}
    losses.update({key: np.empty(count, dtype=np.int32) for key in ("correction_cp", "combined_cp")})
    was_training = model.training
    model.eval()
    try:
        for begin in range(0, count, batch_size):
            end = min(begin + batch_size, count)
            hce = torch.from_numpy(data["hce"][begin:end].astype(np.float32))
            score = torch.from_numpy(data["score"][begin:end].astype(np.float32))
            logits = model(_dense_features(data["features"][begin:end])).reshape(-1)
            if not torch.isfinite(logits).all():
                raise ValueError("Non-finite frozen network output")
            correction, combined = engine_centipawns(logits, hce)
            target = torch.sigmoid(score * K / CP_SCALE).double()
            for key, cp in (("hce", hce), ("combined", combined), ("net_only", correction)):
                probability = torch.sigmoid(cp * K / CP_SCALE).double()
                losses[key][begin:end] = ((probability - target) ** 2).cpu().numpy()
            losses["correction_cp"][begin:end] = correction.cpu().numpy().astype(np.int32)
            losses["combined_cp"][begin:end] = combined.cpu().numpy().astype(np.int32)
    finally:
        model.train(was_training)
    return losses


def verify_reference_holdout(data, manifest, shipped_metrics, reference_run, shipped_identity):
    """Authenticate equality with a previously frozen fresh-game baseline run."""
    reference_run = Path(reference_run).resolve()
    summary_path, snapshot_path = reference_run / "summary.json", reference_run / "input-manifest.json"
    summary, snapshot = json.loads(summary_path.read_text()), json.loads(snapshot_path.read_text())
    count = len(data["score"])
    if (summary.get("status") != "baseline_only" or summary.get("input_integrity") != "passed"
            or summary.get("validation_count") != count or summary.get("initial", {}).get("count") != count):
        raise ValueError("Reference is not a completed full-held-out baseline")
    config = summary.get("config", {})
    root = config.get("data_dir")
    if not isinstance(root, str) or not Path(root).is_absolute():
        raise ValueError("Original baseline prepared-data resolution root is absent")
    old_dir = Path(root)
    original_manifest = old_dir / "manifest.json"
    _hash_binding(original_manifest, summary.get("manifest_sha256"), "baseline original manifest")
    if json.loads(original_manifest.read_text()) != snapshot:
        raise ValueError("Reference manifest snapshot differs from the frozen original")
    initial_net = config.get("initial_net")
    if not isinstance(initial_net, dict) or initial_net.get("sha256") != shipped_identity.get("sha256"):
        raise ValueError("Reference shipped network differs")
    old_record = snapshot.get("files", {}).get("validation.npz", {})
    old_npz = old_dir / "validation.npz"
    _hash_binding(old_npz, old_record.get("sha256"), "baseline validation arrays")
    if old_record.get("rows") != count:
        raise ValueError("Reference validation array row count differs")
    with np.load(old_npz, allow_pickle=False) as arrays:
        if set(arrays.files) != set(data):
            raise ValueError("Reference validation array names differ")
        for name in data:
            previous = arrays[name]
            current = data[name]
            if previous.dtype != current.dtype or previous.shape != current.shape or previous.tobytes() != current.tobytes():
                raise ValueError("Reference validation array values/order differ: " + name)
    old_recipe = snapshot.get("artifacts", {}).get("validation-provenance.jsonl")
    current_recipe = manifest.get("artifacts", {}).get("validation-provenance.jsonl")
    if not isinstance(old_recipe, dict) or old_recipe != current_recipe:
        raise ValueError("Reference original held-out provenance recipe differs")
    old_recipe_path = old_dir / "validation-provenance.jsonl"
    _hash_binding(old_recipe_path, old_recipe.get("sha256"), "baseline original provenance recipe")
    for metric in ("teacher_mse_hce", "teacher_mse_combined"):
        previous = summary["initial"].get(metric)
        if (not isinstance(previous, (float, int)) or not math.isfinite(previous)
                or not math.isclose(previous, shipped_metrics[metric], abs_tol=1e-12, rel_tol=1e-12)):
            raise ValueError("Reference baseline metric differs: " + metric)
    inputs = [summary_path, snapshot_path, original_manifest, old_npz, old_recipe_path]
    return {"status": "PASS_SAME_FROZEN_VALIDATION_ARRAYS_RECIPE_AND_BASELINE", "rows": count,
            "reference_run": str(reference_run), "array_identity": "exact dtype/shape/value bytes of all four arrays",
            "recipe_identity": old_recipe, "metric_tolerance": 1e-12,
            "inputs": [{"path": str(path), "sha256": sha256(path)} for path in inputs]}


def _format_interval(stats):
    relative = stats["improvement_relative"]
    text = f"absolute reduction {stats['improvement_abs']:.9g}, 95% CI [{stats['ci95_abs'][0]:.9g}, {stats['ci95_abs'][1]:.9g}]"
    if relative is not None:
        text += f"; relative {100 * relative:.3f}%"
    if stats["ci95_relative"] is not None:
        low, high = stats["ci95_relative"]
        text += f", 95% CI [{100 * low:.3f}%, {100 * high:.3f}%]"
    else:
        text += "; relative CI undefined when a resample has zero reference loss"
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--shipped-net", type=Path, required=True)
    parser.add_argument("--candidate-net", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--bootstrap-draws", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--reference-baseline-run", type=Path,
                        help="Authenticate identical validation arrays/recipe and shipped metrics against this prior run")
    args = parser.parse_args(argv)
    if args.batch_size < 1 or args.bootstrap_draws < 1 or args.seed < 0:
        raise ValueError("Positive batch size/draws and nonnegative seed required")
    if args.out.exists():
        raise FileExistsError("Hold-out comparison output already exists: " + str(args.out))
    torch.set_num_threads(1)
    train, validation, manifest, manifest_sha = load_prepared_data(args.data_dir)
    del train
    provenance = validate_validation_provenance(args.data_dir, manifest, validation)
    game_ids = provenance["game_ids"]
    shipped, candidate = NNUE([128], qat=True), NNUE([128], qat=True)
    shipped_identity, candidate_identity = _load_initial(shipped, args.shipped_net), _load_initial(candidate, args.candidate_net)
    old = per_row_losses(shipped, validation, args.batch_size)
    new = per_row_losses(candidate, validation, args.batch_size)
    aggregate_metrics = []
    for model, rows in ((shipped, old), (candidate, new)):
        aggregate = evaluate(model, validation, args.batch_size)
        aggregate_metrics.append(aggregate)
        for key, metric in (("hce", "teacher_mse_hce"), ("combined", "teacher_mse_combined"), ("net_only", "teacher_mse_net_only")):
            if not math.isclose(float(rows[key].mean()), aggregate[metric], abs_tol=1e-12, rel_tol=1e-12):
                raise ValueError("Per-row loss aggregate differs from the complete trainer metric")
    reference_check = (verify_reference_holdout(validation, manifest, aggregate_metrics[0],
                                               args.reference_baseline_run, shipped_identity)
                       if args.reference_baseline_run is not None else None)
    comparisons = {
        "hce_vs_shipped": cluster_bootstrap(old["hce"], old["combined"], game_ids, args.bootstrap_draws, args.seed),
        "hce_vs_candidate": cluster_bootstrap(old["hce"], new["combined"], game_ids, args.bootstrap_draws, args.seed),
        "shipped_vs_candidate": cluster_bootstrap(old["combined"], new["combined"], game_ids, args.bootstrap_draws, args.seed),
    }
    # Rehash before publishing a result; every input remains independently bound.
    verify_unchanged_inputs(args.data_dir, manifest, manifest_sha)
    _hash_binding(args.data_dir / "validation-provenance.jsonl", provenance["recipe_sha256"], "validation-provenance.jsonl")
    for identity in (shipped_identity, candidate_identity):
        _hash_binding(Path(identity["path"]), identity["sha256"], identity["path"])
    if reference_check is not None:
        for identity in reference_check["inputs"]:
            _hash_binding(Path(identity["path"]), identity["sha256"], identity["path"])
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    arrays = {"game_ids": np.asarray(game_ids), "position_keys": np.asarray(provenance["position_keys"]),
              "hce_cp": validation["hce"], "teacher_cp": validation["score"], "loss_hce": old["hce"],
              "loss_shipped_combined": old["combined"], "loss_candidate_combined": new["combined"],
              "loss_shipped_net_only": old["net_only"], "loss_candidate_net_only": new["net_only"],
              "shipped_correction_cp": old["correction_cp"], "candidate_correction_cp": new["correction_cp"],
              "shipped_combined_cp": old["combined_cp"], "candidate_combined_cp": new["combined_cp"]}
    atomic_write(out / "per-row-losses.npz", lambda stream: np.savez_compressed(stream, **arrays))
    metrics = {"status": "PASS_FIXED_HELDOUT_LOSS_COMPARISON_NOT_ELO", "utc": datetime.now(timezone.utc).isoformat(),
               "manifest_sha256": manifest_sha, "shipped_net": shipped_identity, "candidate_net": candidate_identity,
               "rows": len(game_ids), "represented_games": len(set(game_ids)),
               "listed_validation_games": provenance["listed_validation_games"],
               "reference_holdout_check": reference_check,
               "mapping": {key: value for key, value in provenance.items() if key not in ("game_ids", "position_keys")},
               "loss_mse": {"hce_only": float(old["hce"].mean()), "shipped_hce_plus_net": float(old["combined"].mean()),
                            "candidate_hce_plus_net": float(new["combined"].mean()),
                            "shipped_residual_term_only": float(old["net_only"].mean()),
                            "candidate_residual_term_only": float(new["net_only"].mean())},
               "comparisons": comparisons, "bootstrap_draws": args.bootstrap_draws, "seed": args.seed,
               "per_row_artifact": {"path": "per-row-losses.npz", "sha256": sha256(out / "per-row-losses.npz"), "rows": len(game_ids)},
               "input_integrity": "passed", "aggregate_agreement_tolerance": 1e-12,
               "limitations": "Intervals condition on the frozen candidate and eligible represented game clusters. They do not correct model selection on this same holdout. Residual-term-only is diagnostic, not the deployed evaluator. No native inference or Elo claim."}
    _json(out / "metrics.json", metrics)
    losses = metrics["loss_mse"]
    text = f"""# Forge fixed-held-out network comparison

{metrics['rows']} eligible positions from {metrics['represented_games']} represented held-out games ({metrics['listed_validation_games']} listed game IDs). Every source-line recipe, feature set, score and STM result replayed; prepared arrays and original source/network hashes remained unchanged. HCE values are bound by the prepared NPZ/native-probe provenance and were not reexecuted here.

| Evaluator | Pure search-teacher probability MSE |
|---|---:|
| HCE only | {losses['hce_only']:.9g} |
| Shipped HCE + residual | {losses['shipped_hce_plus_net']:.9g} |
| Candidate HCE + residual | {losses['candidate_hce_plus_net']:.9g} |
| Shipped residual term only | {losses['shipped_residual_term_only']:.9g} |
| Candidate residual term only | {losses['candidate_residual_term_only']:.9g} |

Prior baseline comparison: {reference_check['status'] if reference_check else 'not supplied; this report does not authenticate an earlier holdout'}.

Candidate versus HCE: {_format_interval(comparisons['hce_vs_candidate'])}.

Candidate versus shipped: {_format_interval(comparisons['shipped_vs_candidate'])}.

Intervals use {args.bootstrap_draws} paired whole-game resamples, seed{args.seed}, with ratio(sum loss / sum rows) and linear percentile endpoints. Positive reduction means lower loss; no per-position independence is assumed. Empty eligible games are not represented clusters. Full per-row losses and game IDs are retained in `per-row-losses.npz`, SHA256 `{metrics['per_row_artifact']['sha256']}`. Full aggregate metrics agree with the trainer within1e-12.

These are conditional held-out loss comparisons, not Elo or independent confirmation after model selection on this holdout. Residual-term-only is diagnostic; the engine deploys HCE plus residual. Search and the shipped network were not modified.
"""
    atomic_write(out / "REPORT.md", lambda stream: stream.write(text.encode()))
    print(json.dumps({"status": metrics["status"], "rows": metrics["rows"], "games": metrics["represented_games"], "loss_mse": losses}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print("Error: " + str(error), file=sys.stderr)
        raise SystemExit(1)
