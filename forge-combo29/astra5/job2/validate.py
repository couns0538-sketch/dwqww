"""Execute and check job 2 protocol stages separately, using an existing empty output folder."""

import argparse
import csv
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "O_del": (8034043, [13640,24637,47194], "dce216236443837d", "3b5fb2c3c8a5211a"),
    "G_del": (15429690, [29574,60830,89192], "dc1e72558bf88b8e", "5bb03c0424a9d6bf"),
    "O_del_fhb7": (8148181, [18586,19817,45782], "2cd1ab85c28b42e1", "3bcd4da745552b26"),
    "G_del_fhb7": (14751618, [34219,32603,53240], "9181bbd3591c4173", "e95cdf298e359440"),
    "O_dm12": (7841038, [11995,19758,32837], "3036c9511ea4c4d0", "b777ea49029deda4"),
    "G_dm12": (16925891, [36326,49343,48341], "a5bcaf0038eced2b", "d3c14b3f726a0dec"),
    "O_dm0": (8665792, [18009,19898,37065], "724960318794e924", "7622b6327b46588f"),
    "G_dm0": (18032844, [41177,58462,81548], "62c4476a64d7e2d9", "a7ca690c32054c5a"),
    "O_sm1": (10300501, [37073,40101,37833], "4fadaf54dfe33ce1", "d72afa986b8d3117"),
    "G_sm1": (18496605, [37997,64719,87437], "503d49e1299cc10c", "65045972b4698804"),
}
SLOTS = {
    "G_base": {0:176423,1:43862,2:67359,3:31604,7:1202904,10:4748667},
    "G_fhb7": {0:164148,1:48601,2:39128,3:29016,7:1041548,10:4134563},
    "O_base": {0:48220,2:5794},
    "O_fhb7": {0:47952,2:2124},
}
SETTINGS = ["base", "fhb7", "del", "del_fhb7", "sd20_base", "sd20_fhb7", "dm12", "dm0", "sm1"]
COPIED = ["index", "fen", "nodes", "bestmove"]


def read(path):
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def digest(rows, col):
    return hashlib.sha256("".join(r[col] + "\n" for r in rows).encode("ascii")).hexdigest()[:16]


def equal_rows(actual, expected, compare_count):
    if min(len(actual), len(expected)) < compare_count:
        raise ValueError(f"expected at least {compare_count} reference rows and actual rows")
    differences = []
    for i in range(compare_count):
        a, e = actual[i], expected[i]
        if any(a[k] != e[k] for k in COPIED):
            differences.append((i + 1, [e[k] for k in COPIED], [a[k] for k in COPIED]))
            if len(differences) == 5:
                break
    if differences:
        raise ValueError(f"first differences (position, expected, actual): {differences}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("step2", "step3", "step4"))
    parser.add_argument("exe", type=Path)
    parser.add_argument("positions", type=Path)
    parser.add_argument("evidence", type=Path, help="job2 directory under which step2–4 folders are written")
    parser.add_argument("job1_rows", type=Path)
    args = parser.parse_args()
    dest = args.evidence / args.stage
    dest.mkdir(parents=True, exist_ok=True)
    runner = Path(__file__).with_name("run_counts.py")
    for suite in (("G", "O") if args.stage == "step4" else ("O", "G")):
        for setting in SETTINGS:
            label = f"{suite}_{setting}"
            path = dest / (label + ".tsv")
            preregistered = setting in ("base", "fhb7")
            pcad_short = setting.startswith("sd20")
            short = (args.stage == "step2" and pcad_short) or (args.stage == "step3" and not preregistered)
            count = 20 if short else {"O":200, "G":353}[suite]
            cmd = [sys.executable, runner, "set", args.exe, args.positions / (suite + ".epd"), setting, path]
            if short:
                cmd += ["--first", str(count)]
            if args.stage != "step2":
                cmd += ["--slots", "16"]
            if args.stage == "step3" and short:
                cmd.append("--blind-counts")
            subprocess.run(cmd, check=True)
            rows = read(path)
            if len(rows) != count:
                raise ValueError(f"{label}: expected {count} rows, got {len(rows)}")
            nodes = [int(r["nodes"]) for r in rows]
            signature = (sum(nodes), nodes[:3], digest(rows, "nodes"), digest(rows, "bestmove"))
            if args.stage == "step2":
                if preregistered or pcad_short:
                    reference = args.job1_rows / (label + "_d12.tsv")
                    equal_rows(rows, read(reference), count)
                    desc = f"{count} rows identical to job1/{reference.name}"
                else:
                    if signature != EXPECTED[label]:
                        raise ValueError(f"{label}: expected {EXPECTED[label]}, observed {signature}")
                    desc = "published sum, first three and both hashes equal"
            elif args.stage == "step3":
                reference = args.evidence / "step2" / path.name
                equal_rows(rows, read(reference), 20)
                desc = "first 20 rows identical to PCAD"
                if not short:
                    equal_rows(rows, read(reference), count)
                    totals = {slot:sum(int(r["a25c"].split()[slot+1]) for r in rows) for slot in SLOTS[label]}
                    if totals != SLOTS[label]:
                        raise ValueError(f"{label}: expected {SLOTS[label]}, observed {totals}")
                    desc += f"; all {count} rows identical; published counters equal {totals}"
            else:
                reference = args.job1_rows / (label + "_d12.tsv") if pcad_short else args.evidence / "step2" / path.name
                equal_rows(rows, read(reference), count)
                desc = f"{count} rows identical to uninstrumented reference"
            print(f"{label}: {count} rows; {signature}; {desc}", flush=True)


if __name__ == "__main__":
    main()
