#!/usr/bin/env python3
"""The malformed-`go` matrix, measured on the audit base.

Sections:
  keywords  every keyword in parse_limits (uci.cpp:73-135) x {no value, junk,
            negative, 2^63, 2^64, zero, valid control}
  combos    a bad value on one keyword beside a well-formed limit on another
  book      which malformed forms reach the book with OwnBook true
  extra     forms outside the seat's list: bare `go`, unknown tokens, case,
            repeated keywords
  ladder    `go nodes abc` vs `go infinite` over a fixed window then `stop`

Every cell is a fresh process. A cell that has not returned by the cap is
reported as CAPPED and is still sent `stop` so its post-stop wire is recorded.

Usage: matrix.py EXE [section ...] > /dev/null   (writes evidence/)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from go_probe import (  # noqa: E402
    MIDGAME_BLACK,
    MIDGAME_WHITE,
    STARTPOS,
    run_cell,
    verdict,
)

CAP_S = 20.0
# Named so no table can be read without knowing what was measured on what.
BUILD = "base@6b98f217 (g++ 13.3.0, sha256 e06310ec)"
EVIDENCE = Path(__file__).resolve().parent.parent / "evidence"

# (keyword, form, command, note)
KEYWORD_CELLS: list[tuple[str, str, str, str]] = []


def add(keyword: str, form: str, command: str, note: str = "") -> None:
    KEYWORD_CELLS.append((keyword, form, command, note))


def keyword_cells() -> None:
    # Numeric keywords: the six malformed/edge forms plus a valid control.
    numeric = {
        "depth": ("go depth 5", "5 plies"),
        "nodes": ("go nodes 50000", "50k node budget"),
        "softnodes": ("go softnodes 50000", "finish the passing iteration, hard cap 4x"),
        "movetime": ("go movetime 100", "100 ms"),
        "movestogo": ("go movestogo 20", "no clock -> see combos section"),
        "wtime": ("go wtime 1000", "1 s, white to move"),
        "btime": ("go btime 1000", "1 s, WRONG side on a white-to-move board"),
        "winc": ("go winc 100", "increment only"),
        "binc": ("go binc 100", "increment only, wrong side"),
        "mate": ("go mate 3", "mate in 3"),
    }
    for kw, (valid, valid_note) in numeric.items():
        add(kw, "no value", f"go {kw}", "token consumed by the reader, nothing after it")
        add(kw, "junk", f"go {kw} abc", "unparseable")
        add(kw, "negative", f"go {kw} -1", "sign")
        add(kw, "2^63", f"go {kw} 9223372036854775808", "int64 overflow; uint64 still fits")
        if kw in ("nodes", "softnodes"):
            add(kw, "2^64", f"go {kw} 18446744073709551616", "uint64 overflow")
        add(kw, "zero", f"go {kw} 0", "the value the parser substitutes on failure")
        add(kw, "valid", valid, valid_note)

    # Flag keywords take no value at all, so "malformed" means junk around them.
    add("infinite", "flag", "go infinite", "no limit by definition")
    add("infinite", "junk after", "go infinite abc", "junk token ignored")
    add("infinite", "with depth", "go infinite depth 5", "does a depth beside infinite bind?")
    add("ponder", "flag", "go ponder", "suppresses the clock, needs ponderhit/stop")
    add("ponder", "junk after", "go ponder abc", "junk token ignored")
    add("ponder", "with clock", "go ponder wtime 1000", "does a clock beside ponder bind?")

    # searchmoves consumes a list until the next keyword; its failure modes are
    # list-shaped rather than value-shaped.
    add("searchmoves", "no moves", "go searchmoves", "specified but empty")
    add("searchmoves", "junk", "go searchmoves abc", "not a move")
    add("searchmoves", "illegal move", "go searchmoves a7a8", "a legal-format illegal move")
    add("searchmoves", "valid", "go searchmoves e2e4", "valid move, no other limit")
    add("searchmoves", "valid+limit", "go searchmoves e2e4 depth 8", "valid move + depth")
    add("searchmoves", "mixed", "go searchmoves e2e4 a7a8", "one legal, one illegal")
    add("searchmoves", "junk+limit", "go searchmoves abc depth 8", "junk move + depth")


COMBO_CELLS: list[tuple[str, str, str]] = [
    # The question: does a bad value on one keyword erase a good limit on another?
    ("bad nodes, good depth", "go depth 5 nodes abc", "does depth still bind?"),
    ("bad nodes first", "go nodes abc depth 5", "order swapped"),
    ("bad nodes, good movetime", "go nodes abc movetime 100", "does movetime still bind?"),
    ("bad depth, good nodes", "go depth abc nodes 50000", "does the node limit still bind?"),
    ("bad wtime, good depth", "go depth 5 wtime abc", "does a 0-ms clock crush depth 5?"),
    ("bad wtime, good depth, explicit 0", "go depth 5 wtime 0", "same, written out"),
    ("bad movetime, good depth", "go depth 5 movetime abc", "does a 0-ms movetime crush depth 5?"),
    ("good wtime, good depth", "go depth 5 wtime 1000", "two well-formed limits"),
    ("good wtime, bad depth", "go depth abc wtime 1000", "clock beats a 1-ply depth"),
    ("bad mate, good depth", "go depth 5 mate abc", "mate 0 beside depth 5"),
    ("bad nodes, good mate", "go nodes abc mate 3", "does mate still bind?"),
    ("bad softnodes, good depth", "go depth 5 softnodes abc", "does depth still bind?"),
    ("bad nodes, good searchmoves", "go searchmoves e2e4 nodes abc", "restricted but unbounded?"),
    ("bad nodes, good clock side", "go wtime 1000 nodes abc", "clock binds"),
    ("bad btime (wrong side), good depth", "go depth 5 btime abc", "btime ignored on white"),
    ("zero nodes, good depth", "go depth 5 nodes 0", "which wins, the 0 or the depth?"),
    ("bad movestogo, good clock", "go movestogo abc wtime 1000", "clock binds"),
    ("good movestogo, good clock", "go movestogo 20 wtime 1000", "movestogo + clock"),
    ("good movestogo, no clock", "go movestogo 20", "no clock at all"),
]

BOOK_CELLS: list[tuple[str, str, str]] = [
    ("book: valid clock", "go wtime 1000", "startpos, OwnBook true"),
    ("book: bad movetime", "go movetime abc", "the seat's accidental case"),
    ("book: movetime 0", "go movetime 0", "zero clock"),
    ("book: bad wtime", "go wtime abc", "0-ms clock via failure"),
    ("book: btime only (wrong side)", "go btime 1000", "no clock for this side"),
    ("book: bad depth", "go depth abc", "no clock -> analysis path"),
    ("book: depth 5", "go depth 5", "no clock -> analysis path"),
    ("book: bad nodes", "go nodes abc", "no clock -> analysis path"),
    ("book: bad mate", "go mate abc", "mate 0, no clock"),
    ("book: searchmoves", "go searchmoves e2e4 wtime 1000", "restriction disables the book"),
    ("book: infinite + clock", "go infinite wtime 1000", "infinite disables the book"),
    ("book: ponder + clock", "go ponder wtime 1000", "ponder disables the book"),
    ("book: bad movetime + depth", "go movetime abc depth 5", "clock present, depth beside it"),
    ("book: movetime 100", "go movetime 100", "short real clock"),
]

EXTRA_CELLS: list[tuple[str, str, str]] = [
    ("bare go", "go", "no arguments at all"),
    ("unknown token", "go foo", "unknown keyword"),
    ("misspelled keyword", "go depht 5", "typo'd keyword"),
    ("misspelled with clock", "go wtime 1000 depht 5", "typo beside a good clock"),
    ("case", "go Depth 5", "wrong case"),
    ("equals form", "go depth=5", "shell-style assignment"),
    ("repeated keyword", "go depth 10 depth 3", "which occurrence wins"),
    ("repeated nodes", "go nodes 50000 nodes abc", "good then bad"),
    ("leading junk", "go xyz depth 5", "junk before a good keyword"),
    ("trailing junk", "go depth 5 xyz", "junk after a good keyword"),
    ("float value", "go depth 5.5", "not an integer"),
    ("hex value", "go depth 0x10", "not decimal"),
    ("plus sign", "go depth +5", "explicit plus"),
    ("space-split digits", "go depth 5 0", "stray extra token"),
    ("movetime 1", "go movetime 1", "1 ms"),
]


def render_md(rows: list[dict], title: str) -> str:
    out = [f"## {title}", "", f"Build: {BUILD}. Cap: {CAP_S:g} s per cell. Fresh process per cell.", ""]
    out.append("| command | returned? | ms | depth | nodes | bestmove | info depth lines | pv? | note |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        returned = "yes" if r["terminated"] else "**NO (capped)**"
        out.append(
            f"| `{r['go']}` | {returned} | {r['elapsed_ms']:g} | {r['max_depth'] if r['max_depth'] is not None else '-'} "
            f"| {r['last_nodes'] if r['last_nodes'] is not None else '-'} | `{r['bestmove']}` "
            f"| {r['info_depth_lines']} | {'yes' if r['pv_present'] else 'no'} | {r['note']} |"
        )
    out.append("")
    return "\n".join(out)


def run_section(name: str, cells, position: str = MIDGAME_WHITE, own_book: bool = False) -> list[dict]:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    started = time.monotonic()
    for i, cell in enumerate(cells, 1):
        if len(cell) == 4:
            keyword, form, command, note = cell
        else:
            keyword, command, note = cell[0], cell[1], cell[2]
            form = ""
        print(f"[{name} {i}/{len(cells)}] {command}", file=sys.stderr, flush=True)
        c = run_cell(exe=EXE, go=command, position=position, own_book=own_book, timeout_s=CAP_S, build=BUILD)
        row = c.as_dict()
        row.update({"verdict": verdict(c), "note": note, "form": form, "keyword": keyword, "section": name})
        rows.append(row)
        label = "RET" if c.terminated else "CAP"
        print(
            f"    {label} d={c.max_depth} n={c.last_nodes} bm={c.bestmove} lines={c.info_depth_lines}"
            + ("" if c.terminated else f" stop->{c.stop_bestmove}"),
            file=sys.stderr,
            flush=True,
        )
    path = EVIDENCE / f"{name}.jsonl"
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    (EVIDENCE / f"{name}.md").write_text(render_md(rows, name))
    print(f"{name}: {len(rows)} cells in {time.monotonic() - started:.0f} s -> {path}", file=sys.stderr)
    return rows


def run_ladder() -> None:
    """`go nodes abc` vs `go infinite`: same ladder over a fixed window, then stop."""
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out = []
    for command in ("go infinite", "go nodes abc", "go nodes", "go mate abc"):
        cell = run_cell(EXE, command, MIDGAME_WHITE, False, 6.0, build=BUILD)
        ladder = []
        for text in cell.wire:
            if text.startswith("info depth"):
                try:
                    ladder.append(int(text.split()[2]))
                except (IndexError, ValueError):
                    pass
        post = []
        for text in cell.stop_wire:
            if text.startswith("info depth"):
                try:
                    post.append(int(text.split()[2]))
                except (IndexError, ValueError):
                    pass
        out.append(
            {
                "go": command,
                "window_s": 6.0,
                "depth_ladder_in_window": ladder,
                "lines_in_window": len(ladder),
                "max_depth_in_window": max(ladder) if ladder else None,
                "bestmove_after_stop": cell.stop_bestmove,
                "post_stop_ladder": post,
                "build": BUILD,
            }
        )
        print(json.dumps(out[-1]), file=sys.stderr, flush=True)
    (EVIDENCE / "ladder.json").write_text(json.dumps(out, indent=2) + "\n")
    lines = ["# `go nodes abc` vs `go infinite`, identical-window comparison", "", f"Build: {BUILD}.", ""]
    lines.append("| command | lines in 6 s | depths seen | bestmove after `stop` |")
    lines.append("|---|---|---|---|")
    for row in out:
        span = f"{row['depth_ladder_in_window'][0]}..{row['depth_ladder_in_window'][-1]}" if row["depth_ladder_in_window"] else "-"
        lines.append(f"| `{row['go']}` | {row['lines_in_window']} | {span} | `{row['bestmove_after_stop']}` |")
    lines.append("")
    (EVIDENCE / "ladder.md").write_text("\n".join(lines))
    print("ladder: written", file=sys.stderr)


if __name__ == "__main__":
    EXE = sys.argv[1]
    want = sys.argv[2:] or ["keywords"]
    t0 = time.monotonic()
    if "keywords" in want:
        keyword_cells()
        run_section("keywords", KEYWORD_CELLS)
    if "combos" in want:
        run_section("combos", COMBO_CELLS)
    if "book" in want:
        run_section("book", BOOK_CELLS, STARTPOS, own_book=True)
    if "extra" in want:
        run_section("extra", EXTRA_CELLS)
    if "ladder" in want:
        run_ladder()
    print(f"total {time.monotonic() - t0:.0f} s", file=sys.stderr)
