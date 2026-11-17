#!/usr/bin/env python3
"""Sanitizer run over the 200-position set, with the sanitizer PROVED live.

A sanitizer run that reports nothing is worth exactly what the evidence that it
was working is worth. Three pieces of evidence are required here and all are
recorded:

1. The binary really contains the sanitizer runtime. Checked by looking for the
   ASan/UBSan runtime symbols and by reading the compiler's own build flags, not
   by trusting the build command that was typed.
2. A PLANTED FAULT is caught. The same source is rebuilt with a deliberate
   heap-buffer-overflow and a deliberate signed-integer overflow behind a
   test-only env var; each must produce a sanitizer report and a non-zero exit.
   This is the only thing that distinguishes "looked and found nothing" from
   "could not have found anything".
3. The clean run examined its rows: every position's search produced an
   `info depth` line, so a run where the engine never really searched cannot
   report a pass.

The planted faults live in a separate translation unit compiled only into the
control binary, so the audited binary is built from the audited sources with no
test hooks in it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import driver  # noqa: E402


def runtime_symbols(binary: str) -> dict:
    """Which sanitizer runtimes are linked into this binary."""
    try:
        out = subprocess.run(["nm", "-C", binary], capture_output=True, text=True, timeout=120).stdout
    except Exception as exc:  # pragma: no cover - nm missing
        return {"error": str(exc)}
    return {
        "asan_present": "__asan_init" in out or "asan_init" in out,
        "ubsan_present": "__ubsan_handle_add_overflow" in out or "__ubsan_handle" in out,
        "asan_symbols": len(re.findall(r"\b__asan_", out)),
        "ubsan_symbols": len(re.findall(r"\b__ubsan_", out)),
    }


def build_flags(build_dir: str) -> dict:
    """The flags the compiler was actually given, from its own cache."""
    path = os.path.join(build_dir, "CMakeFiles", "forge.dir", "flags.make")
    if not os.path.exists(path):
        return {"error": f"no {path}"}
    text = open(path).read()
    return {
        "sanitize_flag": re.search(r"-fsanitize=\S+", text).group(0) if re.search(r"-fsanitize=\S+", text) else None,
        "debug_info": "-g" in text,
        "no_omit_frame_pointer": "-fno-omit-frame-pointer" in text,
        "raw_contains_fsanitize": "-fsanitize=" in text,
    }


def run_set(binary: str, fens: list[str], depth: int, env: dict, log_path: str,
            option: str | None = None) -> dict:
    """Search every position and record what the sanitizer said."""
    sanitizer_hits: list[str] = []
    searched = 0
    errors: list[str] = []
    old = dict(os.environ)
    os.environ.update(env)
    try:
        options = {}
        if option:
            name, _, value = option.partition("=")
            options[name] = value or "true"
        eng = driver.Engine(binary, options=options, timeout=180.0)
        for index, fen in enumerate(fens):
            try:
                eng.set_position(fen, cold=True)
                res = eng.go_depth(depth)
                searched += 1
            except Exception as exc:
                errors.append(f"row {index} {fen}: {exc}")
                break
        eng.quit()
    finally:
        os.environ.clear()
        os.environ.update(old)

    # The engine's log holds everything both streams said, which is where a
    # sanitizer report lands: ASan writes to stderr, which the driver merges.
    text = "\n".join(eng.log) if 'eng' in dir() else ""
    for line in text.splitlines():
        if re.search(r"(AddressSanitizer|runtime error:|SUMMARY: |UndefinedBehaviorSanitizer)", line):
            sanitizer_hits.append(line)
    with open(log_path, "w") as fh:
        fh.write(text)
    return {
        "positions": len(fens),
        "searched": searched,
        "sanitizer_hits": len(sanitizer_hits),
        "sanitizer_lines": sanitizer_hits[:40],
        "errors": errors,
    }


def planted_fault(binary: str, name: str, env_var: str, log_path: str) -> dict:
    """Run the control binary and require it to report a fault.

    The control binary carries two planted faults behind env vars. A run that
    exits 0, or that produces no sanitizer line, means the sanitizer is not
    live and the clean result means nothing.
    """
    env = dict(os.environ)
    env[env_var] = "1"
    proc = subprocess.run([binary], input=b"uci\nquit\n", capture_output=True, env=env, timeout=300)
    text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    with open(log_path, "w") as fh:
        fh.write(text)
    caught = bool(re.search(r"(AddressSanitizer|runtime error:|UndefinedBehaviorSanitizer)", text))
    return {
        "fault": name,
        "env": env_var,
        "exit_code": proc.returncode,
        "sanitizer_reported": caught,
        "evidence": [l for l in text.splitlines() if re.search(r"(ERROR|SUMMARY|runtime error)", l)][:8],
        "passed": caught and proc.returncode != 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", required=True, help="sanitized engine built from audited sources")
    ap.add_argument("--clean-build", required=True, help="its cmake build dir")
    ap.add_argument("--planted", required=True, help="sanitized control binary with planted faults")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--option", default="", help="NAME=VALUE to enable one switch")
    args = ap.parse_args()

    fens = [l.strip() for l in open(os.path.join(args.corpus, "positions200.fens")) if l.strip()]
    os.makedirs(args.out, exist_ok=True)

    syms = runtime_symbols(args.clean)
    flags = build_flags(args.clean_build)
    if not (syms.get("asan_present") and syms.get("ubsan_present")):
        raise SystemExit(f"sanitizer runtime not linked: {syms}")
    if not flags.get("raw_contains_fsanitize"):
        raise SystemExit(f"build flags carry no -fsanitize: {flags}")

    faults = [
        planted_fault(args.planted, "heap-buffer-overflow", "FORGE_PLANT_ASAN",
                      os.path.join(args.out, "planted-asan.txt")),
        planted_fault(args.planted, "signed-integer-overflow", "FORGE_PLANT_UBSAN",
                      os.path.join(args.out, "planted-ubsan.txt")),
    ]
    if not all(f["passed"] for f in faults):
        raise SystemExit(f"planted fault NOT caught, so the clean run proves nothing: {faults}")

    clean = run_set(args.clean, fens, args.depth, {}, os.path.join(args.out, "clean-run.txt"),
                    args.option or None)
    if clean["searched"] != len(fens):
        raise SystemExit(f"only {clean['searched']} of {len(fens)} positions searched: {clean['errors']}")

    report = {
        "binary": args.clean,
        "option": args.option or None,
        "runtime": syms,
        "build_flags": flags,
        "planted_faults": faults,
        "clean_run": clean,
        "passed": (
            syms["asan_present"] and syms["ubsan_present"]
            and clean["sanitizer_hits"] == 0
            and clean["searched"] == len(fens)
            and all(f["passed"] for f in faults)
        ),
    }
    with open(os.path.join(args.out, "sanitizer.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "planted_faults"}, indent=1))
    for f in faults:
        print(f"  planted {f['fault']}: caught={f['sanitizer_reported']} exit={f['exit_code']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
