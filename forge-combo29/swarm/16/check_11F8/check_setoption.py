#!/usr/bin/env python3
"""check_setoption.py EXE OUT.txt : independent check of seat 11's S-F8 (and seat 02's S-C2 partial refutation).

Claim under test (seat 11 S-F8): "`setoption` with the value word omitted is accepted SILENTLY and changes NOTHING".
Seat 02 partly refuted it: the MECHANISM is right (the token loop eats `false` into the option NAME, so the name is
unknown and the option is not applied), but it is NOT silent — `info string unknown option UseNNUE false` is printed.

This runs the four combinations on the given build and asserts what actually comes out:
  no value word     -> an unknown-option line, and eval's nnue is the DEFAULT (20), i.e. not applied
  with value word   -> no unknown-option line, and eval's nnue is 0, i.e. applied
Missing line or wrong value fails loudly (no silent skip).
"""
import re
import subprocess
import sys
import time

EXE, OUT = sys.argv[1], sys.argv[2]


class Missing(Exception):
    pass


def run(script, want_eval=True):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write(script)
    p.stdin.flush()
    lines = []
    dl = time.monotonic() + 60
    while time.monotonic() < dl:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.strip() == "readyok" and want_eval is False:
            break
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return lines


results = []
for label, setopt in (("no value word", "setoption name UseNNUE false"),
                      ("with value word", "setoption name UseNNUE value false")):
    script = f"uci\nisready\n{setopt}\nisready\neval\nisready\nquit\n"
    lines = run(script)
    unknown = [l for l in lines if "unknown option" in l.lower()]
    ev = [l for l in lines if l.startswith("info string eval")]
    if not ev:
        raise Missing(f"{label}: no eval line (cannot judge whether the option was applied)")
    m = re.search(r"nnue (-?\d+)", ev[-1])
    if not m:
        raise Missing(f"{label}: eval line unparsed: {ev[-1]}")
    nnue = int(m.group(1))
    results.append((label, bool(unknown), unknown[:1], nnue, ev[-1]))

lines_out = [f"exe {EXE}", ""]
for label, had_unknown, unk, nnue, ev in results:
    lines_out.append(f"{label:16s} unknown-option line: {str(had_unknown):5s} {unk[0] if unk else ''}")
    lines_out.append(f"{'':16s} {ev}")
lines_out.append("")

ok = True
# seat 02's finding: the no-value form is NOT silent on either build
if not results[0][1]:
    lines_out.append("DISAGREES with seat 02 S-C2: the no-value form printed NO unknown-option line on this build.")
    ok = False
else:
    lines_out.append("AGREES with seat 02 S-C2: the no-value form prints an unknown-option line (not silent).")
# and it is not applied
if results[0][3] != 20:
    lines_out.append(f"UNEXPECTED: no-value form changed nnue to {results[0][3]} (expected the default 20).")
    ok = False
else:
    lines_out.append("AGREES with seat 11 S-F8's mechanism: the no-value form is NOT APPLIED (nnue stays at the default 20).")
# and the value form works
if results[1][3] != 0 or results[1][1]:
    lines_out.append(f"UNEXPECTED: with the value word nnue={results[1][3]} unknown_line={results[1][1]} (expected 0 and no line).")
    ok = False
else:
    lines_out.append("with the value word the option IS applied (nnue 0) and no unknown-option line appears.")

text = "\n".join(lines_out) + "\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)
sys.exit(0 if ok else 1)
