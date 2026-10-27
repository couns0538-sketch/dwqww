"""Tests for forge_sol_S30_log_curves.py and forge_sol_S30_fit.py on synthetic log fixtures (stdlib only).
Temporary folders go to TMP. Run: python -I -B test_forge_sol_S30.py"""
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
CURVES = HERE / "forge_sol_S30_log_curves.py"
FIT = HERE / "forge_sol_S30_fit.py"


def epoch_line(e, n, teacher, b06):
    return (f"EPOCH {e}/{n} done in 97s train_mse=0.004121 | HOLDOUT n=999,424 mse_teacher={teacher:.6f} (HCE 0.005077, +21.57%) "
            f"mse_b0.6={b06:.6f} (HCE 0.017049, +10.11%) mse_b0.8=0.006949")


def final_line(teacher, b06):
    return f"FINAL FULL HOLDOUT n=16,384,000: net mse_teacher={teacher:.6f} mse_b0.6={b06:.6f} mse_b0.8=0.006761 | HCE 0.005070/0.017052/b0.8 0.008355"


def write_run(runs: Path, name: str, epochs: int, seed: int, positions: int, b06: float, teacher: float = 0.0045, lr="7.07e-4", resume=False):
    cmd = (f"cmd: python -u train_resid_v3a.py --train a.pos b.pos --holdout h.pos --hce-dir x --residual --final-full-val --shape 256 "
           f"--epochs {epochs} --lr {lr} --blend-end 0.6 --seed {seed} --batch-size 8192 --warmup-steps 300 --val-positions 1000000 --run-dir r\r\n")
    (runs / f"{name}.cmd.txt").write_bytes(cmd.encode())
    lines = ["holdout: 16,388,575 positions from 2 files (1s)", f"train: {positions:,} positions from 19 files (4s load)",
             f"steps/epoch=16,770 total=804,960 batch=8192 lr={lr} cosine blend 1.0->0.6"]
    lines += [epoch_line(e, epochs, teacher + 0.0001 / e, b06 + 0.0002 / e) for e in range(1, epochs + (0 if resume else 1))]
    if resume:
        (runs / f"{name}.log").write_bytes(("\r\n".join(lines) + "\r\n").encode())
        (runs / f"{name}.resume1.log").write_bytes(("resumed x: next_epoch=1\r\n" + epoch_line(epochs, epochs, teacher, b06) + "\r\n\x00"
                                                     + final_line(teacher, b06) + "\r\n").encode())
    else:
        lines.append(final_line(teacher, b06))
        (runs / f"{name}.log").write_bytes(("\r\n".join(lines) + "\r\n").encode())


def run(script, *args):
    return subprocess.run([sys.executable, "-I", "-B", str(script), *map(str, args)], capture_output=True, text=True)


class Curves(unittest.TestCase):
    def make(self, tmp):
        runs = tmp / "runs"
        runs.mkdir()
        write_run(runs, "a_e48_s1", 4, 1, 161913894, 0.014298)
        write_run(runs, "b_e48_s2", 4, 2, 161913894, 0.014271)
        write_run(runs, "c_e48_s3", 4, 3, 191913894, 0.014251, resume=True)
        write_run(runs, "d_e48_s4", 4, 4, 221913894, 0.014212)
        (runs / "x.guard.log").write_text(final_line(0.1, 0.1) + "\n")
        (runs / "x.export_ep16.log").write_text(final_line(0.1, 0.1) + "\n")
        return runs

    def test_parse_cite_skip_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            runs = self.make(tmp)
            r = run(CURVES, "--runs", runs, "--out", tmp / "out")
            self.assertEqual(r.returncode, 0, r.stderr)
            rows = list(csv.DictReader(open(tmp / "out" / "final_table.csv", encoding="utf-8")))
            self.assertEqual(sorted(x["run"] for x in rows), ["a_e48_s1", "b_e48_s2", "c_e48_s3", "d_e48_s4"])   # guard/export skipped
            c = [x for x in rows if x["run"] == "c_e48_s3"][0]
            self.assertEqual(c["where"], "c_e48_s3.resume1.log:3")            # resumed FINAL cited in its own file, NUL stripped
            self.assertEqual((c["epochs"], c["seed"], c["lr"], c["train_positions"]), ("4", "3", "7.07e-4", "191913894"))
            a = [x for x in rows if x["run"] == "a_e48_s1"][0]
            self.assertEqual(a["where"], "a_e48_s1.log:8")
            curves = list(csv.DictReader(open(tmp / "out" / "epoch_curves.csv", encoding="utf-8")))
            self.assertEqual(len(curves), 16)
            spread = list(csv.DictReader(open(tmp / "out" / "seed_spread.csv", encoding="utf-8")))
            two = [s for s in spread if s["runs"] == "2"][0]
            self.assertAlmostEqual(float(two["b06_max"]) - float(two["b06_min"]), 0.000027, places=9)

    def test_refuses_output_inside_runs_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            runs = self.make(tmp)
            self.assertNotEqual(run(CURVES, "--runs", runs, "--out", runs / "out").returncode, 0)
            self.assertEqual(run(CURVES, "--runs", runs, "--out", tmp / "o1").returncode, 0)
            self.assertEqual(run(CURVES, "--runs", runs, "--out", tmp / "o2").returncode, 0)
            for name in ("final_table.csv", "epoch_curves.csv", "seed_spread.csv", "summary.json"):
                self.assertEqual((tmp / "o1" / name).read_bytes(), (tmp / "o2" / name).read_bytes(), name)


class Fit(unittest.TestCase):
    def test_data_curve_slope_and_seed_spread(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            runs = tmp / "runs"
            runs.mkdir()
            import math
            for i, positions in enumerate((140e6, 160e6, 180e6, 200e6, 220e6, 240e6)):
                b06 = 0.0175 - 0.00024 * math.log(positions)          # exact log-linear: slope -0.00024 per ln
                for seed in (1, 2):
                    write_run(runs, f"r{i}_s{seed}", 48, seed + 10 * i, int(positions), b06 + (0.00001 if seed == 2 else 0.0))
            self.assertEqual(run(CURVES, "--runs", runs, "--out", tmp / "out").returncode, 0)
            r = run(FIT, "--final", tmp / "out" / "final_table.csv", "--out", tmp / "fit.json")
            self.assertEqual(r.returncode, 0, r.stderr)
            fit = json.loads((tmp / "fit.json").read_text(encoding="utf-8"))
            s = fit["data_curve_e48"]["fit"]["b06 = c + s*ln(positions)"]["s"]
            self.assertAlmostEqual(s, -0.00024, delta=2e-6)
            pooled = fit["seed_spread_pooled"]["b06_pooled_sd"]
            self.assertAlmostEqual(pooled, 0.00001 / 2 ** 0.5, delta=1e-7)
            r2 = run(FIT, "--final", tmp / "out" / "final_table.csv", "--out", tmp / "fit2.json")
            self.assertEqual((tmp / "fit.json").read_bytes(), (tmp / "fit2.json").read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
