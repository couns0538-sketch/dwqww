#!/usr/bin/env python3
"""
Job 40 PGN Converter & Per-Game List Recounter (`recount_pgn.py`):
1. `pgn_to_games_tsv`: Reads temporary `fastchess` PGN from `/tmp/carbon2_job40/` (never committed)
   and writes the committed per-game list `<tag>_games.tsv` with one line per finished game:
     `white\tblack\tresult\tplies\ttermination\topening_fen`
2. `recount_games_tsv`: Reads ONLY the committed `<tag>_games.tsv` (and compares opening FENs
   against `UHO_Lichess_4852_v1.epd` lines `start_line..end_line` and final numbers against
   `<tag>_fastchess.txt`), computing exact `W-L-D`, `pentanomial [LL, LD, WL+DD, WD, WW]`,
   `Elo`, `95% CI`, `nElo`, and `LOS %`.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys
from typing import Optional

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j40_lib import compute_pentanomial_elo, fmt_cmp, sha256_file, utc_now  # noqa: E402

HEADER_RE = re.compile(r'^\[([A-Za-z0-9_]+)\s+"((?:\\.|[^"\\])*)"\]\s*$')


def normalize_fen4(fen: str) -> str:
    return " ".join(fen.strip().split()[:4])


def parse_pgn_games(pgn_path: pathlib.Path) -> list[dict[str, str | int]]:
    games: list[dict[str, str | int]] = []
    if not pgn_path.exists():
        return games

    cur_headers: dict[str, str] = {}
    in_headers = False

    def flush_game() -> None:
        nonlocal cur_headers
        if not cur_headers:
            return
        res = cur_headers.get("Result", "*")
        if res in ("1-0", "0-1", "1/2-1/2"):
            games.append(
                {
                    "round": int(cur_headers.get("Round", "0")),
                    "game_id": int(cur_headers.get("GameId", "0")),
                    "white": cur_headers["White"],
                    "black": cur_headers["Black"],
                    "result": res,
                    "plies": int(cur_headers.get("PlyCount", "0")),
                    "termination": cur_headers.get("Termination", "normal"),
                    "fen": cur_headers.get("FEN", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
                }
            )
        cur_headers = {}

    with open(pgn_path, "r", encoding="utf-8", errors="replace") as f:
        for raw_ln in f:
            ln = raw_ln.strip()
            m = HEADER_RE.match(ln)
            if m:
                if not in_headers and cur_headers:
                    flush_game()
                in_headers = True
                k, v = m.group(1), m.group(2).replace('\\"', '"')
                cur_headers[k] = v
            elif ln == "":
                if in_headers:
                    in_headers = False
            else:
                in_headers = False
        if cur_headers:
            flush_game()

    return games


def pgn_to_games_tsv(
    pgn_path: pathlib.Path,
    out_tsv: pathlib.Path,
    engine1: str,
    engine2: str,
) -> int:
    games = parse_pgn_games(pgn_path)
    # Sort deterministically by (round, 0 if white == engine1 else 1, game_id)
    # so the two games of every completed opening round appear consecutively.
    games.sort(key=lambda g: (int(g["round"]), 0 if g["white"] == engine1 else 1, int(g["game_id"])))
    lines = [
        "# white\tblack\tresult\tplies\ttermination\topening_fen",
    ]
    for g in games:
        w = str(g["white"])
        b = str(g["black"])
        assert {w, b} == {engine1, engine2}, f"Unexpected engine names: {w!r} vs {b!r}"
        lines.append(
            f"{w}\t{b}\t{g['result']}\t{g['plies']}\t{g['termination']}\t{g['fen']}"
        )
    out_tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(games)


def load_book_slice(book_path: pathlib.Path, start_1based: int, count: int) -> list[str]:
    out: list[str] = []
    end_1based = start_1based + count - 1
    with open(book_path, "r", encoding="utf-8") as bf:
        for idx, raw in enumerate(bf, start=1):
            if idx < start_1based:
                continue
            if idx > end_1based:
                break
            s = raw.strip()
            if ";" in s:
                s = s.split(";", 1)[0].strip()
            out.append(s)
    return out


def parse_fastchess_final_stats(fc_txt_path: pathlib.Path, engine1: str, engine2: str) -> Optional[dict]:
    """
    Extracts the LAST `Results of <engine1> vs <engine2>` (fastchess 1.8+) or
    `Score of <engine1> vs <engine2>:` block printed by `fastchess`.
    """
    txt = fc_txt_path.read_text(encoding="utf-8", errors="replace")
    res_hdr_pat = re.compile(rf"^Results of {re.escape(engine1)} vs {re.escape(engine2)}\b")
    elo_line_pat = re.compile(
        r"^Elo:\s*([+-]?[0-9.]+|inf|-inf)\s*\+/-\s*([0-9.]+|inf|nan),\s*nElo:\s*([+-]?[0-9.]+|inf|-inf)\s*\+/-\s*([0-9.]+|inf|nan)"
    )
    games_line_pat = re.compile(
        r"^Games:\s*(\d+),\s*Wins:\s*(\d+),\s*Losses:\s*(\d+),\s*Draws:\s*(\d+),\s*Points:\s*([0-9.]+)\s*\(([0-9.]+)\s*%\)"
    )
    penta_pat = re.compile(r"Ptnml\(0-2\):\s*\[\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\]")

    lines = txt.splitlines()
    last: Optional[dict] = None
    for i, ln in enumerate(lines):
        s_ln = ln.strip()
        if res_hdr_pat.search(s_ln):
            elo_val: Optional[float] = None
            elo_err: Optional[float] = None
            nelo_val: Optional[float] = None
            nelo_err: Optional[float] = None
            tot = w = l = d = None
            pct_s = 0.0
            penta: Optional[list[int]] = None
            games_raw = ""
            elo_raw = ""
            penta_raw = ""
            for j in range(i + 1, min(i + 10, len(lines))):
                sub = lines[j].strip()
                if res_hdr_pat.search(sub):
                    break
                me = elo_line_pat.search(sub)
                if me:
                    elo_val = float(me.group(1))
                    elo_err = float(me.group(2))
                    nelo_val = float(me.group(3))
                    nelo_err = float(me.group(4))
                    elo_raw = sub
                mg = games_line_pat.search(sub)
                if mg:
                    tot = int(mg.group(1))
                    w = int(mg.group(2))
                    l = int(mg.group(3))
                    d = int(mg.group(4))
                    pct_s = float(mg.group(6))
                    games_raw = sub
                mp = penta_pat.search(sub)
                if mp:
                    penta = [int(mp.group(k)) for k in range(1, 6)]
                    penta_raw = sub
            if tot is not None and w is not None and l is not None and d is not None:
                last = {
                    "w": w,
                    "l": l,
                    "d": d,
                    "total": tot,
                    "pct": pct_s,
                    "elo": elo_val,
                    "err95": elo_err,
                    "nelo": nelo_val,
                    "nelo_err95": nelo_err,
                    "ptnml": penta,
                    "raw_score_line": f"{games_raw} | {elo_raw} | {penta_raw}",
                }
    return last


def pts_for_engine1(white: str, black: str, result: str, engine1: str) -> int:
    """Returns half-points (`0`, `1`, or `2`) scored by `engine1` in a single game."""
    if result == "1/2-1/2":
        return 1
    if result == "1-0":
        return 2 if white == engine1 else 0
    if result == "0-1":
        return 2 if black == engine1 else 0
    raise ValueError(f"Unexpected result {result!r}")


def recount_games_tsv(
    tag: str,
    tsv_path: pathlib.Path,
    fc_txt_path: pathlib.Path,
    out_recount_path: pathlib.Path,
    engine1: str,
    engine2: str,
    book_path: pathlib.Path,
    start_line: int,
    target_rounds: int,
    was_cut: bool,
) -> dict:
    rows: list[tuple[str, str, str, int, str, str]] = []
    for ln in tsv_path.read_text(encoding="utf-8").splitlines():
        if not ln or ln.startswith("#"):
            continue
        w, b, res, plies_s, term, fen = ln.split("\t")
        rows.append((w, b, res, int(plies_s), term, fen))

    w_cnt = 0
    l_cnt = 0
    d_cnt = 0
    non_normal_terms = 0
    total_plies = 0
    for w, b, res, plies, term, _fen in rows:
        hp = pts_for_engine1(w, b, res, engine1)
        if hp == 2:
            w_cnt += 1
        elif hp == 1:
            d_cnt += 1
        else:
            l_cnt += 1
        if term != "normal":
            non_normal_terms += 1
        total_plies += plies

    # Group pairs sequentially from the sorted per-game list
    ptnml = [0, 0, 0, 0, 0]  # [LL, LD, WL+DD, WD, WW] (0, 1, 2, 3, 4 half-points for engine1)
    pair_fens4: list[str] = []
    unpaired_games = 0
    idx = 0
    while idx < len(rows):
        if idx + 1 < len(rows):
            g1 = rows[idx]
            g2 = rows[idx + 1]
            if normalize_fen4(g1[5]) == normalize_fen4(g2[5]) and {g1[0], g2[0]} == {engine1, engine2}:
                hp_sum = pts_for_engine1(g1[0], g1[1], g1[2], engine1) + pts_for_engine1(g2[0], g2[1], g2[2], engine1)
                ptnml[hp_sum] += 1
                pair_fens4.append(normalize_fen4(g1[5]))
                idx += 2
                continue
        unpaired_games += 1
        idx += 1

    book_slice = load_book_slice(book_path, start_line, target_rounds)
    book_fens4 = [normalize_fen4(s) for s in book_slice]
    if not was_cut:
        book_matches = sum(1 for a, b in zip(pair_fens4, book_fens4) if a == b)
        exp_book_matches = target_rounds
    else:
        book_set = set(book_fens4)
        book_matches = sum(1 for a in pair_fens4 if a in book_set)
        exp_book_matches = len(pair_fens4)

    est = compute_pentanomial_elo(ptnml)
    fc = parse_fastchess_final_stats(fc_txt_path, engine1, engine2)

    all_ok = True
    checks: list[str] = []

    ok_term, s_term = fmt_cmp(f"{tag} non-normal terminations", non_normal_terms, 0)
    all_ok = all_ok and ok_term
    checks.append(s_term)

    ok_bk, s_bk = fmt_cmp(f"{tag} opening FEN pairs matching book slice", book_matches, exp_book_matches)
    all_ok = all_ok and ok_bk
    checks.append(s_bk)

    if not was_cut:
        ok_g, s_g = fmt_cmp(f"{tag} finished games vs target", len(rows), target_rounds * 2)
        ok_p, s_p = fmt_cmp(f"{tag} finished pairs vs target", sum(ptnml), target_rounds)
        all_ok = all_ok and ok_g and ok_p
        checks.extend([s_g, s_p])

    if fc is not None and fc["total"] == len(rows):
        ok_w, s_w = fmt_cmp(f"{tag} recount W vs fastchess", w_cnt, fc["w"])
        ok_l, s_l = fmt_cmp(f"{tag} recount L vs fastchess", l_cnt, fc["l"])
        ok_d, s_d = fmt_cmp(f"{tag} recount D vs fastchess", d_cnt, fc["d"])
        all_ok = all_ok and ok_w and ok_l and ok_d
        checks.extend([s_w, s_l, s_d])
        if fc["ptnml"] is not None:
            ok_pt, s_pt = fmt_cmp(f"{tag} recount ptnml vs fastchess", ptnml, fc["ptnml"])
            all_ok = all_ok and ok_pt
            checks.append(s_pt)
        if fc["elo"] is not None and fc["err95"] is not None:
            ok_el, s_el = fmt_cmp(f"{tag} recount Elo vs fastchess", f"{est['elo']:+.2f}", f"{fc['elo']:+.2f}")
            ok_er, s_er = fmt_cmp(f"{tag} recount +/-95% vs fastchess", f"{est['err95']:.2f}", f"{fc['err95']:.2f}")
            all_ok = all_ok and ok_el and ok_er
            checks.extend([s_el, s_er])

    status_str = "CUT" if was_cut else "COMPLETE"
    mean_plies = (total_plies / len(rows)) if rows else 0.0
    lines = [
        f"=== {tag} RECOUNT FROM PER-GAME LIST ({status_str}) ===",
        f"games_tsv_path: {tsv_path}",
        f"games_tsv_sha256({tsv_path}): {sha256_file(tsv_path)}",
        f"fastchess_stdout_path: {fc_txt_path}",
        f"fastchess_stdout_sha256({fc_txt_path}): {sha256_file(fc_txt_path)}",
        f"book_slice: {book_path} lines {start_line}..{start_line + target_rounds - 1} ({target_rounds} openings)",
        f"status: {status_str}",
        f"engines: {engine1} vs {engine2}",
        f"games_finished: {len(rows)} (unpaired={unpaired_games}, mean_plies={mean_plies:.2f})",
        f"recounted_WLD ({engine1} vs {engine2}): {w_cnt} - {l_cnt} - {d_cnt} (score={est['score']:.6f})",
        f"recounted_pentanomial [LL, LD, WL+DD, WD, WW]: {ptnml} (pairs={sum(ptnml)})",
        f"recounted_Elo: {est['elo']:+.2f} +/- {est['err95']:.2f} (95% CI [{est['ci_low']:+.2f}, {est['ci_high']:+.2f}]; exact [{est['exact_ci_low']:+.2f}, {est['exact_ci_high']:+.2f}])",
        f"recounted_nElo: {est['nelo']:+.2f} +/- {est['nelo_err95']:.2f} | LOS: {est['los_pct']:.2f}%",
        f"fastchess_own_line: {fc['raw_score_line'] if fc else '<none>'}",
        f"fastchess_own_elo_ptnml: Elo={fc['elo']:+.2f} +/- {fc['err95']:.2f}, Ptnml={fc['ptnml']}"
        if (fc and fc["elo"] is not None)
        else "fastchess_own_elo_ptnml: <partial/cut>",
        "checks:",
        *checks,
        f"utc_recounted: {utc_now()}",
    ]
    out_recount_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    return {
        "tag": tag,
        "status": status_str,
        "games": len(rows),
        "w": w_cnt,
        "l": l_cnt,
        "d": d_cnt,
        "ptnml": ptnml,
        "pairs": sum(ptnml),
        "elo": float(est["elo"]),
        "err95": float(est["err95"]),
        "ci_low": float(est["ci_low"]),
        "ci_high": float(est["ci_high"]),
        "all_ok": all_ok,
    }
