"""End-to-end consistency audit: every headline number in FINDINGS.md and
SEARCHMOVES_TABLE.md must appear in the evidence file it cites.

The documents were edited several times AFTER their numbers were produced, which is
exactly when a stale number survives.  This walks a hard-coded list of
(claim, number-as-written, evidence-file, must-appear-as) and checks the string is
present.  It is deliberately literal and dumb: a substring check that a human
reading the doc can also run by eye.

A claim is only listed here if a reader could grep for it.  Numbers that are
derived in prose (percentages, intervals) are checked via a form that appears
verbatim in the file.

Run: python3 audit_doc_numbers.py
Writes audit_doc_numbers.txt   -- exits non-zero on any mismatch.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# (document, claim label, evidence file, strings that must be present)
CHECKS = [
    ("FINDINGS F1", "causal split four arms", "job1/causal_split.txt",
     ["base_all  | 49/60 | 1/60", "pA_all    | 60/60 | 60/60",
      "pB_all    | 51/60 | 7/60", "pAB_all   | 60/60 | 60/60"]),
    ("FINDINGS F2", "order vs search", "job1/order_vs_search.txt",
     ["bestmove changed: 22/120", "of the 22 changes, score UNCHANGED: 0/22",
      "of the 22 changes, |delta| >= 10 cp: 18/22"]),
    ("FINDINGS F3", "proven-tie change counts", "job1/ties.txt",
     ["ties2   d 8: bestmove changed 1/20", "ties3   d12: bestmove changed 1/20",
      "ties5   d 8: bestmove changed 0/12"]),
    ("FINDINGS F4", "pinned vs intree", "job1/pinned_vs_intree.txt",
     ["(move, position) pairs measured: 265", "identical                                  : 10/265",
      "|delta| >= 10 cp                           : 211/265",
      "|delta| >= 50 cp                           : 50/265", "sd 44.2"]),
    ("FINDINGS F5", "pin count table", "job2/pin_count.txt",
     ["   1 | 60 | 60/60 | 1/60 | 48/60 | 28", " all | 60 | 49/60 | 1/60 | 46/60 | 26"]),
    ("FINDINGS F6", "rank order R1/R3", "job3/rank_final.txt",
     ["R1 | 3 | 159 | 139/159", "R1 | 5 | 530 | 475/530",
      "R3 | 3 | 159 | 142/159", "R3 | 5 | 530 | 486/530",
      "determinism, same command twice, bestmove+score identical : 60/60",
      "R1 (unrestricted MultiPV) rank-1 == plain bestmove+score  : 53/60"]),
    ("FINDINGS F6a", "depth 10 cross-check", "job3/rank_final_depth10.txt",
     ["R1 | 3 | 144 | 136/144", "R3 | 3 | 144 | 134/144", "R3 | 5 | 480 | 434/480"]),
    ("FINDINGS F6b", "verifier operation", "job3/verifier_operation.txt",
     ["positions: 60", "pin arm's winner == plain bestmove                    : 49/60",
      "positions where some other candidate beat the best move: 11/60"]),
    ("FINDINGS F7", "gap sweep", "job3/rank_why.txt",
     [" 100 | 317 | 313/317 | 0.987", "  10 | 511 | 478/511 | 0.935",
      "median ratio 1.003"]),
    ("FINDINGS F8", "degenerate matrix", "job4/degenerate.txt",
     ["== CONTROLS ==", "startpos C1 harness sees a restriction (E0 != E5): 1",
      "startpos C2 argument order irrelevant (E3 == E4): 1"]),
    ("FINDINGS F9", "zero-move meanings", "job4/zero_move_meaning.txt",
     ["| checkmate | yes |", "| stalemate | yes |"]),
    ("FINDINGS F11", "planted faults", "selftest_falsify.txt",
     ["ALL PLANTED FAULTS HANDLED: True"]),
    ("FINDINGS F12", "fix vs pinned score", "job1/fix_vs_pinned_score.txt",
     ["identical  10/265", "identical   9/265"]),
    ("FINDINGS F12a", "subgroup significance", "job1/fix_significance.txt",
     ["exact McNemar two-sided p = 0.0625"]),
    ("FINDINGS F12b", "patch A ranking, paired", "job3/patchA_ranking.txt",
     ["positions validated in BOTH (used for the pairing)   : 51",
      "3 | 122 | 110/122 | 112/122", "5 | 386 | 367/386 | 367/386",
      "3 | 122 | 110/122 | 115/122", "5 | 386 | 366/386 | 368/386"]),
    ("FINDINGS F13", "tag regression test", "job3/test_tag_no_overwrite.txt",
     ["ALL: True"]),
    ("FINDINGS F10", "FEN diagnostic placement", "job4/diagnostic_placement.txt",
     ["A1 position has 'invalid FEN': True", "A1 go output  has 'invalid FEN': False"]),
]


def negative_control():
    """Prove this audit can fail.

    Bug this guards, found by trying it the first time: the planting step used a
    string replace whose target did not match, so nothing was planted, the audit
    then passed, and the "control" looked green.  A control that silently does
    nothing is worse than no control.  So the planting asserts the target exists
    AND that the mutated text differs before anything is run.
    """
    src = open(os.path.abspath(__file__)).read()
    target = '"R3 | 3 | 159 | 142/159"'
    if target not in src:
        return False, f"negative control could not plant: target {target} not in source"
    mutated = src.replace(target, '"R3 | 3 | 159 | 199/159"')
    if mutated == src:
        return False, "negative control could not plant: replacement changed nothing"

    tmp = os.path.join(HERE, "_audit_neg_tmp.py")
    with open(tmp, "w") as fh:
        fh.write(mutated)
    try:
        proc = subprocess.run([sys.executable, tmp], cwd=HERE,
                              capture_output=True, text=True, timeout=120)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    # The planted run must FAIL (non-zero) and must name the planted string.
    ok = proc.returncode != 0 and "199/159" in (proc.stdout + proc.stderr)
    return ok, (f"planted run exit {proc.returncode} "
                f"(expected non-zero), names planted value: {'199/159' in (proc.stdout + proc.stderr)}")


def main():
    out = ["# doc-number audit", ""]
    failures = 0
    for doc, label, rel, needles in CHECKS:
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            out.append(f"MISSING FILE {rel}  ({doc}: {label})")
            failures += 1
            continue
        with open(path, errors="replace") as fh:
            body = fh.read()
        bad = [n for n in needles if n not in body]
        if bad:
            failures += 1
            out.append(f"FAIL {doc} [{label}] <- {rel}")
            for n in bad:
                out.append(f"      missing: {n!r}")
        else:
            out.append(f"ok   {doc:16s} [{label}] <- {rel}  ({len(needles)} strings)")

    nc_ok, nc_detail = negative_control()
    if not nc_ok:
        failures += 1

    out += ["", "== NEGATIVE CONTROL ==",
            "a planted wrong number must make this audit exit non-zero",
            f"negative control passed: {nc_ok}",
            f"detail: {nc_detail}",
            "",
            "== RESULT ==",
            f"groups checked: {len(CHECKS)}",
            f"groups failing: {failures}",
            f"ALL DOC NUMBERS TRACEABLE: {failures == 0}"]
    text = "\n".join(out)
    with open(os.path.join(HERE, "audit_doc_numbers.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
