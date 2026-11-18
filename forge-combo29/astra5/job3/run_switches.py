"""Run Step 3's individual PC switch ladders and two PCA guards."""

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pc", type=Path)
    parser.add_argument("pca", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--seconds", type=int, default=0, help="wall-clock budget per ladder")
    args = parser.parse_args()
    with args.manifest.open(encoding="utf-8", newline="") as source:
        labels = list(dict.fromkeys(r["label"] for r in csv.DictReader(source, delimiter="\t")))
    runner = Path(__file__).with_name("ladder.py")
    ladders = [(args.pc, label, ["--switches", args.manifest, "--label", label]) for label in labels]
    for guard in ("RfpTtGuard", "RfpNoTtPv"):
        ladders.append((args.pca, guard, ["--set", guard + "=1"]))

    def launch(ladder):
        exe, label, extra = ladder
        cmd = [sys.executable, runner, exe, "PC20", args.out / label, "--last", "16", "--two",
               "--seconds", str(args.seconds), *extra]
        subprocess.run(cmd, check=True)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(launch, ladders))


if __name__ == "__main__":
    main()
