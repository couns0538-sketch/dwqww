#!/usr/bin/env python3
"""Read the raw result files and print the report facts. No hand-typed numbers."""

from pathlib import Path

ROOT = Path("/agent/repos/dwqww/forge-combo29/grok/094")


def nodes_in(path: Path) -> str:
    text = path.read_text()
    found = None
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            index = parts.index("nodes")
            if index + 1 < len(parts) and parts[index + 1].isdigit():
                found = parts[index + 1]
    return found if found else "MISSING"


def file_text(name: str) -> str:
    return (ROOT / name).read_text().rstrip()


def count_lines(name: str, needle: str) -> int:
    return sum(1 for line in (ROOT / name).read_text().splitlines() if needle in line)


def main() -> None:
    print("step | status | evidence | result")
    honesty = []
    for tag, label in (("B", "bench11"), ("B", "bench13"), ("B", "bench16"), ("B", "perft5")):
        pass
    for tag in ("B", "P"):
        bits = []
        for name in ("bench11", "bench13", "bench16", "perft5"):
            bits.append(f"{name} {nodes_in(ROOT / f'HONESTY_{tag}_{name}.txt')}")
        print(f"honesty {tag} | done | HONESTY_{tag}.txt | " + " ".join(bits))
    print("baseline O | done | O_B.meta | " + [line for line in file_text("O_B.meta").splitlines() if line.startswith("sum ")][0])
    print("baseline G | done | G_B.meta | " + [line for line in file_text("G_B.meta").splitlines() if line.startswith("sum ")][0])
    print("apply | done | apply_check.txt | " + file_text("apply_check.txt"))
    print("proof off O | done | compare_O_off.txt | " + " ; ".join(file_text("compare_O_off.txt").splitlines()[:4]))
    print("proof off G | done | compare_G_off.txt | " + " ; ".join(file_text("compare_G_off.txt").splitlines()[:4]))
    print("proof on O | done | compare_O_on.txt | " + " ; ".join(file_text("compare_O_on.txt").splitlines()[:4]))
    print("uci | done | UCI_OPTIONS_IDEA.txt | " + " ; ".join(file_text("UCI_OPTIONS_IDEA.txt").splitlines()))
    print("asan nm | done | asan_nm_count.txt G100_asan.meta | count " + file_text("asan_nm_count.txt"))
    print("asan real lines | done | G100_asan.log | AddressSanitizer " + str(count_lines("G100_asan.log", "AddressSanitizer")) + " runtime error " + str(count_lines("G100_asan.log", "runtime error")))
    print("asan scratch | done | scratch_asan_report.log | heap-buffer-overflow " + str(count_lines("scratch_asan_report.log", "heap-buffer-overflow")))
    print("match | done | match_summary.txt | " + " ; ".join(file_text("match_summary.txt").splitlines()))
    print("partner apply | done | partner_apply_check.txt | " + file_text("partner_apply_check.txt"))
    print("partner honesty | done | partner_honesty.progress | " + " ; ".join(file_text("partner_honesty.progress").splitlines()))
    print("partner off | done | partner_compare_off.txt | " + " ; ".join(file_text("partner_compare_off.txt").splitlines()[:4]))
    print("partner on | done | partner_compare_on.txt | " + " ; ".join(file_text("partner_compare_on.txt").splitlines()[:4]))
    print("partner match | done | partner_match.log | " + " ; ".join(line for line in file_text("partner_match.log").splitlines() if line.startswith("Elo:") or line.startswith("Games:") or line.startswith("MATCH_EXIT")))


if __name__ == "__main__":
    main()
