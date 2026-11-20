#!/usr/bin/env python3
"""Print the step table by reading the raw result files in this folder."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

def read(name):
    path = os.path.join(HERE, name)
    with open(path, encoding="utf-8") as handle:
        return handle.read().strip()

def main():
    rows = [
        ("STEP 1 seat", "done", "SEAT.txt", read("SEAT.txt")),
        ("STEP 2 honesty B", "done", "HONESTY_B.txt", read("HONESTY_B.txt").splitlines()[0] + " ... " + read("HONESTY_B.txt").splitlines()[-2]),
        ("STEP 2 O depth 12", "done", "b_O_d12.sum", read("b_O_d12.sum").splitlines()[0]),
        ("STEP 2 G depth 12", "done", "b_G_d12.sum", read("b_G_d12.sum").splitlines()[0]),
        ("STEP 3 prediction", "done", "prediction.txt", read("prediction.txt").splitlines()[1]),
        ("proof 1 honesty P", "done", "HONESTY_P.txt", read("HONESTY_P.txt").splitlines()[0] + " ... " + read("HONESTY_P.txt").splitlines()[-2]),
        ("proof 2 off O", "done", "proof_off_O.txt", read("proof_off_O.txt")),
        ("proof 2 off G", "done", "proof_off_G.txt", read("proof_off_G.txt")),
        ("proof 3 on O", "done", "proof_on_O.txt", read("proof_on_O.txt").splitlines()[0] + " | " + read("p_on_O_d12.sum").strip()),
        ("proof 5 sanitizer", "done", "san_g100.meta", "nm count " + read("san_g100.meta").splitlines()[3] + " " + [ln for ln in read("san_g100.meta").splitlines() if ln.startswith("sanitizer_lines")][0]),
        ("match", "done", "match_on_vs_off.parse", read("match_on_vs_off.parse")),
        ("STEP 4 off O", "done", "n060_proof_off_O.txt", read("n060_proof_off_O.txt")),
        ("STEP 4 off G", "done", "n060_proof_off_G.txt", read("n060_proof_off_G.txt")),
        ("STEP 4 on vs partner rows", "done", "n060_proof_on_O.txt", read("n060_proof_on_O.txt").replace("\n", " | ")),
        ("STEP 4 on vs B", "done", "n060_on_vs_B.txt", read("n060_on_vs_B.txt").splitlines()[0]),
        ("STEP 4 match R", "done", "n060_match_R.parse", read("n060_match_R.parse")),
    ]
    print("step | status | evidence | result")
    for step, status, evidence, result in rows:
        one = " ".join(result.split())
        print("%s | %s | %s | %s" % (step, status, evidence, one))

if __name__ == "__main__":
    main()
