"""Derive disjoint Job 26 replay books from the pinned UHO source."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import random
import re


SOURCE_SHA256 = "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a"
CELLS = (
    ("K15", 50, 7261),
    ("C15", 100, 7262),
    ("P1", 1000, 7263),
    ("P2", 1000, 7264),
    ("E2", 1000, 7265),
    ("P3", 1000, 7266),
    ("P4", 1000, 7267),
)
FEN_HEADER = re.compile(rb'^\[FEN[ \t]+"([^"\r\n]+)"\][ \t]*\r?$', re.MULTILINE)
METHOD = (
    "In order K15,C15,P1,P2,E2,P3,P4, draw one-based UHO line ordinals "
    "without replacement with Python random.Random(cell_seed).sample. "
    "Accept in sample order after first-four-field exclusion against every "
    "archived FEN and each earlier accepted line. Preserve source text with "
    "an LF delimiter. Initial sample size is twice the requested count plus "
    "32. If exhausted, restart deterministically with twice the sample size."
)


def fen_keys(value):
    fields = value.split()
    if len(fields) != 6:
        raise ValueError(f"expected a six-field FEN: {value!r}")
    return b" ".join(fields), b" ".join(fields[:4])


def inspect_source(path):
    digest = sha256()
    positions = 0
    with path.open("rb") as source:
        for line in source:
            digest.update(line)
            positions += 1
    if digest.hexdigest() != SOURCE_SHA256:
        raise ValueError(f"incorrect pinned UHO SHA-256 for {path}: {digest.hexdigest()}")
    return positions


def prior_fens(archive):
    files = sorted(
        (path for path in archive.glob("job*/raw/**/*.pgn")
         if int(path.relative_to(archive).parts[0][3:]) < 26),
        key=lambda path: (int(path.relative_to(archive).parts[0][3:]), path.as_posix()),
    )
    if not files:
        raise ValueError(f"no historical PGNs at {archive}")
    exact = set()
    first_four = set()
    inventory = []
    for path in files:
        content = path.read_bytes()
        tags = FEN_HEADER.findall(content)
        if not tags or len(tags) != len(re.findall(rb'^\[FEN\b', content, re.MULTILINE)):
            raise ValueError(f"missing or malformed FEN tag in {path}")
        for tag in tags:
            complete, key = fen_keys(tag)
            exact.add(complete)
            first_four.add(key)
        inventory.append({
            "path": path.relative_to(archive).as_posix(),
            "sha256": sha256(content).hexdigest(),
            "fen_tags": len(tags),
        })
    return exact, first_four, inventory


def choose_lines(source_path, positions, archive_keys):
    sample_multiplier = 2
    while True:
        samples = {}
        for name, count, seed in CELLS:
            size = min(positions, count * sample_multiplier + 32)
            samples[name] = random.Random(seed).sample(range(1, positions + 1), size)
        wanted = set().union(*samples.values())
        with source_path.open("rb") as source:
            sample_rows = {
                number: line.rstrip(b"\r\n")
                for number, line in enumerate(source, 1)
                if number in wanted
            }
        if sample_rows.keys() != wanted:
            raise ValueError("the source changed while selecting openings")
        used = set(archive_keys)
        selected = {}
        for name, count, _ in CELLS:
            retained = []
            for number in samples[name]:
                line = sample_rows[number]
                _, key = fen_keys(line)
                if key in used:
                    continue
                used.add(key)
                retained.append((number, line))
                if len(retained) == count:
                    break
            if len(retained) != count:
                break
            selected[name] = retained
        if len(selected) == len(CELLS):
            return selected, {name: len(sample) for name, sample in samples.items()}
        if all(len(sample) == positions for sample in samples.values()):
            raise ValueError("not enough disjoint unused positions")
        sample_multiplier *= 2


def read_back(output, chosen, archive_exact, archive_keys):
    seen_exact = set()
    seen_keys = set()
    for name, count, _ in CELLS:
        rows = (output / f"{name}.epd").read_bytes().splitlines()
        if len(rows) != count or rows != [row for _, row in chosen[name]]:
            raise ValueError(f"{name}: opening readback differs from original UHO rows")
        for row in rows:
            complete, key = fen_keys(row)
            if complete in archive_exact or key in archive_keys:
                raise ValueError(f"{name}: overlap with a historical FEN: {row!r}")
            if complete in seen_exact or key in seen_keys:
                raise ValueError(f"{name}: overlap with a new FEN: {row!r}")
            seen_exact.add(complete)
            seen_keys.add(key)
    return {
        "retained_positions": len(seen_exact),
        "distinct_exact_fen": len(seen_exact),
        "distinct_first_four_field_keys": len(seen_keys),
        "prior_exact_fen_overlap": 0,
        "prior_first_four_field_overlap": 0,
        "internal_overlap": 0,
        "epd_readback_matches_source_rows": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("archive", type=Path, help="forge-combo29/sol directory")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source_path = args.source.resolve(strict=True)
    archive = args.archive.resolve(strict=True)
    output = args.output.resolve()
    targets = [output / f"{name}.epd" for name, _, _ in CELLS] + [output / "manifest.json"]
    if any(path.exists() for path in targets):
        raise FileExistsError("select a new output directory instead of overwriting a book")

    positions = inspect_source(source_path)
    historical_exact, historical_keys, inventory = prior_fens(archive)
    chosen, sample_sizes = choose_lines(source_path, positions, historical_keys)
    output.mkdir(parents=True, exist_ok=True)
    cells = {}
    for (name, count, seed), target in zip(CELLS, targets[:-1], strict=True):
        rows = chosen[name]
        content = b"".join(row + b"\n" for _, row in rows)
        with target.open("xb") as file:
            file.write(content)
        cells[name] = {
            "file": target.name,
            "count": count,
            "seed": seed,
            "sampled_ordinals": sample_sizes[name],
            "source_line_numbers": [number for number, _ in rows],
            "sha256": sha256(target.read_bytes()).hexdigest(),
            "fen_keys_sha256": [sha256(fen_keys(row)[1]).hexdigest() for _, row in rows],
        }
    verification = read_back(output, chosen, historical_exact, historical_keys)
    manifest = {
        "source": {"path": str(source_path), "sha256": SOURCE_SHA256, "positions": positions},
        "selection_order": [name for name, _, _ in CELLS],
        "algorithm": METHOD,
        "historical": {
            "glob": "job*/raw/**/*.pgn under forge-combo29/sol",
            "scope": "All FEN tags, including controls, cut matches and unfinished games",
            "pgn_count": len(inventory),
            "fen_tags": sum(file["fen_tags"] for file in inventory),
            "distinct_exact": len(historical_exact),
            "distinct_first_four": len(historical_keys),
            "files": inventory,
        },
        "cells": cells,
        "verification": verification,
    }
    with targets[-1].open("x", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)
        file.write("\n")
    print(f"{len(inventory)} prior PGNs, {len(historical_keys)} prior first-four keys")
    print(f"{positions} UHO rows, {verification['retained_positions']} disjoint selected rows")
    for name, cell in cells.items():
        print(f"{name:4} {cell['count']:4} seed={cell['seed']} {cell['sha256']}")


if __name__ == "__main__":
    main()
