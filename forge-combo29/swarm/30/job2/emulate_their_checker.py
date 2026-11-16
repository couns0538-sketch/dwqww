#!/usr/bin/env python3
"""emulate_their_checker.py -- counts how many bestmoves deepseek6's OWN legality check in
fuzzuci56.py actually examines, without running the engine at all.

Their check (fuzzuci56.py, lines 96-125) is:
    best = last bestmove in the output;  pos_line = last 'position' line in the output
    if best and best != '0000' and pos_line:
        b = chess.Board(lastpos ...)          # lastpos = the last 'position' line SENT
        ...
        except ValueError: pass               # silently skipped
Their `lastpos` is assigned from the SENT lines (line 75), and `pos_line` from the
ENGINE'S OUTPUT (line 102). The engine never prints a line starting with "position"
(checked: `grep -rn 'cout << \"position' src/*.cpp` is empty), so pos_line stays None
and the whole block is skipped for every sequence. That is the claim; this script
measures it by re-implementing their block exactly and counting.

It also counts the second defect: chess.Board("position startpos ...") cannot parse, so
even if pos_line were set, the ValueError branch would swallow it.

usage: emulate_their_checker.py SEQFILE [--verbose]
"""
import json
import sys

import chess


def their_checker(lastpos, output_lines):
    """Exactly their lines 96-125, with `out` = the engine's output lines."""
    best = None
    pos_line = None
    for l in output_lines:
        if l.startswith("position"):
            pos_line = l
        if l.startswith("bestmove"):
            best = l.split()[1]
    if best and best != "0000" and pos_line:
        try:
            b = chess.Board(lastpos if "moves" in lastpos or "fen" in lastpos
                            else chess.STARTING_FEN)
            if " moves " in lastpos:
                parts = lastpos.split(" moves ", 1)
                b = chess.Board(parts[0].replace("position fen ", "").strip()
                                or chess.STARTING_FEN)
                for mv in parts[1].split():
                    try:
                        mm = chess.Move.from_uci(mv)
                    except Exception:
                        break
                    if mm not in b.legal_moves:
                        break
                    b.push(mm)
            legal = any(m.uci() == best for m in b.legal_moves)
            if not legal:
                return "ILLEGAL"
            return "OK"
        except ValueError:
            return "SKIPPED_VALUEERROR"
    return "NOT_ENTERED"


def main():
    seqfile = sys.argv[1]
    verbose = "--verbose" in sys.argv
    seqs, cur = [], None
    for line in open(seqfile):
        line = line.rstrip("\n")
        if line.startswith("### seq "):
            cur = []
            seqs.append(cur)
        elif cur is not None:
            cur.append(line)

    counts = {"NOT_ENTERED": 0, "SKIPPED_VALUEERROR": 0, "OK": 0, "ILLEGAL": 0}
    examples = []
    for i, lines in enumerate(seqs):
        # the engine's output, reconstructed: the engine prints ONLY these line kinds
        # (grep over src/ for every std::cout << "..." literal that could start a line);
        # the important part is that it never echoes a command back.
        out = []
        for l in lines:
            s = l.strip()
            if s.startswith("go") or s == "isready":
                out.append("bestmove a2a3")      # the only line shape that matters here
        lastpos = None
        for l in lines:
            if l.startswith("position"):
                lastpos = l
        if lastpos is None:
            lastpos = ""
        res = their_checker(lastpos, out)
        counts[res] += 1
        if res != "NOT_ENTERED" and len(examples) < 5:
            examples.append({"seq": i, "result": res, "lastpos": lastpos})

    total = len(seqs)
    verdict = {
        "sequences": total,
        "their_check_outcomes": counts,
        "sequences_whose_bestmove_was_actually_examined": counts["OK"] + counts["ILLEGAL"],
        "verdict": ("their ZERO illegal bestmoves is VACUOUS: the check never ran"
                    if counts["OK"] + counts["ILLEGAL"] == 0 else
                    "their check ran for some sequences"),
        "why": ("pos_line is read from the ENGINE'S OUTPUT, and the engine never prints a "
                "line starting with 'position'; also chess.Board() cannot parse a "
                "'position ...' string, so the ValueError branch would swallow it too"),
        "examples": examples,
    }
    print(json.dumps(verdict, indent=1))
    if verbose:
        print("first sequence, as sent:", json.dumps(seqs[0]))


if __name__ == "__main__":
    main()
