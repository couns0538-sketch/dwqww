#!/usr/bin/env python3
"""accept_all.py EXE FENFILE OUTDIR LABEL

Sends every FEN in FENFILE through the engine and counts refusals.
Purpose: measure whether the parser's strictness bites on REAL positions (from played
games) or only on malformed input.

Attribution is exact: for the k-th FEN the engine emits either
   `info string invalid FEN: ...` followed by `readyok`, or just `readyok`,
so the lines between consecutive readyoks belong to consecutive FENs, in order. A batch
that does not produce exactly len(chunk) readyoks is re-run FEN by FEN and that is
recorded as a batch fault (never silently trusted).

python-chess is asked about each FEN too, so "refused by Forge, accepted by python-chess"
is separated from "refused by both".
"""
import os
import subprocess
import sys

import chess

BATCH = 500


def eng(exe, lines, timeout=900):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    return subprocess.run([exe], input="\n".join(lines) + "\n", text=True,
                          capture_output=True, timeout=timeout, env=env)


def main():
    exe, fenfile, outdir, label = sys.argv[1:5]
    os.makedirs(outdir, exist_ok=True)
    fens = [ln.strip() for ln in open(fenfile) if ln.strip()]

    segments = []
    batch_faults = 0
    idx = 0
    batch = 0
    while idx < len(fens):
        chunk = fens[idx:idx + BATCH]
        lines = ["uci", "isready"]
        for f in chunk:
            lines += ["position fen " + f, "isready"]
        lines.append("quit")
        p = eng(exe, lines)
        with open(os.path.join(outdir, "%s_raw_%03d.txt" % (label, batch)), "w") as fh:
            fh.write("=== exe: %s\n=== batch %d, %d FENs\n" % (os.path.abspath(exe), batch, len(chunk)))
            fh.write("=== the FENs of this batch, in order:\n")
            for i, f in enumerate(chunk):
                fh.write("%d\t%s\n" % (idx + i, f))
            fh.write("=== stdout:\n" + p.stdout + "\n=== stderr:\n" + p.stderr)
            fh.write("=== returncode: %d\n" % p.returncode)
        # split on readyok
        cur = []
        got = []
        for ln in p.stdout.splitlines():
            if ln == "readyok":
                got.append(cur)
                cur = []
            else:
                cur.append(ln)
        # the first readyok answers the initial `isready`
        got = got[1:]
        if len(got) != len(chunk):
            batch_faults += 1
            for f in chunk:
                single = eng(exe, ["isready", "position fen " + f, "isready"], timeout=120)
                segs = []
                c = []
                for ln in single.stdout.splitlines():
                    if ln == "readyok":
                        segs.append(c)
                        c = []
                    else:
                        c.append(ln)
                segs = segs[1:]
                segments.append(segs[0] if segs else ["<no readyok>"])
        else:
            segments.extend(got)
        idx += len(chunk)
        batch += 1

    results = []
    for f, seg in zip(fens, segments):
        refused = any("invalid FEN" in ln for ln in seg)
        try:
            chess.Board(f)
            py = True
        except Exception:
            py = False
        results.append((f, refused, py))

    n_ref = sum(1 for _, r, _ in results if r)
    forge_only = [(f, py) for f, r, py in results if r and py]
    py_only = [(f, py) for f, r, py in results if not r and not py]
    with open(os.path.join(outdir, "%s_summary.md" % label), "w") as fh:
        fh.write("file: %s, %d FENs, batch faults (re-run singly): %d\n\n" % (fenfile, len(results), batch_faults))
        fh.write("| measure | count |\n|---|---|\n")
        fh.write("| refused by Forge | %d |\n" % n_ref)
        fh.write("| refused by Forge but ACCEPTED by python-chess | %d |\n" % len(forge_only))
        fh.write("| accepted by Forge but refused by python-chess | %d |\n" % len(py_only))
        fh.write("\nrefused FENs (all of them):\n")
        for f, r, py in results:
            if r:
                fh.write("- `%s`  python-chess accepts: %s\n" % (f, py))
    print(open(os.path.join(outdir, "%s_summary.md" % label)).read())


if __name__ == "__main__":
    main()
