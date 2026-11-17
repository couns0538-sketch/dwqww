#!/usr/bin/env python3
"""Run every mutant through the loader probe (release + ASan/UBSan) and the real engine.

For each mutant we record, separately:
  * probe_rel   : the loader's verdict and its exact error text (stdout/stderr kept apart)
  * probe_asan  : the same under ASan+UBSan, with any sanitizer line counted
  * engine      : what the UCI engine prints on BOTH streams when the net is offered
                  through NNUEArchFile, and whether `isready` still answers

Nothing here reads a net twice under a different name: the engine arm checks the
loudness of the refusal, the probe arm gets the loader's own message.

Usage: run_mutants.py <manifest.json> <probe dir> <forge exe> <out.json> [--asan]
"""
import json
import os
import re
import subprocess
import sys

SAN_PAT = re.compile(r"(AddressSanitizer|LeakSanitizer|runtime error:|SUMMARY: UndefinedBehaviorSanitizer)")


def run(argv, timeout=300, env=None):
    base = dict(os.environ)
    base.setdefault("ASAN_OPTIONS", "detect_leaks=0:abort_on_error=1")
    base.setdefault("UBSAN_OPTIONS", "print_stacktrace=1:halt_on_error=1")
    if env:
        base.update(env)
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=base)
        return proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        return None, exc.stdout or "", exc.stderr or "", True


def engine_arm(forge, path):
    """Offer the net to the engine. Read to readyok; never pipe quit into a search."""
    script = "uci\nisready\nsetoption name NNUEArchFile value %s\nisready\nquit\n" % path
    try:
        proc = subprocess.run([forge], input=script, capture_output=True, text=True, timeout=300)
        rc, out, err, timed = proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        rc, out, err, timed = None, exc.stdout or "", exc.stderr or "", True
    lines = [ln for ln in out.splitlines() if "NNUE v3" in ln or "ERROR" in ln]
    refused = any("info string NNUE v3:" in ln and "loaded v3" not in ln for ln in lines)
    accepted = any("loaded v3" in ln for ln in lines)
    return {
        "rc": rc,
        "timeout": timed,
        "stdout_lines": lines,
        "stderr": err.strip(),
        "stderr_nonempty": bool(err.strip()),
        "readyok_count": sum(1 for ln in out.splitlines() if ln == "readyok"),
        "refused": refused,
        "accepted": accepted,
    }


def probe_arm(probe, path):
    rc, out, err, timed = run([probe, "load", path], timeout=600)
    san = []
    for ln in (out + err).splitlines():
        if SAN_PAT.search(ln):
            san.append(ln.strip())
    verdict = "crash"
    detail = ""
    if timed:
        verdict = "timeout"
    elif rc == 0:
        verdict = "accept"
        for ln in out.splitlines():
            if ln.startswith("ACCEPTED\t"):
                detail = ln
    elif rc == 1 and not san:
        verdict = "refuse"
        for ln in out.splitlines():
            if ln.startswith("REFUSED\t"):
                detail = ln.split("\t", 1)[1]
    elif rc is not None and rc < 0:
        verdict = "signal"
    elif rc == 1 and san:
        verdict = "refuse_but_sanitizer"
    return {
        "rc": rc,
        "verdict": verdict,
        "detail": detail,
        "stdout_head": out.strip().splitlines()[:3],
        "stderr_head": err.strip().splitlines()[:6],
        "sanitizer_lines": san,
        "timeout": timed,
    }


def main():
    manifest = json.load(open(sys.argv[1]))
    probe_dir = sys.argv[2]
    forge = sys.argv[3]
    outpath = sys.argv[4]
    do_asan = "--asan" in sys.argv[5:]

    probe_rel = os.path.join(probe_dir, "loadprobe_rel")
    probe_asan = os.path.join(probe_dir, "loadprobe_asan")

    results = []
    for case in manifest["cases"]:
        path = os.path.join(manifest["outdir"], case["name"] + ".fnn3")
        row = dict(case)
        row["probe_rel"] = probe_arm(probe_rel, path)
        if do_asan:
            row["probe_asan"] = probe_arm(probe_asan, path)
        row["engine"] = engine_arm(forge, path)
        results.append(row)
        got = row["probe_rel"]["verdict"]
        san = len(row["probe_asan"]["sanitizer_lines"]) if do_asan else "-"
        print("%-26s %-8s want %-8s got %-8s san %-3s eng %s"
              % (case["name"], case["class"], case["expect"], got, san,
                 "accept" if row["engine"]["accepted"] else ("refuse" if row["engine"]["refused"] else "?")))

    with open(outpath, "w") as handle:
        json.dump({"manifest": manifest, "results": results}, handle, indent=1)
    print("wrote %s (%d cases)" % (outpath, len(results)))


if __name__ == "__main__":
    main()
