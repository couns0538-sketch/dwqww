#!/usr/bin/env python3
"""Planted-bug check for jobA_cause.py: the unit tests must PASS on the clean copy and FAIL on each mutant.
Usage: python -I mutation_check.py <scratch dir outside the repo>"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MUTANTS = {
    "clean": None,
    "abba_pairs_B2_with_A1": ("out += [b1 / a1, b2 / a2]", "out += [b1 / a1, b2 / a1]"),
    "jmp_may_fall_through": ('allowed = {target} if mnem == "jmp" else {target, nxt}', "allowed = {target, nxt}"),
    "one_sided_sign_test": ("return min(1.0, 2 * min(lower, upper))", "return min(1.0, min(lower, upper))"),
    "zmm_counted_as_ymm": ('if "%zmm" in ins:\n            c["zmm"] += 1', 'if "%zmm" in ins:\n            c["ymm"] += 1'),
}


def main() -> int:
    out_dir = Path(sys.argv[1]).resolve()
    if HERE in out_dir.parents or out_dir == HERE:
        sys.exit("scratch dir must be outside the source folder")
    out_dir.mkdir(parents=True, exist_ok=True)
    source = (HERE / "jobA_cause.py").read_text(encoding="utf-8")
    ok = True
    for name, edit in MUTANTS.items():
        text = source
        if edit is not None:
            if source.count(edit[0]) != 1:
                sys.exit(f"{name}: anchor not found exactly once")
            text = source.replace(edit[0], edit[1])
        path = out_dir / f"jobA_cause_{name}.py"
        path.write_text(text, encoding="utf-8")
        env = dict(os.environ, JOBA_CAUSE_PATH=str(path))
        proc = subprocess.run([sys.executable, "-I", str(HERE / "test_jobA_cause.py")], env=env,
                              capture_output=True, text=True)
        passed = proc.returncode == 0
        expected = edit is None
        verdict = "as expected" if passed == expected else "UNEXPECTED"
        ok &= passed == expected
        failed = [l.split(" ")[0] for l in proc.stderr.splitlines() if l.endswith(("FAIL", "ERROR"))]
        print(f"{name:<24} tests {'PASS' if passed else 'FAIL'} ({verdict}); failing: {', '.join(failed) or '-'}")
    print("MUTATION CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
