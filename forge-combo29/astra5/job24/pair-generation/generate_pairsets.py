"""Produce the 80 paired tuning vectors from the pinned Job 18 option table."""
import argparse
import csv
from hashlib import sha256
from pathlib import Path
import random
import sys

SOURCE_SHA256 = "8b9f11a1ca4f209b57cbc59ae6fc4c2bd6a09a54ffd4ce5af265fa87fbbede81"


def generate(source, target):
    if sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("settings source differs from Job 18 at 040834de294a31f81a3d6aa54a605af692a4fcb4")
    with source.open(newline="") as stream:
        settings = list(csv.DictReader(stream, delimiter="\t"))
    names = [r["name"] for r in settings]
    if len(settings) != 40 or len(set(names)) != 40:
        raise ValueError("expected 40 distinct setting names")
    writer = csv.writer(target, delimiter="\t", lineterminator="\n")
    writer.writerow(["j"] + [f"{side}_{name}" for side in ("plus", "minus") for name in names])
    for j in range(1, 81):
        rng = random.Random(240000 + j)
        plus, minus = [], []
        for r in settings:
            start, lower, upper, step = (int(r[key]) for key in ("start", "min", "max", "step"))
            sign = 2 * rng.randint(0, 1) - 1
            plus.append(max(lower, min(upper, start + sign * step)))
            minus.append(max(lower, min(upper, start - sign * step)))
        writer.writerow([j, *plus, *minus])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Job 18 sets.txt at commit 040834d")
    args = parser.parse_args()
    generate(args.source, sys.stdout)
