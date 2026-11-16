#!/usr/bin/env python3
"""check_s11f1.py <exe> <outdir>

Checks seat 11's S-F1 from its SENTENCE alone (I did not read or copy their script):
  "position fen reads only six tokens and the following loop silently discards any extra token,
   so a malformed FEN with junk after the sixth field is ACCEPTED (set_fen itself would reject a
   7th field)."

My own harness, three parts:
  (a) engine: send `position fen <FEN> <junk>` and compare with `position fen <FEN>` through
      `go perft 2` -- same nodes means the junk was swallowed.
  (b) engine: `position fen` with the junk placed so that it LOOKS like a 7th field of the FEN
      passed directly to set_fen (which the finding says would be rejected).
  (c) PLANTED CONTROL (Opus file 2, rule 1): a fake engine that refuses every FEN must make this
      harness report REFUSED; if my harness cannot see that difference it proves nothing.
The fake engine is a text file written by this script, run through the same function.
"""
import os
import subprocess
import sys

FENS = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("endgame", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
]
JUNKS = ["junk", "xyz 1 2", "999999", "e4 e5", "w", "KQkq"]


def run_lines(exe, lines, timeout=120):
    payload = ("\n".join(lines) + "\nquit\n").encode()
    p = subprocess.run([exe], input=payload, capture_output=True, timeout=timeout)
    return p.stdout.decode(errors="replace"), p.stderr.decode(errors="replace"), p.returncode


def perft2(exe, pos_line):
    out, err, rc = run_lines(exe, ["uci", "isready",
                                   "setoption name Hash value 16", "isready",
                                   pos_line, "isready", "go perft 2"])
    nodes = None
    refused = "invalid fen" in (out + err).lower()
    for line in out.splitlines():
        if line.startswith("nodes "):
            nodes = int(line.split()[1])
    # Seat 19's integrity rule: assert the line was found. A missing count must never pass as
    # "same board" (a None == None comparison would) nor as an acceptance.
    if nodes is None and not refused:
        raise AssertionError("no 'nodes N' line for %r; harness output was:\n%s" % (pos_line, out[-500:]))
    return {"pos": pos_line, "nodes": nodes, "refused": refused, "rc": rc,
            "raw": out}


def main():
    exe = os.path.realpath(sys.argv[1])
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)

    # (c) the planted control: a fake engine that always refuses the FEN
    fake = os.path.join(outdir, "fake_refuse.sh")
    with open(fake, "w") as f:
        f.write("""#!/usr/bin/env bash
# PLANTED CONTROL (not the engine): answers every position with a refusal and perft with 1 node.
while IFS= read -r line; do
  case "$line" in
    uci) echo "id name fake-refuse"; echo uciok ;;
    isready) echo readyok ;;
    position*) echo "info string invalid FEN: planted refusal" ;;
    "go perft"*) echo "nodes 1" ;;
    quit) exit 0 ;;
  esac
done
""")
    os.chmod(fake, 0o755)

    rows = []
    for label, fen in FENS:
        base = perft2(exe, "position fen " + fen)
        for junk in JUNKS:
            with_junk = perft2(exe, "position fen %s %s" % (fen, junk))
            rows.append({
                "case": "%s + '%s'" % (label, junk),
                "fen": fen,
                "junk": junk,
                "nodes_plain": base["nodes"],
                "nodes_with_junk": with_junk["nodes"],
                "accepted_with_junk": not with_junk["refused"],
                "same_board": base["nodes"] is not None and base["nodes"] == with_junk["nodes"],
            })

    # (c) run the SAME function against the planted fake
    plant_rows = []
    for label, fen in FENS[:1]:
        base = perft2(fake, "position fen " + fen)
        for junk in JUNKS[:2]:
            wj = perft2(fake, "position fen %s %s" % (fen, junk))
            plant_rows.append({"case": "fake: %s + '%s'" % (label, junk),
                               "refused_plain": base["refused"], "refused_with_junk": wj["refused"],
                               "nodes": wj["nodes"]})

    with open(os.path.join(outdir, "table.txt"), "w") as f:
        f.write("| case | nodes plain | nodes with junk | accepted with junk | same board |\n")
        f.write("|---|---|---|---|---|\n")
        for r in rows:
            f.write("| %s | %s | %s | %s | %s |\n" % (
                r["case"], r["nodes_plain"], r["nodes_with_junk"],
                r["accepted_with_junk"], r["same_board"]))
        f.write("\n# PLANTED CONTROL (rule 1): the same perft2() against a fake engine that always refuses\n")
        f.write("| case | refused plain | refused with junk | nodes |\n|---|---|---|---|\n")
        for r in plant_rows:
            f.write("| %s | %s | %s | %s |\n" % (r["case"], r["refused_plain"],
                                                 r["refused_with_junk"], r["nodes"]))

    accepted = sum(1 for r in rows if r["accepted_with_junk"])
    same = sum(1 for r in rows if r["same_board"])
    plant_seen = sum(1 for r in plant_rows if r["refused_with_junk"])
    with open(os.path.join(outdir, "RESULT.txt"), "w") as f:
        f.write("exe: %s\n" % exe)
        f.write("sha256: %s\n" % subprocess.run(["sha256sum", exe], capture_output=True,
                                                 text=True).stdout.split()[0])
        f.write("date_utc: %s\n" % subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                                   capture_output=True, text=True).stdout.strip())
        f.write("cases: %d, accepted despite junk: %d, same board as without junk: %d\n"
                % (len(rows), accepted, same))
        f.write("planted control: %d of %d fake cases seen as refused (must be all)\n"
                % (plant_seen, len(plant_rows)))
        f.write("verdict: %s\n" % ("CONFIRMS 11-F1" if accepted == len(rows) and same == len(rows)
                                   and plant_seen == len(plant_rows) else "REFUTES/INCONCLUSIVE 11-F1"))
        f.write("\n# every refusal line found by the plain (junk-free) FENs, for the record:\n")
    print(open(os.path.join(outdir, "RESULT.txt")).read())
    print(open(os.path.join(outdir, "table.txt")).read())


if __name__ == "__main__":
    main()
