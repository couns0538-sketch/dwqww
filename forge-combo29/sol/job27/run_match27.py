#!/usr/bin/env python3
"""Run one Job 27 match with its own pinned, disjoint opening subset."""

from hashlib import sha256
import json
from pathlib import Path
import re
import sys

MATCHES = {
    # games, seed, workers, nodes A, nodes B, extra options A and B
    "K16": (100, 7271, 4, 2000, 2000, (), ()),
    "D2s": (8000, 7272, 4, 2000, 2000, (("DrawJitter", "8"),), (("DrawJitter", "0"),)),
}
MEASURED = ("D2s",)


def opening_provenance(manifest_path, match, book, source_sha):
    try:
        contents = manifest_path.read_bytes()
        manifest = json.loads(contents)
        source = manifest["source"]["sha256"]
        source_positions = manifest["source"]["positions"]
        verified = manifest["verification"]
        entry = manifest["cells"][match]
        count, seed, digest = entry["count"], entry["seed"], entry["sha256"]
        filename = entry["file"]
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise SystemExit(f"Cannot read opening manifest for {match}: {error}") from error
    games, expected_seed, *_ = MATCHES[match]
    if source != source_sha or source_positions != 2632036:
        raise SystemExit(f"{manifest_path} does not identify the pinned source book")
    expected_count = sum(config[0] // 2 for config in MATCHES.values())
    count_fields = ("retained_positions", "distinct_exact_fen", "distinct_first_four_field_keys")
    overlap_fields = ("prior_exact_fen_overlap", "prior_first_four_field_overlap", "internal_overlap")
    if (any(verified.get(key) != expected_count for key in count_fields)
            or any(verified.get(key) != 0 for key in overlap_fields)
            or verified.get("epd_readback_matches_source_rows") is not True):
        raise SystemExit(f"{manifest_path} has no successful disjoint opening verification")
    if filename != f"{match}.epd" or book.resolve() != (manifest_path.parent / filename).resolve():
        raise SystemExit(f"{match} must use {manifest_path.parent / (match + '.epd')}")
    if count != games // 2 or seed != expected_seed:
        raise SystemExit(f"{match} has an unexpected manifest opening count or seed")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise SystemExit(f"{match} requires a valid opening-subset SHA-256")
    return {
        "book_sha256": digest,
        "book_source_sha256": source,
        "book_source_positions": source_positions,
        "book_manifest_sha256": sha256(contents).hexdigest(),
        "book_openings_count": count,
    }


def main():
    here = Path(__file__).resolve().parent
    for job16 in (here.parent / "job16", here.parent / "sol-job16"):
        if (job16 / "run_match16.py").is_file():
            sys.path.insert(0, str(job16))
            break
    else:
        raise SystemExit("Job 16 run_match16.py is missing from the adjacent job16 or sol-job16 directory")

    import run_match16

    original_grid, description = run_match16.MATCHES, run_match16.__doc__
    official_book_sha = run_match16.BOOK_SHA256
    original_run, original_command = run_match16.run, run_match16.fastchess_command

    def command_with_paired_output(fastchess, engine, book, pgn, match):
        command = original_command(fastchess, engine, book, pgn, match)
        if match in MEASURED:
            command.extend(("-ratinginterval", "1"))
        return command

    def run_with_opening_pin(args):
        provenance = opening_provenance(here / "openings/manifest.json", args.match,
                                        args.book, official_book_sha)
        run_match16.BOOK_SHA256 = provenance["book_sha256"]
        try:
            status = original_run(args)
        finally:
            run_match16.BOOK_SHA256 = official_book_sha

        sidecar = args.output / f"{args.match}.meta"
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        # Keep the actual hash when the inherited gate rejected a mislabeled input.
        provenance.pop("book_sha256")
        meta.update(provenance)
        if args.match in MEASURED:
            meta["rating_interval_pairs"] = 1
        temporary = sidecar.with_name(f".{sidecar.name}.tmp")
        temporary.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        temporary.replace(sidecar)
        return status

    run_match16.MATCHES = MATCHES
    run_match16.__doc__ = __doc__
    run_match16.run = run_with_opening_pin
    run_match16.fastchess_command = command_with_paired_output
    try:
        return run_match16.main()
    finally:
        run_match16.MATCHES = original_grid
        run_match16.__doc__ = description
        run_match16.run = original_run
        run_match16.fastchess_command = original_command


if __name__ == "__main__":
    raise SystemExit(main())
