"""S-A3 planted-bug check: 28 mutants of the staged v3d copy (the 8 S39 + 9 S50 ones, + 11 for the lr schedule options); each
must be caught by its named test in test_v3d_sa3.py.

Mutants are written to F:\\opus_scratch\\sol_SA3\\tmp\\mutants\\opus_nnue_smoke_sa3_v3d_mutN.py (never a train_resid* name) and
tested one at a time in a child process at Idle priority (CPU, 1 thread).
  <venv python> -I -B mutation_check_sa3.py               (all 28)
  <venv python> -I -B mutation_check_sa3.py --only 20     (one mutant; its file gets a _rerun suffix)
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"F:\opus_scratch\sol_SA3")
SRC = ROOT / "opus_nnue_smoke_sa3_v3d.py"
OUT = ROOT / "tmp" / "mutants"
MUTANTS = [  # (name, anchor, replacement, the test that must catch it)
    ("OFF order seed changed", "rng_e = np.random.default_rng(a.seed * 1000 + e)", "rng_e = np.random.default_rng(a.seed * 1000 + e + 1)",
     "test_off_equals_v3b_full_permutation"),
    ("weighted epoch not shuffled", "    rng.shuffle(buf[:w])\n    return w", "    return w", "test_no_repeats_and_quotas"),
    ("quota ties to the higher index", "key=lambda f: (q[f] - share[f], f))", "key=lambda f: (q[f] - share[f], -f))", "test_known_cases"),
    ("chunked compaction offset bug", "            buf[w + i:w + j] = seg[i:j]", "            buf[w:w + j - i] = seg[i:j]",
     "test_chunked_copy_overlap"),
    ("steps/epoch ignore --epoch-positions", "    spe = (E or N) // a.batch_size", "    spe = N // a.batch_size",
     "test_uniform_is_prefix_of_v3b_order"),
    ("N == data size treated as ON", "    E = a.epoch_positions if a.epoch_positions < N else 0",
     "    E = a.epoch_positions if a.epoch_positions <= N else 0", "test_n_at_least_data_size_is_v3b"),
    ("--recent-weight without --epoch-positions accepted", "    if a.recent_weight != 1.0 and not a.epoch_positions:", "    if False:",
     "test_validation_before_any_output"),
    ("no capping at file size", "        capped = [f for f in active if left * sizes[f] * weights[f] >= sizes[f] * tot]  # share >= rows",
     "        capped = []", "test_known_cases"),
    # SA3 --init-weights
    ("init weights not loaded", "    model.load_state_dict(sd)\n    val = ck.get(\"val\") if payload else None",
     "    val = ck.get(\"val\") if payload else None", "test_loads_weights_only_and_logs_md5"),
    ("warm-start init check accepts any val", "            if abs(init[1.0] - ref[1.0]) > 1e-6 or abs(init[0.6] - ref[0.6]) > 1e-6:",
     "            if False:", "test_init_check_needs_the_same_val_subset"),
    ("init file loaded although --resume is given", "    if a.init_weights and a.resume:", "    if False:", "test_resume_does_not_load_init"),
    ("missing init file not rejected up front", "            ap.error(f\"--init-weights {a.init_weights}: no such file\")", "            pass",
     "test_missing_file_rejected_before_run_dir"),
    ("no hidden-size check", "    for key, want in ((\"hidden\", hidden), (\"residual\", residual)):", "    for key, want in ((\"residual\", residual),):",
     "test_hidden_and_residual_mismatch_rejected"),
    ("no residual-mode check", "    for key, want in ((\"hidden\", hidden), (\"residual\", residual)):", "    for key, want in ((\"hidden\", hidden),):",
     "test_hidden_and_residual_mismatch_rejected"),
    ("source md5 not in the settings dump", "    if init_md5:\n        settings[\"init_weights_md5\"] = init_md5\n", "",
     "test_loads_weights_only_and_logs_md5"),
    ("non-finite init weights accepted", "    if not all(torch.isfinite(v).all() for v in sd.values()):", "    if False:",
     "test_non_finite_rejected"),
    ("off settings dump lists init_weights", "V3C_OFF = {\"epoch_positions\": 0, \"recent_weight\": 1.0, \"init_weights\": None}",
     "V3C_OFF = {\"epoch_positions\": 0, \"recent_weight\": 1.0}", "test_off_settings_dump_equals_v3b"),
    # S-A3 lr schedule options
    ("cosine rewritten (same maths, other float rounding)",
     "        return lr * (floor + (1 - floor) * 0.5 * (1 + math.cos(math.pi * min(pr, 1.0))))",
     "        return lr * floor + lr * (1 - floor) * 0.5 * (1 + math.cos(math.pi * min(pr, 1.0)))", "test_default_is_v3b_bit_for_bit"),
    ("linear decays to zero instead of the floor",
     "        pr = (s - warmup) / max(1, total - warmup)\n        return lr * (floor + (1 - floor) * (1 - min(pr, 1.0)))",
     "        pr = (s - warmup) / max(1, total - warmup)\n        return lr * (1 - min(pr, 1.0))", "test_linear"),
    # (run 1 had "if s < d0" -> "if s <= d0" here: an equivalent mutant, the decay formula at its first step gives exactly the
    # peak lr (f + (1 - f) * 1 == 1.0), so no lr changes; replaced by this off-by-one that reaches the floor one step early)
    ("wsd decay one step ahead (floor reached one step early)", "        pr = (s - d0) / max(1, total - d0)",
     "        pr = (s - d0 + 1) / max(1, total - d0)", "test_wsd_rounding_and_stable_phase"),
    ("wsd decay length truncated (no round half up)", "    return max(warmup, total - max(1, int(decay_frac * total + 0.5)))",
     "    return max(warmup, total - max(1, int(decay_frac * total)))", "test_wsd_rounding_and_stable_phase"),
    ("wsd decay may start inside the warmup", "    return max(warmup, total - max(1, int(decay_frac * total + 0.5)))",
     "    return total - max(1, int(decay_frac * total + 0.5))", "test_wsd_decay_never_inside_warmup"),
    ("horizon ignores --lr-schedule-epochs", "    lr_epochs = a.lr_schedule_epochs or a.epochs", "    lr_epochs = a.epochs",
     "test_long_horizon_stops_early"),
    ("no warmup for linear/wsd", "    if s < warmup:\n        return lr * (s + 1) / warmup\n    if kind == \"cosine\":",
     "    if s < warmup and kind == \"cosine\":\n        return lr * (s + 1) / warmup\n    if kind == \"cosine\":", "test_linear"),
    ("schedule missing from the checkpoint config", "        config[\"lr_schedule\"] = a.lr_schedule\n", "",
     "test_settings_dump_and_config_record_the_schedule"),
    ("default schedule written to the config (default .json != v3b)",
     "    if not lr_default:  # v3d: recorded only for a non-default schedule (default -> v3b's config, .json and .pt)",
     "    if True:  # v3d: recorded only for a non-default schedule (default -> v3b's config, .json and .pt)",
     "test_off_json_and_stdout_equal_v3b"),
    ("settings dump drops the options of a set schedule",
     "    if lr_default:  # v3d: the three lr schedule options are written only when one of them is set (then all three)",
     "    if True:  # v3d: the three lr schedule options are written only when one of them is set (then all three)",
     "test_settings_dump_and_config_record_the_schedule"),
    ("--lr-decay-frac accepted without wsd", "    if a.lr_decay_frac != V3D_LR[\"lr_decay_frac\"] and a.lr_schedule != \"wsd\":",
     "    if False:", "test_lr_options_rejected_before_the_run_dir"),
]


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    adam = ROOT / "qa_adam_dml.py"  # the trainer imports it from its own folder
    assert hashlib.sha256(adam.read_bytes()).hexdigest() == "799faa89bc7b8dbd8c9a8747dd6658085eb0a69b84800af191db5ca7fd660cba"
    if not (OUT / adam.name).exists():
        shutil.copyfile(adam, OUT / adam.name)
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    only = None  # --only 20,21: run just these mutants (new file names, earlier mutant files are kept)
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    caught = 0
    for i, (name, old, new, expect) in enumerate(MUTANTS, 1):
        if only is not None and i not in only:
            continue
        assert src.count(old) == 1, f"mutant {i}: anchor not found once"
        path = OUT / f"opus_nnue_smoke_sa3_v3d_mut{i}{'_rerun' if only else ''}.py"
        path.write_text(src.replace(old, new), encoding="utf-8", newline="\n")
        proc = subprocess.run([sys.executable, "-I", "-B", str(HERE / "test_v3d_sa3.py"), "--v3c", str(path)], capture_output=True,
                              text=True, env=env, creationflags=0x00000040)
        failed = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+) ", proc.stderr, re.M)) - {"test_copies"})
        ok = proc.returncode != 0 and expect in failed
        caught += ok
        print(f"mutant {i} ({name}): {'CAUGHT' if ok else 'MISSED'} by {expect}: {expect in failed}; rc={proc.returncode}; "
              f"all failing tests: {', '.join(failed) or '-'}", flush=True)
    count = len(only) if only is not None else len(MUTANTS)
    print(f"RESULT {caught}/{count} mutants caught")
    return 0 if caught == count else 1


if __name__ == "__main__":
    raise SystemExit(main())
