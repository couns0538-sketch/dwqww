#!/usr/bin/env python3
"""Independently reconcile the book and game records using legal en passant."""

from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import re
from unittest.mock import patch

import chess

import independent_matches32 as matches
from independent_matches28 import opening_key, pgn_results

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parent / "sol-job1/repo"
FEN_TAG = re.compile(rb'(?m)^\[FEN "([^"\r\n]+)"\]\r?$')


def digest(data):
    return sha256(data).hexdigest()


def canonical_fen(fen):
    fields = fen.split()
    assert len(fields) == 6, fen
    if fields[3] != "-" and not chess.Board(fen).has_legal_en_passant():
        fields[3] = "-"
    return " ".join(fields)


def canonical_key(fen):
    return opening_key(canonical_fen(fen))


def tagged_fens(data):
    return Counter(line.decode("ascii") for line in FEN_TAG.findall(data))


def load_selected(args, manifest, describe):
    selected = {}
    for name, cell in manifest["cells"].items():
        raw = (args.books / cell["file"]).read_bytes()
        assert digest(raw) == cell["sha256"], name
        lines = raw.decode("ascii").splitlines()
        assert len(lines) == cell["count"], name
        assert list(map(opening_key, lines)) == cell["fen_keys_sha256"], name
        normalized = {canonical_key(fen): raw_key for fen, raw_key in zip(lines, cell["fen_keys_sha256"], strict=True)}
        assert len(normalized) == len(lines), name
        selected[name] = normalized
        for source, fen in zip(cell["source_line_numbers"], lines, strict=True):
            canonical = canonical_fen(fen)
            if fen == canonical:
                continue
            original, normalized_board = chess.Board(fen), chess.Board(canonical)
            assert original.is_valid() and normalized_board.is_valid(), (name, fen)
            assert set(original.legal_moves) == set(normalized_board.legal_moves), (name, fen)
            assert original.fen(en_passant="legal") == canonical, (name, fen)
            if describe:
                print(f"{name}, UHO source row {source}, book FEN {fen}")
                print(f"  Canonical FEN {canonical}; {original.legal_moves.count()} identical legal moves")
                print(f"  Keys {opening_key(fen)} -> {opening_key(canonical)}")
                for move in original.generate_pseudo_legal_ep():
                    assert not original.is_legal(move)
                    original.push(move)
                    king = original.king(not original.turn)
                    attackers = ", ".join(
                        f"{original.piece_at(square).symbol()} on {chess.square_name(square)}"
                        for square in original.attackers(original.turn, king)
                    )
                    assert attackers
                    print(f"  Pseudo-legal {move.uci()} exposes {chess.square_name(king)} to {attackers}.")
                    original.pop()
        if describe:
            print(f"{name} book SHA-256 {cell['sha256']}; {len(normalized)} unique normalized keys.")
    return selected


def archive_freshness(args, manifest, selected):
    archive = args.repo / "forge-combo29/sol"
    historical = manifest["historical"]
    sol = Counter()
    for file in historical["files"]:
        data = (archive / file["path"]).read_bytes()
        assert digest(data) == file["sha256"], file["path"]
        result = tagged_fens(data)
        assert result.total() == file["fen_tags"], file["path"]
        sol.update(result)
    assert sol.total() == historical["fen_tags"]
    past = {canonical_key(fen) for fen in sol}
    replay_receipt = manifest["historical_replay"]
    replay_bytes = (archive / replay_receipt["path"]).read_bytes()
    assert digest(replay_bytes) == replay_receipt["sha256"]
    replay = {canonical_key(line.decode("ascii").split("\t")[1]) for line in replay_bytes.splitlines()}
    assert len(replay) == replay_receipt["start_count"]
    astra = json.loads((HERE / "astra5-prior32.json").read_bytes())
    assert astra["sol_manifest_sha256"] == matches.MANIFEST_SHA
    astra_normalized, astra_raw = set(), set()
    for row in astra["rows"]:
        data = matches.blob(args.repo, astra["astra5_commit"], row["source"] + ".pgn")
        assert digest(data) == row["pgn_sha256"], row["source"]
        archive_fens = tagged_fens(data)
        assert archive_fens.total() == row["games"]
        astra_normalized.update(map(canonical_key, archive_fens))
        astra_raw.update(map(opening_key, archive_fens))
    exclusion = manifest["extra_exclusion"]
    filter_bytes = (HERE / exclusion["file"]).read_bytes()
    assert digest(filter_bytes) == exclusion["sha256"] and set(filter_bytes.decode("ascii").splitlines()) == astra_raw
    assert len(astra_raw) == exclusion["first_four_hash_count"]
    print(f"Historical Sol: {len(historical['files'])} archived PGNs, {sol.total()} FEN headers, {len(past)} normalized keys.")
    print(f"Job 3 replay: {len(replay)} normalized starts. Astra5: {len(astra['rows'])} pinned PGNs, {len(astra_normalized)} normalized keys.")
    for name, keys in selected.items():
        overlaps = [len(keys.keys() & archive_keys) for archive_keys in (past, replay, astra_normalized)]
        assert overlaps == [0, 0, 0], (name, overlaps)
        print(f"{name}: normalized overlap Sol / Job 3 / Astra5 = {overlaps}.")
    for left, right in combinations(selected, 2):
        assert not selected[left].keys() & selected[right].keys(), (left, right)
    print("All six between-book normalized intersections: zero.")


def check_match(args, manifest, canonical):
    raw_by_canonical = canonical[args.match]

    def readback(pgn, original_keys):
        assert original_keys == set(manifest["cells"][args.match]["fen_keys_sha256"])
        with patch("independent_matches28.opening_key", canonical_key):
            games, unresolved, results, used, *counted = pgn_results(pgn, raw_by_canonical.keys())
        return games, unresolved, results, {raw_by_canonical[key] for key in used}, *counted

    with patch.object(matches, "pgn_results", readback):
        matches.check(args)
    if args.published:
        matches.verify_publication(args, (HERE / f"{args.match}.commit").read_text().strip())


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("match", choices=("openings", *matches.SCHEDULE))
    cli.add_argument("--published", action="store_true")
    cli.add_argument("--books", type=Path, default=HERE / "openings")
    cli.add_argument("--raw", type=Path, default=HERE / "raw")
    cli.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    args = cli.parse_args()
    args.manifest = args.books / "manifest.json"
    args.pgn = None
    manifest_data = args.manifest.read_bytes()
    assert digest(manifest_data) == matches.MANIFEST_SHA
    manifest = json.loads(manifest_data)
    selected = load_selected(args, manifest, args.match == "openings")
    if args.match == "openings":
        archive_freshness(args, manifest, selected)
        print(f"Frozen manifest SHA-256 {matches.MANIFEST_SHA}.")
    else:
        check_match(args, manifest, selected)


if __name__ == "__main__":
    main()
