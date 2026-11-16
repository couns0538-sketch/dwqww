#!/usr/bin/env python3
"""S02 check of seat 11's S-F8: `setoption name <X> <word>` with the `value` keyword omitted is silently
swallowed, because the name-reading loop eats every token up to `value` and the word becomes part of the NAME.

Their claim has two halves, and I test both, because the second is what makes it a finding rather than a
quirk:
  (a) `setoption name UseNNUE false` prints NO line and changes nothing;
  (b) `setoption name UseNNUE value false` DOES change something (the net stops running), which is the
      control that proves the first case's silence means "ignored", not "accepted".

Independent harness, written from their sentence. I do not use `eval`'s `nnue` field as the only witness:
I also measure a node-count change on bench 13, which is a number the engine prints itself, and I assert
that the line I parse was actually found (seat 19's warning).

usage: check_s11f8.py <exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys


def run(exe, lines):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.run([exe], input="\n".join(lines) + "\n", capture_output=True, text=True, env=env)
    return p.stdout + p.stderr


def find(out, pattern, what):
    """Return the match, or die loudly. A missing line must never be read as a pass (seat 19's warning)."""
    m = re.search(pattern, out, re.MULTILINE)
    if not m:
        sys.exit("FAIL: expected line %r (%s) not found in the engine output. A silent parser is exactly the "
                 "bug this check must not repeat. Output was:\n%s" % (pattern, what, out[-800:]))
    return m


def eval_line(exe, setup):
    out = run(exe, ["uci", "isready"] + setup + ["position startpos", "eval", "quit"])
    m = find(out, r"^info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)", "eval line")
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), out


def bench_nodes(exe, setup, depth=13):
    out = run(exe, ["uci", "isready"] + setup + ["bench %d" % depth, "quit"])
    m = find(out, r"^info string bench depth %d nodes (\d+)" % depth, "bench line")
    return int(m.group(1)), out


def main():
    exe = sys.argv[1]
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    meta = {"exe": exe,
            "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
            "option_lines_sent": ["setoption name UseNNUE value false  (the correct form)",
                                  "setoption name UseNNUE false        (the `value` keyword omitted)",
                                  "setoption name Hash value 1 / setoption name Hash 1"],
            "position": "startpos for eval; bench 13 built in",
            "note": "every parsed line is asserted present; a missing line aborts the check"}
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)
    results = {}

    # ---- half (a): the omitted-`value` form, and the control that it should have mattered
    base = eval_line(exe, [])
    right = eval_line(exe, ["setoption name UseNNUE value false"])
    wrong = eval_line(exe, ["setoption name UseNNUE false"])
    results["eval_default"] = base[:3]
    results["eval_value_false"] = right[:3]
    results["eval_no_value_word"] = wrong[:3]
    open(os.path.join(outdir, "eval_raw.txt"), "w").write(
        "=== default (no setoption)\n%s\n=== setoption name UseNNUE value false\n%s\n"
        "=== setoption name UseNNUE false\n%s\n" % (base[3], right[3], wrong[3]))

    print("eval (hce, nnue, total):")
    print("  default                          %s" % (base[:3],))
    print("  `... UseNNUE value false`        %s   <- control: must differ in nnue" % (right[:3],))
    print("  `... UseNNUE false` (no `value`) %s   <- the finding: must equal the default" % (wrong[:3],))

    b0, _ = bench_nodes(exe, [])
    b1, _ = bench_nodes(exe, ["setoption name UseNNUE value false"])
    b2, _ = bench_nodes(exe, ["setoption name UseNNUE false"])
    results["bench13_default"] = b0
    results["bench13_value_false"] = b1
    results["bench13_no_value_word"] = b2
    print("bench 13 nodes:")
    print("  default %d ; `UseNNUE value false` %d ; `UseNNUE false` %d" % (b0, b1, b2))

    # ---- the other half: is the word swallowed INTO THE NAME?  A name that matches nothing is silent,
    #      a name that matches an option with a bad value answers. So:
    h_right, _ = bench_nodes(exe, ["setoption name Hash value 1"])
    h_wrong, _ = bench_nodes(exe, ["setoption name Hash 1"])
    # and the discriminating test: does the engine answer at all about the swallowed word?
    answer_out = run(exe, ["uci", "isready", "setoption name UseNNUE false", "isready", "quit"])
    answers = [l for l in answer_out.splitlines() if l.startswith("info string")]
    results["answer_lines_when_value_word_omitted"] = answers
    print("answer lines for `setoption name UseNNUE false`: %r %s"
          % (answers, "(SILENT — nothing said at all)" if not answers else ""))
    print("bench 13 nodes with Hash set the correct way: %d ; omitting `value`: %d" % (h_right, h_wrong))

    # ---- verdict, with every condition asserted rather than assumed
    checks = {
        "omitting `value` leaves the net running (eval nnue equals the default)": wrong[1] == base[1],
        "the correct form DOES stop the net (eval nnue differs from the default)": right[1] != base[1],
        "omitting `value` changes no bench node count (silently ignored)": b2 == b0,
        "the correct form DOES change the bench node count": b1 != b0,
        "omitting `value` prints no info string at all": len(answers) == 0,
    }
    print()
    print("### verdict checks")
    for name, ok in checks.items():
        print("- %-72s %s" % (name, "PASS" if ok else "FAIL"))
    json.dump({"results": results, "checks": checks}, open(os.path.join(outdir, "verdict.json"), "w"), indent=1)
    if not all(checks.values()):
        sys.exit("CONCLUSION: REFUTES S-F8 (at least one condition failed)")
    print()
    print("CONCLUSION: CONFIRMS S-F8 — `setoption name <X> <word>` with the `value` keyword omitted is "
          "silently swallowed and changes nothing, while the correct form changes the search.")


if __name__ == "__main__":
    main()
