#!/usr/bin/env python3
"""Planted-bug check for picker_audit.py.
(a) The unit tests must PASS on the clean copy and FAIL on each tool mutant.
(b) With --dis/--exe: the audit must PASS on the real lock disassembly and report CHECK (exit 1)
    when a call to operator new is planted into MovePicker::next (copy in the scratch dir).
Usage: python -I -B mutation_check.py <scratch dir outside the repo> [--dis lock_exe.dis --exe lock.exe]"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MUTANTS = {
    "clean": None,
    "alloc_regex_misses_new": ('r"operator new|\\bmalloc', 'r"\\bmalloc'),
    "closure_ignores_tail_jumps": ('DIRECT_RE = re.compile(r"^(call|jmp)', 'DIRECT_RE = re.compile(r"^(call)'),
    "switch_targets_unchecked": ("inside = all(lo <= t < hi for t in targets)", "inside = True"),
    "any_import_allowed": ("return imp.group(1) in ALLOWED_IMPORTS,", "return True,"),
}


def run(cmd, env=None):
    return subprocess.run(cmd, env=env, capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scratch", type=Path)
    ap.add_argument("--dis", type=Path)
    ap.add_argument("--exe", type=Path)
    args = ap.parse_args()
    out_dir = args.scratch.resolve()
    if out_dir == HERE or HERE in out_dir.parents:
        sys.exit("scratch dir must be outside the source folder")
    out_dir.mkdir(parents=True, exist_ok=True)
    source = (HERE / "picker_audit.py").read_text(encoding="utf-8")
    ok = True
    for name, edit in MUTANTS.items():
        text = source
        if edit is not None:
            if source.count(edit[0]) != 1:
                sys.exit(f"{name}: anchor not found exactly once")
            text = source.replace(edit[0], edit[1])
        path = out_dir / f"picker_audit_{name}.py"
        path.write_text(text, encoding="utf-8")
        proc = run([sys.executable, "-I", "-B", str(HERE / "test_picker_audit.py")],
                   env=dict(os.environ, PICKER_AUDIT_PATH=str(path)))
        passed = proc.returncode == 0
        good = passed == (edit is None)
        ok &= good
        failed = [l.split(" ")[0] for l in proc.stderr.splitlines() if l.endswith(("FAIL", "ERROR"))]
        print(f"(a) {name:<28} tests {'PASS' if passed else 'FAIL'} ({'as expected' if good else 'UNEXPECTED'});"
              f" failing: {', '.join(failed) or '-'}")
    if args.dis and args.exe:
        audit = [sys.executable, "-I", "-B", str(HERE / "picker_audit.py")]
        real = run(audit + [str(args.dis), "--exe", str(args.exe)])
        good = real.returncode == 0 and "ALLOCATION AUDIT: PASS" in real.stdout
        ok &= good
        print(f"(b) real lock disassembly: exit {real.returncode} ({'as expected' if good else 'UNEXPECTED'})")
        text = args.dis.read_text(encoding="utf-8", errors="replace")
        new_entry = re.search(r"^([0-9a-f]+) <operator new\(unsigned long long\)>:$", text, re.M)
        head = re.search(r"^[0-9a-f]+ <forge::MovePicker::next\(bool\)>:\n(\s+)([0-9a-f]+):", text, re.M)
        if not (new_entry and head):
            sys.exit("cannot plant: symbols not found")
        addr = int(head.group(2), 16)
        target = int(new_entry.group(1), 16)
        planted_line = f"{head.group(1)}{addr:x}:\tcall   {target:x} <operator new(unsigned long long)>\n"
        insert_at = head.end() - len(head.group(1)) - len(head.group(2)) - 1
        planted = text[:insert_at] + planted_line + text[insert_at:]
        ppath = out_dir / "lock_exe_planted_new.dis"
        ppath.write_text(planted, encoding="utf-8")
        bad = run(audit + [str(ppath), "--exe", str(args.exe)])
        hits = re.search(r"allocation-family calls reachable from the picker: (\d+)", bad.stdout)
        n_hits = int(hits.group(1)) if hits else 0
        good = bad.returncode == 1 and n_hits >= 1 and "ALLOCATION AUDIT: CHECK" in bad.stdout
        ok &= good
        print(f"(b) planted operator-new call in MovePicker::next: exit {bad.returncode}, {n_hits} allocation hits, "
              f"{'CHECK reported' if 'ALLOCATION AUDIT: CHECK' in bad.stdout else 'no CHECK'} "
              f"({'as expected' if good else 'UNEXPECTED'})")
    print("MUTATION CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
