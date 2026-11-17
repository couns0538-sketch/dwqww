#!/usr/bin/env python3
"""Check FINDINGS.md's tables against the evidence files.

A findings document that states numbers is a set of claims; this re-derives the
ones that are mechanically checkable from the JSONL/JSON evidence and fails on a
mismatch. It cannot check prose (see §6 of the parent report on why a keyword
sweep is not a proof), so its clean exit means "the cited figures match the
artefacts", not "the document is correct".

Exit 0 = every checked claim matches. Exit 1 = at least one mismatch.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "evidence"
DOC = ROOT / "FINDINGS.md"

failures: list[str] = []
checks = 0


def load(name: str) -> list[dict]:
    path = EV / name
    if path.suffix == ".json":
        return json.loads(path.read_text())
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def check(claim: str, condition: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(f"{claim}{(' :: ' + detail) if detail else ''}")


def by_go(rows: list[dict]) -> dict[str, dict]:
    return {r["go"]: r for r in rows}


def main() -> int:
    kw = load("keywords.jsonl")
    combos = load("combos.jsonl")
    book = load("book.jsonl")
    extra = load("extra.jsonl")
    eating = load("eating.jsonl")
    lastwins = load("lastwins.jsonl")
    smoves = load("searchmoves.jsonl")
    ladder = load("ladder.json")
    bounded = load("boundedness.json")
    huge = load("huge_clock.json")
    inter = load("movetime_zero_interleaved.json")

    # Lookups must be per SECTION. `go depth abc` and `go movetime 0` appear in
    # both the midgame matrix and the startpos book matrix, and a flat dict keyed
    # on the command string silently returns whichever file was concatenated
    # last -- which made the first run of this checker report six "mismatches"
    # that were the checker's own bug. Keyed on (section, command) instead.
    def index(rows: list[dict], section: str) -> dict[str, dict]:
        return {r["go"]: r for r in rows if r.get("section", section) == section}

    keyword = index(kw, "keywords")
    combo = index(combos, "combos")
    bookm = index(book, "book")
    extram = index(extra, "extra")
    eatingm = index(eating, "eating")
    lastwinsm = index(lastwins, "lastwins")
    sm = index(smoves, "searchmoves")

    def cell(go: str, section: str = "keywords") -> dict:
        table = {
            "keywords": keyword,
            "combos": combo,
            "book": bookm,
            "extra": extram,
            "eating": eatingm,
            "lastwins": lastwinsm,
            "searchmoves": sm,
        }[section]
        return table[go]

    # --- §1 keyword table -------------------------------------------------
    for go, depth, nodes, bm in [
        ("go depth", 1, 42, "e1g1"),
        ("go depth abc", 1, 42, "e1g1"),
        ("go depth -1", 1, 42, "e1g1"),
        ("go depth 0", 1, 42, "e1g1"),
        ("go depth 5", 5, 818, "a2a3"),
        ("go movetime", 4, 302, "e1g1"),
        ("go movetime abc", 5, 818, "a2a3"),
        ("go movetime -1", 5, 818, "a2a3"),
        ("go nodes 50000", 12, 38459, "e1g1"),
        ("go softnodes 50000", 13, 84245, "e1g1"),
        ("go mate 3", 5, 53074, "e1g1"),
        ("go wtime 1000", 13, 84245, "e1g1"),
        ("go movetime 100", 13, 84245, "e1g1"),
    ]:
        c = cell(go)
        check(f"§1 {go} depth", c["max_depth"] == depth, f"{c['max_depth']} != {depth}")
        check(f"§1 {go} nodes", c["last_nodes"] == nodes, f"{c['last_nodes']} != {nodes}")
        check(f"§1 {go} bestmove", c["bestmove"] == bm, f"{c['bestmove']} != {bm}")

    # Unbounded rows: no bestmove inside the cap.
    for go in [
        "go nodes", "go nodes abc", "go nodes -1", "go nodes 9223372036854775808",
        "go nodes 18446744073709551616", "go softnodes", "go softnodes abc",
        "go movestogo", "go movestogo abc", "go movestogo 0", "go movestogo 20",
        "go btime", "go btime abc", "go btime 1000", "go winc 100", "go binc 100",
        "go mate", "go mate abc", "go mate 0", "go infinite", "go infinite abc",
        "go ponder", "go ponder wtime 1000", "go wtime 9223372036854775808",
        "go movetime 9223372036854775808",
    ]:
        c = cell(go)
        check(f"§1 {go} is capped", c["terminated"] is False, "returned inside the cap")

    # The zero-node forms return with no info lines.
    for go in ["go nodes 0", "go softnodes 0"]:
        c = cell(go)
        check(f"§1 {go} no info lines", c["terminated"] and c["info_depth_lines"] == 0,
              f"term={c['terminated']} lines={c['info_depth_lines']}")

    # --- §2a keyword eating ----------------------------------------------
    for go in ["go nodes depth 5", "go mate depth 5", "go softnodes depth 5", "go movestogo depth 5"]:
        check(f"§2a {go} unbounded", cell(go, "eating")["terminated"] is False, "returned")
    check("§2a wtime eats depth -> 1 ply", cell("go wtime depth 5", "eating")["max_depth"] == 1)
    check("§2a depth eats nodes -> 1 ply", cell("go depth nodes 50000", "eating")["max_depth"] == 1)

    # --- §2b: a malformed nodes value beside a depth limit ----------------
    # Only `go depth 5 nodes abc` is checked for depth 5 here. The reverse
    # direction (`go depth abc nodes 50000`) is in the combos file and yields
    # depth 1: the 1-ply depth finishes before the node budget can bind.
    for go, depth in [
        ("go depth 5 nodes abc", 5),
        ("go nodes abc movetime 100", 13),
        ("go nodes abc mate 3", 5),
        ("go depth 5 softnodes abc", 5),
        ("go wtime 1000 nodes abc", 13),
        ("go depth abc nodes 50000", 1),
        ("go depth 5 wtime abc", 1),
        ("go depth 5 wtime 0", 1),
    ]:
        check(f"§2b {go} depth", cell(go, "combos")["max_depth"] == depth, f"{cell(go, 'combos')['max_depth']} != {depth}")
    c = cell("go depth 5 nodes 0", "combos")
    check("§2b nodes 0 overrides depth", c["info_depth_lines"] == 0, f"lines={c['info_depth_lines']}")

    # --- §2c/2d boundedness ----------------------------------------------
    b = {(r["position"], r["go"]): r for r in bounded}
    for go in ["go nodes abc", "go mate abc", "go nodes"]:
        check(f"§2c {go} returns on K+R v K", b[("K+R v K", go)]["returned_on_its_own"] is True)
        check(f"§2c {go} caps on middlegame", b[("middlegame", go)]["returned_on_its_own"] is False)
    check("§2c infinite never returns on K+R v K",
          b[("K+R v K", "go infinite")]["returned_on_its_own"] is False)
    check("§2c K+R depth 64", b[("K+R v K", "go nodes abc")]["max_depth"] == 64,
          f"{b[('K+R v K', 'go nodes abc')]['max_depth']}")
    h = {r["go"]: r for r in huge}
    check("§2d huge wtime returns at depth 64",
          h["go wtime 9223372036854775808"]["returned_on_its_own"] and
          h["go wtime 9223372036854775808"]["max_depth"] == 64)
    check("§2d huge movetime returns at depth 64",
          h["go movetime 9223372036854775808"]["returned_on_its_own"] and
          h["go movetime 9223372036854775808"]["max_depth"] == 64)
    check("§2d malformed wtime is 1 ply", h["go wtime abc"]["max_depth"] == 1)

    # --- §3 movetime race -------------------------------------------------
    i = {r["go"]: r for r in inter}
    check("§3 movetime 0 has 3 outcomes", i["go movetime 0"]["distinct_outcomes"] == 3,
          str(i["go movetime 0"]["distinct_outcomes"]))
    check("§3 movetime 1 has 1 outcome", i["go movetime 1"]["distinct_outcomes"] == 1)
    top = i["go movetime 0"]["outcomes"][0]
    check("§3 movetime 0 modal outcome is depth 5", top["max_depth"] == 5, str(top["max_depth"]))
    check("§3 movetime 0 modal count is 27", top["count"] == 27, str(top["count"]))
    check("§3 repeats are 30", i["go movetime 0"]["repeats"] == 30)

    # --- §4 book ----------------------------------------------------------
    # The book MOVE is nondeterministic (book_rng seeded from the clock), so the
    # checkable claim is the wire SHAPE -- an `info string book move` line, zero
    # `info depth` lines, a legal move -- not a particular move. Asserting a
    # specific move here is what made this checker's first version fail against
    # a correct document.
    for go in [
        "go wtime 1000", "go movetime abc", "go movetime 0", "go wtime abc",
        "go movetime 100", "go movetime abc depth 5",
    ]:
        c = cell(go, "book")
        check(f"§4 {go} is a book reply", c["book_move_line"] is not None, "no book line")
        check(f"§4 {go} zero info depth", c["info_depth_lines"] == 0, str(c["info_depth_lines"]))
        check(f"§4 {go} terminated", c["terminated"] is True)
        check(f"§4 {go} has a legal-looking move",
              c["bestmove"] is not None and c["bestmove"] != "0000", str(c["bestmove"]))
    for go in ["go btime 1000", "go nodes abc", "go mate abc", "go infinite wtime 1000", "go ponder wtime 1000"]:
        c = cell(go, "book")
        check(f"§4 {go} does not reach book", c["book_move_line"] is None, "reached the book")
        check(f"§4 {go} unbounded", c["terminated"] is False, "returned")
    c = cell("go searchmoves e2e4 wtime 1000", "book")
    check("§4 searchmoves disables book", c["book_move_line"] is None and c["max_depth"] == 14)
    check("§4 depth 5 on startpos is a real search", cell("go depth 5", "book")["info_depth_lines"] == 5)

    # The discriminator claim: nodes 0 has NO info string, book has one.
    check("§4 nodes 0 emits no info string", cell("go nodes 0", "keywords")["info_string_lines"] == [],
          str(cell("go nodes 0", "keywords")["info_string_lines"]))
    check("§4 book emits an info string", len(cell("go movetime 100", "book")["info_string_lines"]) > 0)

    # --- §5 extra forms ---------------------------------------------------
    for go in ["go", "go foo", "go depht 5", "go Depth 5", "go depth=5"]:
        check(f"§5 {go} unbounded", cell(go, "extra")["terminated"] is False, "returned")
    for go, depth in [
        ("go wtime 1000 depht 5", 13),
        ("go depth 10 depth 3", 3),
        ("go nodes 50000 nodes abc", 12),
        ("go xyz depth 5", 5),
        ("go depth 5 xyz", 5),
        ("go depth 5.5", 1),
        ("go depth 0x10", 1),
        ("go depth +5", 1),
        ("go depth 5 0", 5),
    ]:
        check(f"§5 {go} depth", cell(go, "extra")["max_depth"] == depth, f"{cell(go, 'extra')['max_depth']} != {depth}")
    for go, depth in [
        ("go nodes 50000 nodes 0", None),
        ("go depth 8 depth abc", 1),
        ("go depth 8 depth 0", 1),
        ("go wtime 2000 wtime abc", 1),
        ("go movetime 200 movetime abc", 5),
    ]:
        check(f"§5 lastwins {go} depth", cell(go, "lastwins")["max_depth"] == depth, f"{cell(go, 'lastwins')['max_depth']} != {depth}")
    check("§5 mate 2 mate abc unbounded", cell("go mate 2 mate abc", "lastwins")["terminated"] is False)
    # `go movetime 1` is deliberately NOT checked for a depth: it is one of the
    # race-affected arms in §3 (1 of 30 runs came back at depth 4), so pinning it
    # to a single depth would be pinning a coin flip.

    # --- §1 searchmoves ---------------------------------------------------
    sm = by_go(smoves)
    for go in ["go searchmoves", "go searchmoves abc", "go searchmoves a7a8"]:
        c = sm[go]
        check(f"§1 {go} -> 0000", c["bestmove"] == "0000")
        check(f"§1 {go} zero nodes", (c["last_nodes"] or 0) == 0, str(c["last_nodes"]))
    check("§1 legal searchmoves alone is unbounded", sm["go searchmoves d2d4"]["terminated"] is False)
    check("§1 searchmoves + depth binds", sm["go searchmoves d2d4 depth 8"]["max_depth"] == 8)
    mixed = sm["go searchmoves d2d4 a7a8"]
    check("§1 mixed searchmoves unbounded", mixed["terminated"] is False)
    check("§1 mixed searchmoves no diagnostic",
          all("illegal" not in s for s in mixed["info_string_lines"]), str(mixed["info_string_lines"]))

    # --- §6 A1 range table ------------------------------------------------
    # The A1 table claims each of these is ACCEPTED by the parser and then
    # reinterpreted. Checked here so the client-side rule does not rest on prose.
    check("A1 depth -1 -> 1 ply", cell("go depth -1")["max_depth"] == 1)
    check("A1 depth 0 -> 1 ply", cell("go depth 0")["max_depth"] == 1)
    check("A1 depth 2^63 -> 1 ply", cell("go depth 9223372036854775808")["max_depth"] == 1)
    check("A1 movestogo 0 -> unbounded", cell("go movestogo 0")["terminated"] is False)
    check("A1 mate 0 -> unbounded", cell("go mate 0")["terminated"] is False)
    c = cell("go nodes 0")
    check("A1 nodes 0 -> zero info lines", c["info_depth_lines"] == 0)
    check("A1 nodes 0 still returns a move", c["bestmove"] is not None)
    # A3: the case a `<=` depth check cannot catch.
    shallow = cell("go depth 5 wtime abc", "combos")
    check("A3 depth 5 wtime abc reports depth 1 (passes a <= check)", shallow["max_depth"] == 1,
          str(shallow["max_depth"]))
    check("A3 which means A3 must assert equality", shallow["max_depth"] != 5)

    # --- ladder -----------------------------------------------------------
    lad = {r["go"]: r for r in ladder}
    check("§ladder infinite ladder non-empty", lad["go infinite"]["lines_in_window"] > 0)
    check("§ladder nodes abc ladder non-empty", lad["go nodes abc"]["lines_in_window"] > 0)

    # --- §1b honesty: the build label is on every row ---------------------
    for rows, name in ((kw, "keywords"), (combos, "combos"), (book, "book"), (extra, "extra")):
        check(f"§method {name} rows carry a build label",
              all("6b98f217" in r.get("build", "") for r in rows), "a row is unlabelled")

    # --- report -----------------------------------------------------------
    print(f"{checks} claims checked against evidence")
    if failures:
        print(f"\n{len(failures)} MISMATCH(ES):")
        for f in failures:
            print("  -", f)
        return 1
    print("all checked claims match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
