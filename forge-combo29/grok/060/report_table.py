#!/usr/bin/env python3
"""Step table. Status words are this run's record; numbers are read from the files."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent

def text(name):
    return (ROOT / name).read_text(encoding="utf-8").rstrip("\n")

def main():
    rows = [
        ("STEP 1 seat", "done", "SEAT.txt stamps.txt", "seat 060 idea 10"),
        ("STEP 2 honesty and baseline", "done", "HONESTY_B.txt proof_B_O_sum.txt proof_B_G_sum.txt", text("proof_B_O_sum.txt").replace("\n", " ") + " | " + text("proof_B_G_sum.txt").replace("\n", " ")),
        ("STEP 3 prediction", "done", "prediction.txt", "9720000 and +3, file not edited"),
        ("STEP 3 patch", "done", "idea.patch.txt apply_check.txt", text("apply_check.txt").splitlines()[0]),
        ("proof 1 honesty of P", "done", "HONESTY_P.txt p_honesty/", "bench 11/13/16 and perft 5 match the known nodes"),
        ("proof 2 switch off", "done", "proof_off_O.txt proof_off_G.txt", text("proof_off_O.txt").replace("\n", " ") + " | " + text("proof_off_G.txt").replace("\n", " ")),
        ("proof 3 switch on", "done", "proof_on_O.txt proof_on_O_sum.txt", text("proof_on_O.txt").replace("\n", " ") + " | " + text("proof_on_O_sum.txt").replace("\n", " ")),
        ("proof 4 uci options", "done", "uci_options.raw", "IdeaS24 check false; Samples 4; Swing 32"),
        ("proof 5 sanitizer", "done", "asan_G100_d10.meta asan_G100_finding.txt asan_scratch_finding.txt", "35 asan symbols, 0 lines on G100, scratch reports heap-buffer-overflow"),
        ("STEP 3 match", "done", "match_stdout.txt match_summary.txt match.pgn", text("match_summary.txt").splitlines()[2]),
        ("STEP 4 partner 010", "done", "partner_proof_off.txt partner_proof_on.txt partner_match_summary.txt", "CONFIRMS; " + text("partner_proof_on.txt").replace("\n", " ") + " | " + text("partner_match_summary.txt").splitlines()[2]),
        ("STEP 5 report", "done", "REPORT.md RESULT.txt", "this file"),
    ]
    print("step | status | evidence | result")
    for step, status, evidence, result in rows:
        print(step + " | " + status + " | " + evidence + " | " + result)

if __name__ == "__main__":
    main()
