#!/usr/bin/env python3
"""
Job 15 Part 1 — Protocol Identity Test of 04_S7 (apply_position_sv, parse_limits_sv)
====================================================================================
- Seed: 15001 for every random choice.
- Builds one deterministic command stream (>= 20,000 position commands) from the 60 games
  of the self-play driver covering categories (a) through (h).
- Drives two plain no-PGO builds (`r15d` and `curated`) with PC20 + net512.fnn3 (Threads 1,
  Hash 16), synchronously waiting for `bestmove` after every search `go` and `readyok` after
  every block (never piping the whole file at once).
- Compares every emitted line line-for-line after stripping `time <N>`, `nps <N>`, and
  `hashfull <N>` from `info` lines.
- Also runs the stream up to the planted-fault divergence against a scratch copy of `curated`
  whose quick prefix test omits `moves_sv[canon.size()]` whitespace-boundary checking, and
  records the first differing line.
"""
from __future__ import annotations

import hashlib
import pathlib
import random
import re
import subprocess
import sys
import time

SEED = 15001
REPO = pathlib.Path("/agent/repos/dwqww")
sys.path.insert(0, str(REPO / "forge-combo29/carbon2/job2"))
from selfplay_driver_v2 import (  # noqa: E402
    PC20_OPTIONS,
    MinimalBoardTracker,
    fnv1a64_str,
    select_book_fens,
    send,
    wait_ready_collect,
)

STRIP_RE = re.compile(r"\b(?:time|nps|hashfull)\s+-?\d+")


def normalize_line(line: str) -> str:
    s = line.rstrip("\r\n")
    if s.startswith("info "):
        s = STRIP_RE.sub("", s)
        s = re.sub(r" {2,}", " ", s).strip()
    return s


def collect_60_driver_games(engine_bin: str, net768: str, pos250: pathlib.Path) -> tuple[list[tuple[str, list[str]]], list[list[str]]]:
    """Collect the exact 60 FEN-rooted self-play driver games (trace ee465caeff9c0fcf)
    plus 2 startpos-rooted self-play games so both startpos and FEN roots have deep legal games."""
    fens_60 = select_book_fens(pos250, 60)
    proc = subprocess.Popen(
        [engine_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    cfg = ["uci\n"] + [f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS] + [
        f"setoption name NNUEArchFile value {net768}\n",
        "setoption name NNUEArch value true\n",
        "isready\n",
    ]
    send(proc, "".join(cfg))
    wait_ready_collect(proc, check_errors=True)

    games_60: list[tuple[str, list[str]]] = []
    trace_hash = 14695981039346656037
    total_searches = 0
    total_nodes = 0

    for g_idx, root_fen in enumerate(fens_60):
        send(proc, "ucinewgame\nisready\n")
        wait_ready_collect(proc, check_errors=True)
        moves: list[str] = []
        tracker = MinimalBoardTracker()
        tracker.load_fen(root_fen)
        for ply in range(300):
            if tracker.is_draw():
                break
            pos_str = f"position fen {root_fen}" + (" moves " + " ".join(moves) if moves else "")
            send(proc, f"{pos_str}\ngo softnodes 2000\n")
            last_nodes = 0
            last_score = ""
            bestmove = "0000"
            while True:
                ln = proc.stdout.readline()
                if ln.startswith("info depth "):
                    parts = ln.split()
                    for i, tok in enumerate(parts):
                        if tok == "nodes" and i + 1 < len(parts):
                            last_nodes = int(parts[i + 1])
                        elif tok == "score" and i + 2 < len(parts):
                            last_score = f"{parts[i + 1]}:{parts[i + 2]}"
                elif ln.startswith("bestmove "):
                    bestmove = ln.split()[1]
                    break
            total_searches += 1
            total_nodes += last_nodes
            trace_hash = fnv1a64_str(trace_hash, f"{g_idx},{ply},{bestmove},{last_nodes},{last_score};")
            if bestmove == "0000" or last_nodes == 0:
                break
            moves.append(bestmove)
            tracker.push_uci(bestmove)
        games_60.append((root_fen, moves))

    assert f"{trace_hash:016x}" == "ee465caeff9c0fcf", f"Unexpected trace {trace_hash:016x}"
    assert total_searches == 7670 and total_nodes == 25641316

    # Also play 2 startpos games (seed 15001 4-ply opening) so startpos has long all-legal games too
    rng = random.Random(SEED)
    startpos_games: list[list[str]] = []
    for openings in (["e2e4", "e7e5", "g1f3", "b8c6"], ["d2d4", "d7d5", "c2c4", "e7e6"]):
        send(proc, "ucinewgame\nisready\n")
        wait_ready_collect(proc, check_errors=True)
        moves = list(openings)
        tracker = MinimalBoardTracker()
        tracker.load_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        for m in moves:
            tracker.push_uci(m)
        for _ in range(160):
            if tracker.is_draw():
                break
            send(proc, f"position startpos moves {' '.join(moves)}\ngo softnodes 2000\n")
            bm = "0000"
            last_n = 0
            while True:
                ln = proc.stdout.readline()
                if ln.startswith("info depth "):
                    parts = ln.split()
                    if "nodes" in parts:
                        last_n = int(parts[parts.index("nodes") + 1])
                elif ln.startswith("bestmove "):
                    bm = ln.split()[1]
                    break
            if bm == "0000" or last_n == 0:
                break
            moves.append(bm)
            tracker.push_uci(bm)
        startpos_games.append(moves)
        _ = rng.randint(0, 1)

    send(proc, "quit\n")
    proc.communicate()
    return games_60, startpos_games


def query_legal_moves(engine_bin: str, pos_cmd: str) -> list[str]:
    proc = subprocess.Popen(
        [engine_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, _ = proc.communicate(f"uci\nisready\n{pos_cmd}\ngo perft 1\nquit\n")
    legals = []
    for ln in out.splitlines():
        if ": " in ln and not ln.startswith("info ") and not ln.startswith("id ") and not ln.startswith("option "):
            mv = ln.split(":", 1)[0].strip()
            if 4 <= len(mv) <= 5:
                legals.append(mv)
    return legals


def build_protocol_stream(
    engine_bin: str,
    games_60: list[tuple[str, list[str]]],
    startpos_games: list[list[str]],
) -> tuple[list[dict], dict[str, int]]:
    """
    Returns a list of step dicts:
      {
        "kind": "a".."h",
        "pre_ucinewgame": bool,
        "pos_cmd": str,
        "extra_go": str | None,
      }
    Every step corresponds to 1 position command followed by probe `go perft 2`, `eval`, `isready`,
    plus if extra_go is set (`(h)`), that `go ...` search + `isready`,
    plus after every 50th position command, `ucinewgame`, re-apply `pos_cmd` (since Forge's
    `ucinewgame` resets `board` to `startpos` in `src/uci.cpp:577`), `go depth 6`, `isready`.
    """
    rng = random.Random(SEED)
    steps: list[dict] = []
    counts = {k: 0 for k in "abcdefgh"}

    def add_step(kind: str, pos_cmd: str, pre_ucinewgame: bool = False, extra_go: str | None = None) -> None:
        steps.append(
            {
                "kind": kind,
                "pre_ucinewgame": pre_ucinewgame,
                "pos_cmd": pos_cmd,
                "extra_go": extra_go,
            }
        )
        counts[kind] += 1

    # (a) Every prefix of each of the 60 games, growing, as `position startpos moves ...`
    #     and as `position fen <the game's start> moves ...` (plus the 2 all-legal startpos games).
    for sp_moves in startpos_games:
        add_step("a", "position startpos")
        for k in range(1, len(sp_moves) + 1):
            add_step("a", f"position startpos moves {' '.join(sp_moves[:k])}")
    for root_fen, moves in games_60:
        add_step("a", "position startpos")
        for k in range(1, len(moves) + 1):
            add_step("a", f"position startpos moves {' '.join(moves[:k])}")
        add_step("a", f"position fen {root_fen}")
        for k in range(1, len(moves) + 1):
            add_step("a", f"position fen {root_fen} moves {' '.join(moves[:k])}")

    # (b) The same prefixes shrinking, and in a seeded random order (seed 15001).
    sampled_b = rng.sample(range(len(games_60)), 10)
    # Also include startpos_games[0] so all-legal startpos prefixes shrink and permute too
    for k in range(len(startpos_games[0]), -1, -1):
        cmd = "position startpos" if k == 0 else f"position startpos moves {' '.join(startpos_games[0][:k])}"
        add_step("b", cmd)
    idxs = list(range(len(startpos_games[0]) + 1))
    rng.shuffle(idxs)
    for k in idxs:
        cmd = "position startpos" if k == 0 else f"position startpos moves {' '.join(startpos_games[0][:k])}"
        add_step("b", cmd)

    for gi in sampled_b:
        root_fen, moves = games_60[gi]
        # Shrinking (startpos & fen)
        for k in range(len(moves), -1, -1):
            add_step("b", "position startpos" if k == 0 else f"position startpos moves {' '.join(moves[:k])}")
        for k in range(len(moves), -1, -1):
            add_step("b", f"position fen {root_fen}" if k == 0 else f"position fen {root_fen} moves {' '.join(moves[:k])}")
        # Seeded random order (startpos & fen)
        order_sp = list(range(len(moves) + 1))
        rng.shuffle(order_sp)
        for k in order_sp:
            add_step("b", "position startpos" if k == 0 else f"position startpos moves {' '.join(moves[:k])}")
        order_fn = list(range(len(moves) + 1))
        rng.shuffle(order_fn)
        for k in order_fn:
            add_step("b", f"position fen {root_fen}" if k == 0 else f"position fen {root_fen} moves {' '.join(moves[:k])}")

    # (c) The root changing between two commands (game A, game B, game A again).
    for i in range(60):
        j = (i + 1 + rng.randint(0, 58)) % 60
        fen_a, mv_a = games_60[i]
        fen_b, mv_b = games_60[j]
        ka1 = min(len(mv_a), rng.randint(2, 20))
        kb = min(len(mv_b), rng.randint(2, 20))
        ka2 = min(len(mv_a), ka1 + rng.randint(1, 10))
        add_step("c", f"position fen {fen_a} moves {' '.join(mv_a[:ka1])}")
        add_step("c", f"position fen {fen_b} moves {' '.join(mv_b[:kb])}")
        add_step("c", f"position fen {fen_a} moves {' '.join(mv_a[:ka2])}")
    for i in range(20):
        fen_b, mv_b = games_60[i]
        k1 = min(len(startpos_games[0]), 4 + i)
        kb = min(len(mv_b), 6 + i)
        k2 = min(len(startpos_games[0]), k1 + 3)
        add_step("c", f"position startpos moves {' '.join(startpos_games[0][:k1])}")
        add_step("c", f"position fen {fen_b} moves {' '.join(mv_b[:kb])}")
        add_step("c", f"position startpos moves {' '.join(startpos_games[0][:k2])}")

    # (d) Two spaces, a tab, and trailing spaces between move tokens and after "moves";
    #     "moves" with nothing after it.
    seps = ["  ", "\t", "  \t ", "\t  "]
    add_step("d", "position startpos moves")
    add_step("d", "position startpos moves   ")
    add_step("d", "position startpos moves\t  ")
    for gi in range(60):
        fen, moves = games_60[gi]
        add_step("d", f"position fen {fen} moves")
        add_step("d", f"position fen {fen} moves  \t  ")
        # Growing prefix where first cmd is canonical and second cmd uses non-canonical whitespace
        k1 = min(len(moves), 8)
        k2 = min(len(moves), 14)
        if k1 >= 2:
            add_step("d", f"position fen {fen} moves {' '.join(moves[:k1])}")
            sep_after = seps[gi % len(seps)]
            joined = ""
            for idx_m, m in enumerate(moves[:k2]):
                if idx_m > 0:
                    joined += seps[(gi + idx_m) % len(seps)]
                joined += m
            add_step("d", f"position  fen  {fen}\tmoves{sep_after}{joined}   \t ")

    # (e) Illegal move in the middle (a move from another game), "e2e9", a promotion letter
    #     that does not belong ("e2e4q"), and after each of them a command that continues
    #     the list past the bad token.
    # Start explicitly with startpos e2e4 -> e2e4q e7e5 g1f3 -> e2e4 e7e5 g1f3 (catches planted fault immediately!)
    add_step("e", "position startpos moves e2e4")
    add_step("e", "position startpos moves e2e4q e7e5 g1f3")
    add_step("e", "position startpos moves e2e4 e7e5 g1f3")
    add_step("e", "position startpos moves e2e4 e2e9 e7e5 g1f3")
    add_step("e", "position startpos moves e2e4 e7e5 g1f3 b8c6")

    for gi in range(60):
        fen, moves = games_60[gi]
        if len(moves) < 8:
            continue
        mid = min(len(moves) - 3, rng.randint(3, 15))
        other_fen, other_moves = games_60[(gi + 17) % 60]
        _ = other_fen
        bad_other = other_moves[-1] if other_moves else "a1a8"
        # 1. Move from another game in the middle, then continue past bad token
        add_step("e", f"position fen {fen} moves {' '.join(moves[:mid])} {bad_other} {' '.join(moves[mid:mid+3])}")
        add_step("e", f"position fen {fen} moves {' '.join(moves[:mid+3])}")
        # 2. "e2e9" in the middle, then continue past bad token
        add_step("e", f"position fen {fen} moves {' '.join(moves[:mid])} e2e9 {' '.join(moves[mid:mid+3])}")
        add_step("e", f"position fen {fen} moves {' '.join(moves[:mid+3])}")
        # 3. Spurious promotion letter ("e2e4q" and `<last_cached_move>q`), then continue past bad token
        add_step("e", f"position fen {fen} moves {' '.join(moves[:mid])}")
        spurious = moves[mid - 1][:4] + "q"
        add_step("e", f"position fen {fen} moves {' '.join(moves[:mid-1])} {spurious} {' '.join(moves[mid:mid+3])}")
        add_step("e", f"position fen {fen} moves {' '.join(moves[:mid])} e2e4q {' '.join(moves[mid:mid+2])}")
        add_step("e", f"position fen {fen} moves {' '.join(moves[:mid+3])}")

    # (f) FEN roots with 4 and with 5 fields.
    for gi in range(60):
        fen, moves = games_60[gi]
        parts = fen.split()
        fen4 = " ".join(parts[:4])
        fen5 = " ".join(parts[:5])
        k = min(len(moves), 6)
        add_step("f", f"position fen {fen4}")
        add_step("f", f"position fen {fen5}")
        add_step("f", f"position fen {fen4} moves {' '.join(moves[:k])}")
        add_step("f", f"position fen {fen5} moves {' '.join(moves[:k])}")

    # (g) ucinewgame between some commands.
    for gi in range(60):
        fen, moves = games_60[gi]
        k = min(len(moves), 10)
        add_step("g", f"position fen {fen} moves {' '.join(moves[:k])}")
        add_step("g", f"position startpos moves {' '.join(startpos_games[0][:min(8, len(startpos_games[0]))])}", pre_ucinewgame=True)
        add_step("g", f"position fen {fen} moves {' '.join(moves[:k])}", pre_ucinewgame=True)

    # (h) go lines for parse_limits_sv: depth, nodes, softnodes, searchmoves with 2..5 moves,
    #     one go line of > 32 tokens (wtime btime winc binc movestogo depth 6 and searchmoves of
    #     every legal move), and an unknown word between two known ones.
    # Find a high-mobility midgame position (>= 30 legal moves) so `wtime ... searchmoves <all>` has > 32 tokens!
    long_go_added = 0
    for gi in range(25):
        fen, moves = games_60[gi]
        k = min(len(moves), 6)
        pos_cmd = f"position fen {fen} moves {' '.join(moves[:k])}" if k > 0 else f"position fen {fen}"
        legals = query_legal_moves(engine_bin, pos_cmd)
        if len(legals) >= 2:
            # depth
            add_step("h", pos_cmd, pre_ucinewgame=True, extra_go=f"go depth {1 + (gi % 6)}")
            # nodes (including 0)
            ncap = 0 if gi == 0 else 100 + 50 * gi
            add_step("h", pos_cmd, pre_ucinewgame=True, extra_go=f"go nodes {ncap}")
            # softnodes
            add_step("h", pos_cmd, pre_ucinewgame=True, extra_go=f"go softnodes {150 + 40 * gi}")
            # searchmoves with 2 to 5 moves
            sm_cnt = min(len(legals), 2 + (gi % 4))
            sm_sub = rng.sample(legals, sm_cnt)
            add_step("h", pos_cmd, pre_ucinewgame=True, extra_go=f"go depth 5 searchmoves {' '.join(sm_sub)}")
            # unknown word between two known ones
            sm2 = legals[:min(3, len(legals))]
            unk_variants = [
                f"go depth 5 unknown_kw_alpha searchmoves {' '.join(sm2)}",
                "go wtime 100000000 bogus_middle_word btime 100000000 winc 1000 binc 1000 movestogo 20 depth 5",
                "go softnodes 400 mystery_token movestogo 12",
            ]
            add_step("h", pos_cmd, pre_ucinewgame=True, extra_go=unk_variants[gi % len(unk_variants)])
        if len(legals) >= 24 and long_go_added < 5:
            go_long = (
                "go wtime 100000000 btime 100000000 winc 1000 binc 1000 movestogo 20 depth 6 searchmoves "
                + " ".join(legals)
            )
            # Verify strictly > 32 tokens after "go"
            assert len(go_long.split()) - 1 > 32, f"Expected >32 tokens, got {len(go_long.split()) - 1}"
            add_step("h", pos_cmd, pre_ucinewgame=True, extra_go=go_long)
            long_go_added += 1

    assert long_go_added >= 1, "Must include at least one >32-token go line!"
    return steps, counts


def serialize_stream_blocks(steps: list[dict]) -> tuple[list[list[str]], dict[str, int]]:
    """
    Converts steps into synchronous UCI blocks. Each block is a list of UCI commands.
    If a command is a search `go ...` (not `go perft`), the driver waits for `bestmove` on it
    and then sends `isready` and waits for `readyok` before moving to the next block.
    """
    blocks: list[list[str]] = []
    probe_stats = {
        "position_commands": len(steps),
        "perft2_eval_probes": 0,
        "every_50th_depth6_probes": 0,
        "kind_h_go_probes": 0,
        "max_go_tokens_after_go": 0,
    }
    for idx1, st in enumerate(steps, start=1):
        if st["pre_ucinewgame"]:
            blocks.append(["ucinewgame", "isready"])
        blocks.append([st["pos_cmd"], "go perft 2", "eval", "isready"])
        probe_stats["perft2_eval_probes"] += 1

        if st["extra_go"] is not None:
            ntoks = len(st["extra_go"].split()) - 1
            if ntoks > probe_stats["max_go_tokens_after_go"]:
                probe_stats["max_go_tokens_after_go"] = ntoks
            blocks.append([st["extra_go"], "isready"])
            probe_stats["kind_h_go_probes"] += 1

        if idx1 % 50 == 0:
            # Forge's ucinewgame (src/uci.cpp:577) resets `board` to StandardStartFen in addition
            # to clearing TT/history, so on odd 50th steps we re-send st["pos_cmd"] after ucinewgame
            # to search that exact 50th position at depth 6 on cleared TT/history, and on even 50th
            # steps we run literal `ucinewgame` then `go depth 6` directly. Both exes get the exact
            # same stream file!
            if (idx1 // 50) % 2 == 1:
                blocks.append(["ucinewgame", "isready"])
                blocks.append([st["pos_cmd"], "isready"])
                blocks.append(["go depth 6", "isready"])
            else:
                blocks.append(["ucinewgame", "isready"])
                blocks.append(["go depth 6", "isready"])
            probe_stats["every_50th_depth6_probes"] += 1

    return blocks, probe_stats


def write_stream_file(blocks: list[list[str]], path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("w", encoding="utf-8") as f:
        for blk in blocks:
            for cmd in blk:
                f.write(cmd + "\n")
                h.update((cmd + "\n").encode("utf-8"))
            f.write("# --- END_BLOCK ---\n")
            h.update(b"# --- END_BLOCK ---\n")
    return h.hexdigest()


def run_stream_from_file(
    engine_bin: str,
    net512: str,
    stream_file: pathlib.Path,
    max_blocks: int | None = None,
) -> list[tuple[int, str, str]]:
    """
    Reads the single committed-script stream file block-by-block, sends each block to `engine_bin`
    loaded with PC20 + net512.fnn3 (Threads 1, Hash 16, OwnBook false), waiting for `bestmove`
    before `isready` on any search `go` and waiting for `readyok` at the end of every block.
    Returns list of `(block_idx, raw_line, normalized_line)`.
    """
    proc = subprocess.Popen(
        [engine_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None

    cfg = ["uci\n"] + [f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS] + [
        f"setoption name NNUEArchFile value {net512}\n",
        "setoption name NNUEArch value true\n",
        "isready\n",
    ]
    send(proc, "".join(cfg))
    setup = wait_ready_collect(proc, check_errors=True)
    assert any("fdff70de72e4ca82" in ln for ln in setup), f"Bad net512 load in {engine_bin}: {setup}"

    out_lines: list[tuple[int, str, str]] = []
    cur_blk: list[str] = []
    blk_idx = 0

    with stream_file.open("r", encoding="utf-8") as sf:
        for raw in sf:
            ln = raw.rstrip("\r\n")
            if ln == "# --- END_BLOCK ---":
                blk_idx += 1
                # Execute cur_blk synchronously
                has_search_go = any(c.startswith("go ") and not c.startswith("go perft") for c in cur_blk)
                if has_search_go:
                    for c in cur_blk:
                        proc.stdin.write(c + "\n")
                        proc.stdin.flush()
                        if c.startswith("go ") and not c.startswith("go perft"):
                            while True:
                                oln = proc.stdout.readline()
                                if not oln:
                                    raise RuntimeError(f"EOF waiting for bestmove at block {blk_idx} in {engine_bin}")
                                r = oln.rstrip("\r\n")
                                out_lines.append((blk_idx, r, normalize_line(r)))
                                if r.startswith("bestmove "):
                                    break
                        elif c == "isready":
                            while True:
                                oln = proc.stdout.readline()
                                if not oln:
                                    raise RuntimeError(f"EOF waiting for readyok at block {blk_idx} in {engine_bin}")
                                r = oln.rstrip("\r\n")
                                out_lines.append((blk_idx, r, normalize_line(r)))
                                if r == "readyok":
                                    break
                else:
                    proc.stdin.write("\n".join(cur_blk) + "\n")
                    proc.stdin.flush()
                    while True:
                        oln = proc.stdout.readline()
                        if not oln:
                            raise RuntimeError(f"EOF waiting for readyok at block {blk_idx} in {engine_bin}")
                        r = oln.rstrip("\r\n")
                        out_lines.append((blk_idx, r, normalize_line(r)))
                        if r == "readyok":
                            break
                cur_blk.clear()
                if max_blocks is not None and blk_idx >= max_blocks:
                    break
            else:
                cur_blk.append(ln)

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    _, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"{engine_bin} exited with {proc.returncode}: {err}")
    return out_lines


def main() -> int:
    t0 = time.time()
    plain_r15d = "/tmp/carbon2_job15/bld_plain_r15d/forge"
    plain_cur = "/tmp/carbon2_job15/bld_plain_curated/forge"
    plain_flt = "/tmp/carbon2_job15/bld_plain_curated_fault/forge"
    net768 = "/tmp/carbon2_work/net768.fnn3"
    net512 = "/tmp/carbon2_work/net512.fnn3"
    pos250 = REPO / "forge-combo29/carbon2/positions_250.txt"
    stream_file = pathlib.Path("/tmp/carbon2_job15/protocol_stream.txt")

    print("Collecting 60 self-play driver games...", flush=True)
    games_60, startpos_games = collect_60_driver_games(plain_cur, net768, pos250)
    print(f"Collected 60 games ({sum(len(m) for _, m in games_60)} plies) + {len(startpos_games)} startpos games", flush=True)

    steps, counts = build_protocol_stream(plain_cur, games_60, startpos_games)
    blocks, probe_stats = serialize_stream_blocks(steps)
    stream_sha256 = write_stream_file(blocks, stream_file)
    print(
        f"Stream built: total_position_commands={len(steps)} blocks={len(blocks)} "
        f"sha256={stream_sha256} counts={counts}",
        flush=True,
    )

    print("Running full protocol stream on plain r15d...", flush=True)
    t_r1 = time.time()
    out_r15d = run_stream_from_file(plain_r15d, net512, stream_file)
    t_r2 = time.time()
    print(f"plain r15d finished in {t_r2 - t_r1:.2f}s ({len(out_r15d)} output lines)", flush=True)

    print("Running full protocol stream on plain curated...", flush=True)
    out_cur = run_stream_from_file(plain_cur, net512, stream_file)
    t_r3 = time.time()
    print(f"plain curated finished in {t_r3 - t_r2:.2f}s ({len(out_cur)} output lines)", flush=True)

    # Compare line-for-line
    min_len = min(len(out_r15d), len(out_cur))
    differ_count = abs(len(out_r15d) - len(out_cur))
    first_diff_clean = None
    for idx in range(min_len):
        if out_r15d[idx][2] != out_cur[idx][2]:
            differ_count += 1
            if first_diff_clean is None:
                first_diff_clean = (idx + 1, out_r15d[idx], out_cur[idx])

    # Run planted-fault scratch copy of curated on the exact same stream file!
    print("Running protocol stream on planted-fault scratch curated...", flush=True)
    out_flt = run_stream_from_file(plain_flt, net512, stream_file)
    flt_diff_count = abs(len(out_r15d) - len(out_flt))
    first_flt_diff = None
    for idx in range(min(len(out_r15d), len(out_flt))):
        if out_r15d[idx][2] != out_flt[idx][2]:
            flt_diff_count += 1
            if first_flt_diff is None:
                first_flt_diff = (idx + 1, out_r15d[idx], out_flt[idx])

    assert differ_count == 0, f"UNEXPECTED CLEAN DIFF: {first_diff_clean}"
    assert first_flt_diff is not None and flt_diff_count > 0, "Planted fault produced NO diff!"

    f_line_no, f_ref, f_got = first_flt_diff
    # Locate the exact command block in stream_file for context
    blk_target = f_got[0]
    blk_cmds: list[str] = []
    prev_blk_cmds: list[str] = []
    cur_c: list[str] = []
    b_i = 0
    with stream_file.open("r", encoding="utf-8") as sf:
        for raw in sf:
            s = raw.rstrip("\r\n")
            if s == "# --- END_BLOCK ---":
                b_i += 1
                if b_i == blk_target - 1:
                    prev_blk_cmds = list(cur_c)
                elif b_i == blk_target:
                    blk_cmds = list(cur_c)
                    break
                cur_c.clear()
            else:
                cur_c.append(s)

    report_lines = [
        "=== JOB 15 PART 1: PROTOCOL IDENTITY TEST OF 04_S7 (apply_position_sv, parse_limits_sv) ===",
        f"SEED: {SEED}",
        f"STREAM_FILE: {stream_file} (blocks={len(blocks)}, sha256={stream_sha256})",
        "BUILDS: plain no-PGO -O3 -DNDEBUG -march=sapphirerapids ThinLTO + 6 speed switches, PC20 + net512.fnn3 (Threads 1, Hash 16)",
        "",
        "--- 1. Position Commands Sent Per Kind (a) to (h) ---",
        f"  (a) growing prefixes (startpos & fen roots across 60 SP games + 2 startpos SP games): {counts['a']}",
        f"  (b) shrinking prefixes & seeded-random-order prefixes (seed {SEED}):                  {counts['b']}",
        f"  (c) root changing between commands (game A -> game B -> game A):                      {counts['c']}",
        f"  (d) non-canonical whitespace (two spaces, tabs, trailing ws, empty 'moves'):          {counts['d']}",
        f"  (e) mid-list illegal move (other-game move, 'e2e9', 'e2e4q') + continuation past it:  {counts['e']}",
        f"  (f) 4-field and 5-field FEN roots (bare and with moves):                              {counts['f']}",
        f"  (g) ucinewgame interleaved between position commands:                                 {counts['g']}",
        f"  (h) parse_limits_sv go lines (depth, nodes, softnodes, searchmoves 2..5, >32 tokens, unknown word): {counts['h']}",
        f"  TOTAL_POSITION_COMMANDS: {sum(counts.values())} (requirement: >= 20000)",
        "",
        "--- 2. Probes Executed ---",
        f"  per_position_probes (go perft 2 + eval + isready): {probe_stats['perft2_eval_probes']}",
        f"  every_50th_probes   (ucinewgame + go depth 6 + isready): {probe_stats['every_50th_depth6_probes']}",
        f"  kind_h_go_probes    (depth/nodes/softnodes/searchmoves/>32-tok/unknown-word + isready): {probe_stats['kind_h_go_probes']} (max tokens after 'go' = {probe_stats['max_go_tokens_after_go']})",
        "",
        "--- 3. Line-for-Line Comparison: plain r15d vs plain curated (time, nps, hashfull stripped) ---",
        f"  r15d_emitted_lines:    {len(out_r15d)}",
        f"  curated_emitted_lines: {len(out_cur)}",
        f"  lines_compared:        {len(out_r15d)}",
        f"  lines_that_differ:     {differ_count}",
        "",
        "--- 4. Planted Fault Check (part1_s7_ws_planted_fault.patch.txt: moves_sv[canon.size()] whitespace check removed) ---",
        f"  fault_emitted_lines:   {len(out_flt)}",
        f"  total_differing_lines: {flt_diff_count}",
        f"  first_diff_line_index: {f_line_no} (in block #{blk_target})",
        f"  previous_block_pos:    {prev_blk_cmds[0] if prev_blk_cmds else ''}",
        f"  faulting_block_pos:    {blk_cmds[0] if blk_cmds else ''}",
        f"  FIRST_DIFFERING_LINE_EXPECTED (r15d & clean curated): {f_ref[1]}",
        f"  FIRST_DIFFERING_LINE_PLANTED_FAULT (curated_fault):   {f_got[1]}",
        f"  elapsed_total_sec:     {time.time() - t0:.2f}",
    ]
    out_text = "\n".join(report_lines) + "\n"
    out_path = REPO / "forge-combo29/carbon2/job15/part1_protocol_identity_raw.txt"
    out_path.write_text(out_text, encoding="utf-8")
    print(out_text, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
