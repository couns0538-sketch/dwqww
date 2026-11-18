"""Compare Step 1 runs directly with the pinned kimi5 depth-12 rows and EPD order."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


SOURCE = "5db05e095d5e81622eb0de13eb8a738a0ae1d22a"
# git ls-tree -r SOURCE -- forge-combo29/tests_kimi5_job25
BLOBS = {
    "O.epd": "e967e8327ec2be34eaf6df7f1763fa13b00e6497",
    "G.epd": "827bda196bb7dea0df27f6d78fb3039e31c58f75",
    "base_O_d12.json": "88c21f491b638bd4f54536648b08821054e73e85",
    "fhb7_O_d12.json": "efd255fa283ac78490ee9d304bbdaa6772bdd87e",
    "base_G_d12.json": "21595a8718f846390624f24bbf70d967604805b9",
    "fhb7_G_d12.json": "acc8da976c1090c0a96bfa7d4370da7d17b91628",
}


def pinned_bytes(path):
    raw = path.read_bytes()
    blob = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
    if blob != BLOBS[path.name]:
        raise SystemExit(f"reference {path.name} does not match its blob at {SOURCE}")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rows", type=Path, help="astra5 TSV directory")
    parser.add_argument("reference", type=Path, help="kimi5 job25 rows directory (JSON)")
    parser.add_argument("positions", type=Path, help="kimi5 job25 EPD directory")
    args = parser.parse_args()
    print(f"Step 1 direct comparison, PCA PC20 depth 12; kimi5 commit {SOURCE}")
    for suite, size in (("O", 200), ("G", 353)):
        epd = args.positions / f"{suite}.epd"
        fens = [" ".join(line.split()[:4] + ["0", "1"])
                for line in pinned_bytes(epd).decode("utf-8").splitlines()]
        for mode in ("base", "fhb7"):
            path = args.rows / f"{suite}_{mode}_d12.tsv"
            meta = Path(str(path) + ".meta").read_text().splitlines()
            if f"completed_rows {size}" not in meta:
                raise SystemExit(f"{path.name}: missing completion marker")
            ref_path = args.reference / f"{mode}_{suite}_d12.json"
            known = json.loads(pinned_bytes(ref_path))
            with path.open(newline="") as stream:
                rows = list(csv.DictReader(stream, delimiter="\t"))
            if any(len(series) != size for series in (fens, rows, known["per_position"], known["bestmove"])):
                raise SystemExit(f"{path.name}: row count mismatch, expected {size}")
            for i, (row, fen, nodes, move) in enumerate(zip(rows, fens, known["per_position"], known["bestmove"]), 1):
                expected = {"index": str(i), "fen": fen, "nodes": str(nodes), "bestmove": move}
                if row != expected:
                    raise SystemExit(f"{path.name} first differing position {i}\nactual {row}\nreference {expected}")
            print(f"{path.name} vs {ref_path.name} and {epd.name}: {size}/{size} indices, FENs, "
                  f"node counts and best moves equal")


if __name__ == "__main__":
    main()
