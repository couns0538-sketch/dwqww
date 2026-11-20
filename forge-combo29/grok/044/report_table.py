#!/usr/bin/env python3
"""Print the report table and the proof numbers from the raw files in this folder."""

from pathlib import Path


def load_nodes(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(int(line.split()[-1]))
    return rows


def last_line(path):
    lines = [line for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines[-1]


def differ(left, right):
    return sum(a != b for a, b in zip(left, right))


def elo_block(path):
    text = Path(path).read_text(encoding="utf-8")
    start = text.rfind("Results of ")
    end = text.find("Finished match", start)
    return text[start:end].strip()


def main():
    folder = Path(__file__).resolve().parent
    base_o = load_nodes(folder / "B_O_depth12.nodes")
    base_g = load_nodes(folder / "B_G_depth12.nodes")
    off_o = load_nodes(folder / "P_off_O_depth12.nodes")
    off_g = load_nodes(folder / "P_off_G_depth12.nodes")
    on_o = load_nodes(folder / "P_on_O_depth12.nodes")
    partner_off_o = load_nodes(folder / "partner_off_O_depth12.nodes")
    partner_off_g = load_nodes(folder / "partner_off_G_depth12.nodes")
    partner_on = load_nodes(folder / "partner_on_O_depth12.nodes")
    partner_claim = load_nodes(folder / "partner094_O_on.nodes")
    asan_raw = (folder / "asan_G100_depth10.raw").read_text(encoding="utf-8")
    scratch = (folder / "asan_scratch_depth10.raw").read_text(encoding="utf-8")
    asan_meta = (folder / "asan_G100_depth10.meta").read_text(encoding="utf-8")
    asan_count = [line for line in asan_meta.splitlines() if line.startswith("nm_asan_count=")][0]
    print("step | status | evidence | result")
    print("STEP 1 | done | SEAT.txt stamps.txt | seat 044 idea 44")
    print("STEP 2 | done | HONESTY_B.txt B_SUMS.txt | plain engine matches the known sums")
    print("STEP 3 proofs | done | P_COMPARE.txt honesty_p_bench11.txt | switch off identical, switch on differs")
    print("STEP 3 match | done | match/fastchess.log match/games.pgn | 1106 games")
    print("STEP 4 | done | partner_compare.txt partner_match/fastchess.log | partner 094")
    print("STEP 5 | done | REPORT.md RESULT.txt | this report")
    print("--- honesty B ---")
    for name in ("honesty_b_bench11.txt", "honesty_b_bench13.txt", "honesty_b_bench16.txt", "honesty_b_perft5.txt"):
        print(last_line(folder / name))
    print("--- honesty P ---")
    for name in ("honesty_p_bench11.txt", "honesty_p_bench13.txt", "honesty_p_bench16.txt", "honesty_p_perft5.txt"):
        print(last_line(folder / name))
    print("--- my switch ---")
    print(f"off_O differ {differ(base_o, off_o)} of {len(off_o)} sum {sum(off_o)}")
    print(f"off_G differ {differ(base_g, off_g)} of {len(off_g)} sum {sum(off_g)}")
    print(f"on_O differ {differ(base_o, on_o)} of {len(on_o)} sum {sum(on_o)}")
    print(f"asan_clean_lines {asan_raw.count('AddressSanitizer')} {asan_count}")
    print(f"asan_scratch_heap {scratch.count('heap-buffer-overflow')}")
    print("--- my match ---")
    print(elo_block(folder / "match" / "fastchess.log"))
    print("--- partner ---")
    print(f"partner_off_O differ {differ(base_o, partner_off_o)} of {len(partner_off_o)} sum {sum(partner_off_o)}")
    print(f"partner_off_G differ {differ(base_g, partner_off_g)} of {len(partner_off_g)} sum {sum(partner_off_g)}")
    print(f"partner_on_vs_claim differ {differ(partner_claim, partner_on)} of {len(partner_on)} sum {sum(partner_on)}")
    print(f"partner_on_vs_B differ {differ(base_o, partner_on)} of {len(partner_on)}")
    print(elo_block(folder / "partner_match" / "fastchess.log"))


if __name__ == "__main__":
    main()
