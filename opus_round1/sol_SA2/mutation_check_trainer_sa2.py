"""S-A2 trainer planted-bug check: mutants of the staged clip copy; each must be caught by its named test in
test_trainer_clip_sa2.py, and the unmutated copy must pass the same tests.

Mutants are written to F:\\opus_scratch\\sol_SA2\\tmp\\mutants\\opus_nnue_smoke_sa2_clip_mutN.py (never a train_resid* name) and
tested one at a time in a child process at Idle priority (CPU, 1 thread).
  <venv python> -I -B mutation_check_trainer_sa2.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"F:\opus_scratch\sol_SA2")
SRC = ROOT / "opus_nnue_smoke_sa2_clip.py"
OUT = ROOT / "tmp" / "mutants"
IDLE = 0x00000040
MUTANTS = [  # (name, anchor, replacement, the test that must catch it)
    ("clip not applied in the training loop",
     "            if clip_units:  # S-A2 --weight-clip (after v3c's int16-rail projection; never looser than it)\n"
     "                model.clip_weights(clip_units)\n", "", "test_training_loop_clips"),
    ("clip bound scaled wrong", "        bound = units / SCALE\n", "        bound = 2 * units / SCALE\n", "test_clip_weights_exact"),
    ("export check never raises", "    if bad:  # units <= 32766", "    if False:  # units <= 32766", "test_int16_check"),
    ("export check never raises (export path)", "    if bad:  # units <= 32766", "    if False:  # units <= 32766",
     "test_export_refuses_before_writing"),
    ("off settings dump lists weight_clip", "V3C_OFF = {\"epoch_positions\": 0, \"recent_weight\": 1.0, \"init_weights\": None,\n"
     "           \"weight_clip\": 0.0}", "V3C_OFF = {\"epoch_positions\": 0, \"recent_weight\": 1.0, \"init_weights\": None}",
     "test_off_default_and_settings_dump"),
    ("the int16 rail accepted as a bound", "<= math.floor(a.weight_clip * SCALE) <= INT16_MAX - 1:",
     "<= math.floor(a.weight_clip * SCALE) <= INT16_MAX:", "test_validation"),
    ("bare --weight-clip one unit too large", "CLIP_UNITS_DEFAULT = 21704", "CLIP_UNITS_DEFAULT = 21705",
     "test_bare_flag_is_the_largest_2_24_bound"),
    ("the clip check alters the export", "    clip_report = int16_check(quant, clip_units) if clip_units else None",
     "    clip_report = int16_check(quant, clip_units) if clip_units else None\n    if clip_units:\n        quant[3] = quant[3] // 2",
     "test_export_off_and_on_byte_identical_to_v3c"),
]


def run_test(copy: Path, test: str) -> tuple[int, str]:
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", TMP=str(ROOT / "tmp"), TEMP=str(ROOT / "tmp"))
    r = subprocess.run([sys.executable, "-I", "-B", str(HERE / "test_trainer_clip_sa2.py"), "--clip", str(copy), f"Tests.{test}"],
                       capture_output=True, text=True, env=env, creationflags=IDLE, timeout=1800)
    return r.returncode, (r.stderr.strip().splitlines() or [""])[-1]


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    ok = True
    tests = sorted({m[3] for m in MUTANTS})
    for t in tests:  # control: the unmutated copy passes every named test
        rc, last = run_test(SRC, t)
        good = rc == 0
        ok &= good
        print(f"control {t}: rc={rc} {'OK' if good else 'FAILED'} | {last}", flush=True)
    for k, (name, anchor, repl, test) in enumerate(MUTANTS, 1):
        assert src.count(anchor) == 1, f"{name}: anchor occurs {src.count(anchor)} times"
        mutant = OUT / f"opus_nnue_smoke_sa2_clip_mut{k}.py"
        if mutant.exists():
            mutant = OUT / f"opus_nnue_smoke_sa2_clip_mut{k}_{os.getpid()}.py"
        mutant.write_text(src.replace(anchor, repl), encoding="utf-8", newline="\n")
        rc, last = run_test(mutant, test)
        caught = rc != 0
        ok &= caught
        print(f"mutant {k} ({name}) -> {test}: rc={rc} {'CAUGHT' if caught else 'NOT CAUGHT'} | {last}", flush=True)
    print("TRAINER MUTATION CHECK PASS" if ok else "TRAINER MUTATION CHECK FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
