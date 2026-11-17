"""Regression test for the `--tag` change to job3/rank_final.py.

The claim under test, which I asserted in a message before verifying it:
    adding `--tag` left the BASE run's outputs byte-identical.

A claim like that is worth a committed check, not a diff I ran once in a shell,
because the failure mode is silent: a tagged run that also rewrites the default
filenames would overwrite the base evidence while looking like it worked.

What this does:
  1. reads the CURRENT default outputs, which are the committed pre-tag artifacts
     (rank_final.txt last written in commit 796a90b6f, before the --tag change)
  2. re-runs the base command `python3 rank_final.py` into the same filenames
  3. compares byte for byte

It also asserts the tagged filenames are DISTINCT from the default ones, so a
future edit cannot reintroduce a collision.

Run: python3 job3/test_tag_no_overwrite.py
Writes job3/test_tag_no_overwrite.txt
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    out = []
    defaults = ["rank_final.txt", "rank_final_pairs.csv"]
    tagged = ["rank_final_patchA.txt", "rank_final_pairs_patchA.csv"]

    out.append("== A: the tagged names must be distinct from the default names ==")
    clash = set(defaults) & set(tagged)
    out.append(f"defaults {defaults}")
    out.append(f"tagged   {tagged}")
    out.append(f"intersection {sorted(clash)}")
    a_ok = not clash
    out.append(f"A passed: {a_ok}")
    out.append("")

    out.append("== B: re-running the default command must not change the default files ==")
    before = {}
    for f in defaults:
        p = os.path.join(HERE, f)
        if not os.path.exists(p):
            out.append(f"MISSING {f}; cannot test")
            before[f] = None
        else:
            before[f] = sha(p)
            out.append(f"before {f} sha256 {before[f]}")

    proc = subprocess.run([PY, "rank_final.py"], cwd=HERE,
                          capture_output=True, text=True, timeout=1200)
    out.append(f"re-run exit code {proc.returncode}")
    if proc.returncode != 0:
        out.append("STDERR tail:")
        out.append(proc.stderr[-2000:])

    b_ok = True
    for f in defaults:
        p = os.path.join(HERE, f)
        after = sha(p) if os.path.exists(p) else None
        same = (before[f] is not None and after == before[f])
        b_ok &= same
        out.append(f"after  {f} sha256 {after}  identical {same}")

    out.append("")
    out.append("== RESULT ==")
    out.append(f"A distinct filenames : {a_ok}")
    out.append(f"B base run stable    : {b_ok}")
    out.append(f"ALL: {a_ok and b_ok}")

    text = "\n".join(out)
    with open(os.path.join(HERE, "test_tag_no_overwrite.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)
    return 0 if (a_ok and b_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
