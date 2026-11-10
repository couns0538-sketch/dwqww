"""coverage.py - does the corpus execute the changed lines of each candidate? (job 3, standard library only)

The job forbids mutated engines, so sensitivity is shown another way: every candidate tree is also built as a
coverage probe (scripts\\build_aux.ps1 -Tag X -Coverage: the unchanged source with clang's source-based
coverage). This tool runs that probe on corpus chunks, on the edge-suite path and on the WITNESS_NOPIN targets,
merges the profiles and reports the execution count of every instrumented line inside an `#if FORGE_SPD_<switch>`
region of the candidate's tree. A line that is never executed is listed, not hidden.

  python -I -B coverage.py TAG...      (EVL PCM CKL WNP KPC BUN)
Receipts: out\\job3\\runs\\coverage\\<TAG>.json. Coverage probes are never used for a comparison.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fuzz  # noqa: E402
import pinguard3  # noqa: E402

OUT = fuzz.OUT
LLVM = r"C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin"      # read and execute only
SWITCHES = {"EVL": ["FORGE_SPD_EVADE_LEGAL"], "PCM": ["FORGE_SPD_PAWN_CAPMASK"], "CKL": ["FORGE_SPD_CHECKERS_KL"],
            "WNP": ["FORGE_SPD_WITNESS_NOPIN"], "KPC": ["FORGE_SPD_KING_PAWN_CACHE"],
            "BUN": ["FORGE_SPD_EVADE_LEGAL", "FORGE_SPD_PAWN_CAPMASK", "FORGE_SPD_CHECKERS_KL"]}
FILES = ["src/board.cpp", "src/eval.cpp", "include/forge/eval.hpp"]


def switch_regions(path, switches):
    """[(switch, first line, last line)]: the text between an #if / #elif that names a candidate switch and the
    matching #else / #elif / #endif. The #else part is the lock's text and is not compiled when the switch is on."""
    regions, stack = [], []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("#if"):
            sw = None if s.startswith("#ifndef") else next((x for x in switches if x in s), None)
            stack.append([sw, i, sw is not None])
        elif s.startswith("#elif") and stack:
            top = stack[-1]
            if top[2]:
                regions.append((top[0], top[1] + 1, i - 1))
            sw = next((x for x in switches if x in s), None)
            top[0], top[1], top[2] = sw or top[0], i, sw is not None
        elif s.startswith("#else") and stack:
            top = stack[-1]
            if top[2]:
                regions.append((top[0], top[1] + 1, i - 1))
            top[2] = False
        elif s.startswith("#endif") and stack:
            top = stack.pop()
            if top[2]:
                regions.append((top[0], top[1] + 1, i - 1))
    return regions, lines


def run_cov(probe, data, profile_dir):
    env = dict(os.environ)
    env["LLVM_PROFILE_FILE"] = os.path.join(profile_dir, "cov_%p.profraw")
    proc = subprocess.Popen([probe, "run"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env)
    pinguard3.check_child(proc._handle)
    _, err = proc.communicate(data)
    return proc.returncode, err.decode("ascii", "replace").strip().splitlines()[-1:]


def inputs():
    """(label, path bytes) of what the coverage probes run."""
    out = []
    for name, chunk in (("v1", 0), ("v2", 100)):
        if os.path.exists(fuzz.seeds_path(name)):
            path, _ = fuzz.gen_chunk(name, chunk)
            out.append((f"fuzz chunk {chunk} of seeds {name} (100,000 positions)", path))
    try:
        import edge
        suite, exp = edge.load_suite()
        legal = [e for e in suite if e["class"] == "LEGAL"]
        path, _ = edge.tier_a_path(legal, exp)
        out.append((f"edge suite, {len(legal)} legal entries and their children", path))
    except Exception as e:  # noqa: BLE001
        print(f"edge suite path not available: {e}")
    targets = os.path.join(fuzz.PACK, "suite", "wnp_targets.tsv")
    if os.path.exists(targets):
        fens = [ln.split("\t")[1] for ln in open(targets, "r", encoding="ascii").read().splitlines()[1:] if ln]
        out.append((f"WITNESS_NOPIN targets, {len(fens)} positions", "".join(f"P {i} X0 0 {f}\nM\n" for i, f in enumerate(fens)).encode("ascii")))
    return out


def main(argv):
    tags = argv[1:]
    if not tags:
        print(__doc__)
        return 1
    pinguard3.ensure()
    fuzz.guard()
    feeds = inputs()
    rdir = os.path.join(OUT, "runs", "coverage")
    os.makedirs(rdir, exist_ok=True)
    code = 0
    for tag in tags:
        pdir = os.path.join(OUT, "aux2", tag + "_cov")
        probe = os.path.join(pdir, "mgprobe.exe")
        tree = os.path.join(OUT, "src", tag)
        if not os.path.exists(probe):
            print(f"{tag}: no coverage probe ({probe}); build it with build_aux.ps1 -Tag {tag} -Coverage")
            code = 2
            continue
        for name in os.listdir(pdir):
            if name.endswith(".profraw") or name.endswith(".profdata"):
                os.remove(os.path.join(pdir, name))
        ran = []
        for label, data in feeds:
            rc, tail = run_cov(probe, data, pdir)
            ran.append({"input": label, "exit": rc, "probe_said": tail})
        raws = [os.path.join(pdir, n) for n in os.listdir(pdir) if n.endswith(".profraw")]
        profdata = os.path.join(pdir, "cov.profdata")
        subprocess.run([os.path.join(LLVM, "llvm-profdata.exe"), "merge", "-o", profdata] + raws, check=True)
        sources = [os.path.join(tree, f.replace("/", os.sep)) for f in FILES]
        lcov = subprocess.run([os.path.join(LLVM, "llvm-cov.exe"), "export", probe, f"-instr-profile={profdata}", "-format=lcov"] + sources,
                              capture_output=True, check=True).stdout.decode("utf-8", "replace")
        counts, current = {}, None
        for ln in lcov.splitlines():
            if ln.startswith("SF:"):
                current = os.path.normcase(os.path.normpath(ln[3:]))
                counts[current] = {}
            elif ln.startswith("DA:") and current is not None:
                a, b = ln[3:].split(",")[:2]
                counts[current][int(a)] = int(b)
        report = {"check": "coverage", "tag": tag, "probe": probe, "probe_sha256": fuzz.sha256_file(probe), "inputs": ran, "switches": {},
                  "note": "execution counts of the lines inside the candidate's #if regions, from a coverage build of the unchanged source; "
                          "the coverage probe is not used for any comparison", "when": fuzz.now()}
        for src in sources:
            regions, lines = switch_regions(src, SWITCHES[tag])
            per_file = counts.get(os.path.normcase(os.path.normpath(src)), {})
            for sw, a, b in regions:
                rows = [{"file": os.path.relpath(src, tree).replace(os.sep, "/"), "line": n, "count": per_file[n], "text": lines[n - 1].strip()[:110]}
                        for n in range(a, b + 1) if n in per_file]
                entry = report["switches"].setdefault(sw, {"lines": []})
                entry["lines"] += rows
        ok = True
        for sw, entry in report["switches"].items():
            rows = entry["lines"]
            entry["instrumented_lines"] = len(rows)
            entry["executed_lines"] = sum(1 for r in rows if r["count"] > 0)
            entry["never_executed"] = [f"{r['file']}:{r['line']}: {r['text']}" for r in rows if r["count"] == 0]
            entry["max_count"] = max((r["count"] for r in rows), default=0)
            if not rows or entry["executed_lines"] == 0:
                ok = False
            print(f"coverage {tag} {sw}: {entry['executed_lines']} of {entry['instrumented_lines']} instrumented lines executed, "
                  f"highest count {entry['max_count']:,}; never executed: {len(entry['never_executed'])}", flush=True)
            for r in entry["never_executed"]:
                print("    never executed: " + r)
        missing = [s for s in SWITCHES[tag] if s not in report["switches"]]
        if missing:
            ok = False
            print(f"coverage {tag}: no #if region found for {missing}")
        report["status"] = "REACHED" if ok else "NOT SHOWN"
        with open(os.path.join(rdir, tag + ".json"), "w", encoding="ascii", errors="replace", newline="\n") as f:
            json.dump(report, f, indent=1)
        for name in raws:
            os.remove(name)
        if not ok:
            code = 3
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
