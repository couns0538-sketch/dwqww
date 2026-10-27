"""S39 planted-bug check: 8 mutants of the staged v3c copy; each must be caught by its named test in test_v3c_s39.py.

Mutants are written to F:\\opus_scratch\\sol_S39\\tmp\\mutants\\opus_nnue_smoke_s39_v3c_mutN.py (never a train_resid* name) and
tested one at a time in a child process at Idle priority (CPU, 1 thread).
  <venv python> -I -B mutation_check_s39.py
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
ROOT = Path(r"F:\opus_scratch\sol_S39")
SRC = ROOT / "opus_nnue_smoke_s39_v3c.py"
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
]


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    adam = ROOT / "qa_adam_dml.py"  # the trainer imports it from its own folder
    assert hashlib.sha256(adam.read_bytes()).hexdigest() == "799faa89bc7b8dbd8c9a8747dd6658085eb0a69b84800af191db5ca7fd660cba"
    if not (OUT / adam.name).exists():
        shutil.copyfile(adam, OUT / adam.name)
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    caught = 0
    for i, (name, old, new, expect) in enumerate(MUTANTS, 1):
        assert src.count(old) == 1, f"mutant {i}: anchor not found once"
        path = OUT / f"opus_nnue_smoke_s39_v3c_mut{i}.py"
        path.write_text(src.replace(old, new), encoding="utf-8", newline="\n")
        proc = subprocess.run([sys.executable, "-I", "-B", str(HERE / "test_v3c_s39.py"), "--v3c", str(path)], capture_output=True,
                              text=True, env=env, creationflags=0x00000040)
        failed = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+) ", proc.stderr, re.M)) - {"test_copies"})
        ok = proc.returncode != 0 and expect in failed
        caught += ok
        print(f"mutant {i} ({name}): {'CAUGHT' if ok else 'MISSED'} by {expect}: {expect in failed}; rc={proc.returncode}; "
              f"all failing tests: {', '.join(failed) or '-'}", flush=True)
    print(f"RESULT {caught}/{len(MUTANTS)} mutants caught")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
