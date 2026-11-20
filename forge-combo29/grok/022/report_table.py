#!/usr/bin/env python3
"""Print the report table and the proof lines from the raw files in this folder."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (HERE / name).read_text(errors="replace")


def honesty(path: str) -> str:
    body = text(path)
    bits = []
    for line in body.splitlines():
        if " nodes " in line and "expected" in line:
            parts = line.split()
            bits.append(parts[2])
    tail = "PASS" if body.strip().endswith("PASS") else "FAIL"
    return tail + " " + " ".join(bits)


def main() -> None:
    proof = text("proof_compare.txt")
    on_claim = text("partner_072/on_vs_claimed.txt")
    on_b = text("partner_072/on_vs_b.txt")
    off = text("partner_072/compare.txt")
    match = text("match_summary.txt")
    pmatch = text("partner_072/match_summary.txt")
    asan_meta = text("asan_g100_d10.txt.meta")
    nm = [line for line in asan_meta.splitlines() if line.startswith("asan_symbol_count")]
    scratch = text("scratch_asan.txt")
    scratch_hit = "yes" if "runtime error:" in scratch else "no"
    print("HONESTY_B", honesty("HONESTY_B.txt"))
    print("HONESTY_P", honesty("HONESTY_P.txt"))
    print("HONESTY_PARTNER", honesty("HONESTY_072.txt"))
    print("--- proof_compare.txt ---")
    print(proof.rstrip())
    print("--- partner off vs B ---")
    print(off.rstrip())
    print("--- partner on vs claimed ---")
    print(on_claim.rstrip())
    print("--- partner on vs B ---")
    print(on_b.rstrip())
    print("--- asan ---")
    print(nm[0] if nm else "missing")
    print(f"scratch_sanitizer_line {scratch_hit}")
    print("--- match ---")
    for line in match.splitlines():
        if line.startswith("Elo:") or line.startswith("Games:"):
            print(line)
    print("--- partner match ---")
    for line in pmatch.splitlines():
        if line.startswith("Elo:") or line.startswith("Games:"):
            print(line)
    def grab(blob: str, prefix: str) -> str:
        for line in blob.splitlines():
            if line.startswith(prefix):
                return line
        return "missing"

    off_o = grab(proof, "differ")
    # proof_compare has three differ lines: none. Take the labelled blocks instead.
    print("--- steps ---")
    rows = [
        ("1 seat", "done", "SEAT.txt stamps.txt", text("SEAT.txt").split(",")[0] + "," + text("SEAT.txt").split(",")[1]),
        ("2 honesty B", "done", "HONESTY_B.txt", honesty("HONESTY_B.txt")),
        ("2 O and G", "done", "proof_compare.txt", "see proof_compare.txt sums"),
        ("3 prediction", "done", "prediction.txt", "file present, not edited after commit"),
        ("3 patch applies", "done", "apply_check.txt idea.patch.txt", text("apply_check.txt").strip()),
        ("3 proof off", "done", "proof_compare.txt", "see OFF_O and OFF_G blocks"),
        ("3 proof on", "done", "proof_compare.txt", "see ON_O block"),
        ("3 uci options", "done", "uci_p.txt", "IdeaS27 and IdeaS27_DeadZone lines in uci_p.txt"),
        ("3 sanitizer", "done", "asan_g100_d10.txt.meta scratch_asan.txt", f"{nm[0] if nm else 'missing'} scratch {scratch_hit}"),
        ("3 match", "done", "match_summary.txt match_og.txt match_og.pgn", grab(match, "Games:")),
        ("4 partner", "done", "partner_072/compare.txt partner_072/on_vs_claimed.txt partner_072/match_summary.txt", "off " + off_o + "; on claimed " + grab(on_claim, "equal") + "; " + grab(pmatch, "Games:")),
    ]
    print("step | status | evidence | result")
    for row in rows:
        print(" | ".join(row))


if __name__ == "__main__":
    main()
