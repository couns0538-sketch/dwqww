"""Planted-bug check for the S30 tools: every mutant must make test_forge_sol_S30.py fail; the unmutated copy passes.
usage: python -I -B mutation_check_s30.py <new scratch dir>"""
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
FILES = ("forge_sol_S30_log_curves.py", "forge_sol_S30_fit.py", "test_forge_sol_S30.py")
MUTANTS = {
    "final_fields_swapped": ("forge_sol_S30_log_curves.py",
                             'finals.append({"run": name, "where": where, "holdout_n": int(num(m[1])), "teacher": num(m[2]), "b06": num(m[3]),',
                             'finals.append({"run": name, "where": where, "holdout_n": int(num(m[1])), "teacher": num(m[3]), "b06": num(m[2]),'),
    "resume_not_joined": ("forge_sol_S30_log_curves.py", '    name = re.sub(r"\\.resume\\d+\\.log$", "", name)\n', ""),
    "guard_logs_read": ("forge_sol_S30_log_curves.py", 'SKIP = (".guard.log", ".chain.log")', 'SKIP = (".chain.log",)'),
    "line_numbers_from_0": ("forge_sol_S30_log_curves.py", "enumerate(read_lines(log), 1)", "enumerate(read_lines(log))"),
    "slope_per_log10": ("forge_sol_S30_fit.py", "    xs = [math.log(r[\"train_positions\"]) for r in family]",
                        "    xs = [math.log10(r[\"train_positions\"]) for r in family]"),
    "pooled_sd_population": ("forge_sol_S30_fit.py", "            pooled_num[metric] += statistics.variance(values) * (len(values) - 1)",
                             "            pooled_num[metric] += statistics.pvariance(values) * (len(values) - 1)"),
}


def main(argv):
    scratch = Path(argv[0])
    scratch.mkdir()
    failures = 0
    for name in ["unmutated", *MUTANTS]:
        d = scratch / name
        d.mkdir()
        for f in FILES:
            shutil.copy2(HERE / f, d / f)
        if name != "unmutated":
            target, old, new = MUTANTS[name]
            text = (d / target).read_text(encoding="utf-8")
            if text.count(old) != 1:
                print(f"{name}: anchor not found exactly once"); failures += 1; continue
            (d / target).write_text(text.replace(old, new), encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-I", "-B", str(d / "test_forge_sol_S30.py")], cwd=d, env=dict(os.environ),
                           capture_output=True, text=True)
        last = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-1:]
        want_fail = name != "unmutated"
        ok = (r.returncode != 0) if want_fail else (r.returncode == 0)
        failures += not ok
        print(f"{name:24s} rc {r.returncode} ({last[0] if last else ''}) -> {'CAUGHT' if want_fail and ok else 'PASS' if ok else 'NOT CAUGHT' if want_fail else 'FAIL'}")
    print("MUTATION CHECK:", "PASS" if not failures else f"FAIL ({failures})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
