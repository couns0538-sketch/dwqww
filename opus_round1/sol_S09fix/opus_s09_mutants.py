#!/usr/bin/env python3
"""Planted-bug check for the S09 v2 files: per mutant, copy the files and test_forge_sol_S09_v2.py into a fresh
folder, apply one single-line bug (pattern must occur exactly once), run the tests, require them to FAIL.
usage: opus_s09_mutants.py --work DIR   (DIR must not exist; S09_CURRENT_TRAINER is passed through if set)"""
from __future__ import annotations
import argparse, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["forge_sol_S09_trainer_buckets_v2.py", "forge_sol_S09_export_identity_v2.py",
         "forge_sol_S09_holdout_validate_v2.py", "opus_s09_patch_one_file.py", "opus_s09_split_pos.py",
         "forge_sol_S09_f006_recipe_args_v2.txt", "forge_sol_S09_f006_recipe_v2.json", "test_forge_sol_S09_v2.py"]
T = "forge_sol_S09_trainer_buckets_v2.py"
MUTANTS = [
    ("default_shape_256", T, 'ap.add_argument("--shape", type=int, default=128,', 'ap.add_argument("--shape", type=int, default=256,'),
    ("default_residual_on", T, '    ap.add_argument("--residual", action="store_true")\n',
     '    ap.add_argument("--residual", action="store_true", default=True)\n'),
    ("head_off_by_one", T, "torch.div(pieces - 1, 4, rounding_mode=\"floor\")", "torch.div(pieces, 4, rounding_mode=\"floor\")"),
    ("export_head_macro", T, 'lines.insert(3, "#define FORGE_NNUE_OUTPUT_HEADS 8")', 'lines.insert(3, "#define FORGE_NNUE_OUTPUT_HEADS 1")'),
    ("nibble_counter", "forge_sol_S09_holdout_validate_v2.py", "np.clip((pieces - 1) // 4, 0, 7)", "np.clip(pieces // 4, 0, 7)"),
    ("split_meta_offset", "opus_s09_split_pos.py", '"r", 16 + n * 34, (n,))', '"r", 16 + n * 33, (n,))'),
    ("patch_removed_lines", "opus_s09_patch_one_file.py", '            if tag in (" ", "-"):\n                if base_lines',
     '            if tag == " ":\n                if base_lines'),
    ("parse_heads", "forge_sol_S09_export_identity_v2.py", 'heads = arrays["NnueB2"].size', "heads = 1"),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True)
    a = ap.parse_args(argv)
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=False)
    survived = 0
    for name, target, old, new in MUTANTS:
        d = work / name
        d.mkdir()
        for f in FILES:
            shutil.copy2(HERE / f, d / f)
        src = (d / target).read_text(encoding="utf-8")
        if src.count(old) != 1:
            raise SystemExit(f"{name}: pattern occurs {src.count(old)} times in {target}")
        (d / target).write_text(src.replace(old, new), encoding="utf-8", newline="\n")
        proc = subprocess.run([sys.executable, "-I", "-B", str(d / "test_forge_sol_S09_v2.py")], capture_output=True,
                              text=True, env=dict(os.environ))
        failed = [l for l in proc.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))]
        status = "KILLED" if proc.returncode != 0 else "SURVIVED"
        survived += status == "SURVIVED"
        print(f"{name}: {status} (rc={proc.returncode}); failing: {', '.join(failed) or '-'}")
    print(f"{len(MUTANTS) - survived}/{len(MUTANTS)} mutants killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
