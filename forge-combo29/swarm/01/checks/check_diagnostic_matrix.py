#!/usr/bin/env python3
"""swarm seat 01: THE FOUR-CASE MATRIX for where the invalid-FEN diagnostic appears (S-C60).

A claim was relayed to me as: "a fresh session gives no diagnostic". My own record says otherwise — every invalid FEN I
tested was diagnosed — so rather than record either version second-hand, this measures the matrix directly.

Four combinations of the two things that could plausibly move the diagnostic:

  * **isready sent between `position` and `go`?** — a harness that respects the handshake vs one that fires immediately;
  * **a predecessor position set first, or a fresh session?** — S-C84's mechanism needs a predecessor, so if the
    diagnostic behaves differently with one that matters.

For each, record whether an `info string invalid FEN` appears and whether a bestmove is produced. The four cells are the
whole claim, so the matrix is the finding — not any single cell.

The CONTROL that makes the matrix non-vacuous: include a LEGAL FEN in the same four shapes. If the control never produces
a diagnostic, then the diagnostic's presence is a property of the invalid FEN and not of the handshake. Without that
control, "no diagnostic in case 1" would be indistinguishable from "the diagnostic never fires in this shape at all" —
which is exactly the vacuity S-F140/Trap 12 warns about.

Usage: check_diagnostic_matrix.py <exe> <outdir>
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

INVALID = "8/8/8/3kK3/8/8/8/8 w - - 0 1"          # adjacent kings: illegal
LEGAL = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"    # valid, rook mate-in-1


def run_case(exe, fen, with_isready, with_predecessor):
    """Return {diag: bool, bestmove: str|None, info_strings: [...]}."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")
    collected = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def pump(until_prefix, deadline_lines=400):
        seen = 0
        while seen < deadline_lines:
            line = p.stdout.readline()
            if not line:
                return None
            line = line.rstrip("\n")
            collected.append(line)
            seen += 1
            if line.startswith(until_prefix):
                return line
        return None

    send("uci")
    pump("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("isready")
    pump("readyok")
    send("ucinewgame")
    send("isready")
    pump("readyok")

    if with_predecessor:
        # a legal predecessor, fully resolved, so the engine has a position to fall back on
        send("position fen " + LEGAL)
        if with_isready:
            send("isready")
            pump("readyok")
        send("go depth 6")
        pump("bestmove")

    send("position fen " + fen)
    if with_isready:
        send("isready")
        pump("readyok")
    send("go depth 6")
    bm = pump("bestmove")

    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()

    # only the lines AFTER the last `position fen` belong to this case
    last_pos = max((i for i, l in enumerate(collected) if l.startswith("position fen")), default=-1)
    tail = collected[last_pos + 1:]
    return {
        "diag": any("invalid FEN" in l for l in tail),
        "info_strings": [l for l in tail if l.startswith("info string")],
        "bestmove": bm.split()[1] if bm and len(bm.split()) > 1 else None,
    }


def main():
    exe, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    L = ["THE FOUR-CASE MATRIX: where does the invalid-FEN diagnostic appear?",
         "exe: %s" % exe, "sha256: %s" % sha,
         "invalid FEN: %s" % INVALID,
         "control FEN: %s" % LEGAL, ""]
    L.append("case\tisready?\tpredecessor?\tINVALID: diag?\tINVALID: bestmove?\tCONTROL: diag?\tCONTROL: bestmove?")
    rows = []
    for with_isready in (False, True):
        for with_pred in (False, True):
            inv = run_case(exe, INVALID, with_isready, with_pred)
            ctl = run_case(exe, LEGAL, with_isready, with_pred)
            rows.append({"isready": with_isready, "predecessor": with_pred,
                         "invalid": inv, "control": ctl})
            L.append("%d\t%s\t%s\t%s\t%s\t%s\t%s" % (
                len(rows), "yes" if with_isready else "no", "yes" if with_pred else "no",
                "YES" if inv["diag"] else "no", inv["bestmove"],
                "yes" if ctl["diag"] else "NO", ctl["bestmove"]))
    L.append("")

    ctl_quiet = all(not r["control"]["diag"] for r in rows)
    inv_always = all(r["invalid"]["diag"] for r in rows)
    inv_never = all(not r["invalid"]["diag"] for r in rows)

    L.append("CONTROL CHECK: the legal FEN produced a diagnostic in %d of 4 cases."
             % sum(1 for r in rows if r["control"]["diag"]))
    if not ctl_quiet:
        L.append("  CONTROL FAILED - the legal FEN also draws a diagnostic, so this matrix cannot attribute the")
        L.append("  diagnostic to the FEN's legality. Reported as measured; do not read the cells above as a result.")
    L.append("")
    if inv_always and ctl_quiet:
        L.append("VERDICT: the diagnostic appears in ALL FOUR cases, and never for the legal control. So it is a")
        L.append("  property of the INVALID FEN, and NEITHER the isready handshake NOR a predecessor changes it.")
        L.append("  That makes the absolute 'a fresh session gives no diagnostic' untenable: a fresh session with no")
        L.append("  isready is case 1, and it diagnoses.")
    elif inv_never:
        L.append("VERDICT: the diagnostic never appears - contradicts my own earlier tests, which all showed it.")
        L.append("  Reported as measured; the discrepancy needs resolving before either version is relied on.")
    else:
        L.append("VERDICT: the diagnostic is CONDITIONAL - see which cells lack it. This is the case where the")
        L.append("  matrix is essential: a single-cell test would have generalised wrongly in either direction.")

    (out / "check_diagnostic_matrix.json").write_text(json.dumps({"sha": sha, "rows": rows}, indent=1))
    txt = "\n".join(L) + "\n"
    (out / "check_diagnostic_matrix.txt").write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
