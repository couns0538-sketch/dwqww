#!/usr/bin/env python3
"""R3-4 planted-bug check: every mutant (one replacement in a fresh copy) must make tools/spsa/test_opus_spsa.py fail;
the clean copy must pass. Copies tools/spsa plus the two engine files the tests read (search_tune.hpp, tune.inc).
Never deletes anything: every run goes to a new directory.

usage: r3_4_mutation_check.py <repo root> <new output dir>
"""
import os
import shutil
import subprocess
import sys

M = [  # (id, file relative to the repo, old text, new text, what it breaks)
    ("M01", "tools/spsa/opus_spsa_core.py", "clamp(theta[p.name] + q.a_k / q.c_k * w_minus_l * q.delta",
     "clamp(theta[p.name] - q.a_k / q.c_k * w_minus_l * q.delta", "update sign"),
    ("M02", "tools/spsa/opus_spsa_core.py", "c = p.c_end * self.iterations ** self.gamma",
     "c = p.c_end * self.iterations ** self.alpha", "c uses alpha"),
    ("M03", "tools/spsa/opus_spsa_core.py", "return a / (self.A + k + 1) ** self.alpha",
     "return a / (self.A + k + 2) ** self.alpha", "a_k off by one"),
    ("M04", "tools/spsa/opus_spsa_core.py", "minus = int(clamp(round_value(t - c_k * delta",
     "minus = int(clamp(round_value(t + c_k * delta", "theta- = theta+"),
    ("M05", "tools/spsa/opus_spsa_core.py", "return math.floor(x + rng.random())",
     "return math.floor(x + 0.5 * rng.random())", "biased randomized rounding"),
    ("M06", "tools/spsa/opus_spsa_core.py", 'return random.Random(f"opus_spsa:{seed}:{k}")',
     "return random.Random()", "unseeded iteration RNG (resume differs)"),
    ("M07", "tools/spsa/opus_spsa_core.py",
     "if sum(i * n for i, n in enumerate(result.ptnml)) != 2 * result.wins + result.draws:", "if False:",
     "no pentanomial / W-L-D consistency check"),
    ("M08", "tools/spsa/opus_spsa_fastchess.py", "if by_lines != (wins, losses, draws):", "if False:",
     "no cross-check of W/L/D with the Finished lines"),
    ("M09", "tools/spsa/opus_spsa_fastchess.py", "pair_counts[points[2 * j - 1] + points[2 * j]] += 1",
     "pair_counts[points[j] + points[min(j + 1, pairs)]] += 1", "wrong game pairing"),
    ("M10", "tools/spsa/opus_spsa_fastchess.py", "job = _new_job(priority)", "job = None",
     "no job object: timeout kills fastchess only"),
    ("M11", "tools/spsa/opus_spsa.py",
     '            append_csv(os.path.join(workdir, "spsa_log.csv"), params, record)\n        log(f"resume',
     '            pass\n        log(f"resume', "no CSV repair on resume"),
    ("M12", "tools/spsa/opus_spsa.py",
     '"params": [[p.name, p.start, p.minimum, p.maximum, p.c_end, p.r_end] for p in params],',
     '"params": [p.name for p in params],', "fingerprint ignores c_end"),
    ("M13", "tools/spsa/opus_spsa.py", 'if cfg["rounding"] == "deterministic" and p.c_end < 0.5:', "if False:",
     "no c_end check for deterministic rounding"),
    ("M14", "tools/spsa/opus_spsa.py", "        state = core.advance_state(state, new_theta, result, record)\n",
     "        state = core.advance_state(state, theta, result, record)\n", "theta never updated"),
    ("M15", "src/search/tune.inc", "int NullMoveMarginBase = 180;", "int NullMoveMarginBase = 181;",
     "engine default differs from the config"),
    ("M16", "include/forge/search_tune.hpp", '"SeeQuietMultiplier", "SeeNoisyMultiplier",',
     '"SeeQuietMultiplier", "QsSeeMargin",', "advertised list differs from the config"),
]
COPY = ["tools/spsa", "include/forge/search_tune.hpp", "src/search/tune.inc"]


def make_tree(repo, dest):
    for rel in COPY:
        src, dst = os.path.join(repo, rel), os.path.join(dest, rel)
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def run_tests(tree, root):
    p = subprocess.run([sys.executable, "-I", "-B", os.path.join(tree, "tools", "spsa", "test_opus_spsa.py"),
                        "--root", root], capture_output=True, text=True, timeout=900)
    failed = sorted({line.split(" ")[1] for line in p.stderr.splitlines()
                     if line.startswith(("FAIL: ", "ERROR: ")) and " (" in line})
    return p.returncode, failed, p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ""


def main():
    repo, out = sys.argv[1], sys.argv[2]
    os.makedirs(out)  # must be new
    clean = os.path.join(out, "clean")
    make_tree(repo, clean)
    clean_rc, failed, last = run_tests(clean, os.path.join(out, "clean_root"))
    print(f"clean copy: rc {clean_rc} {last}", flush=True)
    ok = clean_rc == 0
    caught = 0
    for mid, rel, old, new, what in M:
        tree = os.path.join(out, mid)
        make_tree(repo, tree)
        path = os.path.join(tree, rel)
        with open(path, "rb") as f:
            text = f.read().decode("utf-8")
        if text.count(old) != 1:
            print(f"{mid} pattern occurs {text.count(old)} times in {rel}: BROKEN MUTANT", flush=True)
            ok = False
            continue
        with open(path, "wb") as f:
            f.write(text.replace(old, new).encode("utf-8"))
        rc, failed, last = run_tests(tree, os.path.join(out, mid + "_root"))
        hit = rc != 0
        caught += hit
        print(f"{mid} {what:<45} {'CAUGHT' if hit else 'SURVIVED'} ({last}) by {', '.join(failed) or '-'}",
              flush=True)
        ok &= hit
    print(f"{caught}/{len(M)} mutants caught; clean copy {'passes' if clean_rc == 0 else 'FAILS'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
