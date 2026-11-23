"""Fable 2026-11-23, W5 with A14 of FINAL_PLAN_2311.md, the HOME side: the credited games of the receiver become
the loop's own text, through the loop's OWN after-game function (the rules that correct a drawn game's result
with the endgame tables, and the rule that leaves out a ply-limit game with a one-sided score).

    to_round.py --state <the receiver's state> --manifest MANIFEST.json --config <the loop's config>
                --pipeline <folder that holds nnloop> --out <NEW folder>

The PC applies these rules, not the server (the decision of teamwork/W5_PLAN_by_fable.md): the server needs no
tables, and here a run STOPS (exit code 4) when the config asks for the tables and they do not open; the loop's
own driver would only write a note and go on with plain draws.
For every credited game, in the order of the pieces: the record is read from state/raw, the engine's lines are
turned into exactly what the loop's `play_game_sg` hands to `_after_game` (pipeline/nnloop/datagen_uci.py), and
its text is appended to <out>/games.plain. <out>/report.json counts games and rows in and out, the games by
the way they ended, the relabelled and the left-out games.
It refuses (exit code 2) a config whose game settings are not the manifest's frozen game line.
Not done here: cutting the text into the PC's rounds (the filter's repeated-position rule needs their
boundaries; the plan's W5 (e), last sentence).
Exit codes: 0; 2 wrong call or settings that do not fit; 3 a credited game that is not in state/raw; 4 no tables.
"""
import argparse
import json
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent.parent / "run"
sys.path.insert(0, str(RUN))
import record  # noqa: E402


def loop_args(g_rec: dict, g: dict, chess):
    """What play_game_sg hands to _after_game for this game: (board, recs, result, ended_by_limit,
    draw_adjudicated, plies). Written from the loop's lines 394 to 453, not shared with them."""
    board = chess.Board()
    for m in g_rec["opening"]:
        board.push_uci(m)
    recs = []
    for row in g_rec["rows"]:
        _, ply, score, bm, fen = row.split(" ", 4)
        recs.append((fen, bm, int(score), int(ply), fen.split(" ", 2)[1] == "w"))
    f = g_rec["end"].split()
    i = f.index("moves")
    keys = ("result", "reason", "plies", "run", "searches", "nodes")
    end = {f[j]: f[j + 1] for j in range(1, i - 1) if f[j] in keys}
    result, reason, plies = int(end["result"]), end["reason"], int(end["plies"])
    if result == 0 and (g.get("adjudicate_bare_king", False) or g.get("adjudicate_tablebase", False)):
        for m in f[i + 1:]:
            mv = chess.Move.from_uci(m)
            if not board.is_legal(mv):
                raise ValueError(f"illegal move {m} in the end line of {g_rec['id']}")
            board.push(mv)
    return board, recs, result, reason == "plylimit", reason == "drawadj" and int(g["draw_adj_count"]) > 0, plies, reason


def game_line_of(g: dict) -> str:
    """The loop's own game command for these settings (datagen_uci.py 414 to 416), to compare with the manifest."""
    return (f"selfgame softnodes {int(g['soft_nodes'])} evallimit {int(g['eval_limit'])} maxply {int(g['max_ply'])} "
            f"writeminply {int(g['write_min_ply'])} drawply {int(g['draw_adj_ply'])} "
            f"drawscore {int(g['draw_adj_score'])} drawcount {int(g['draw_adj_count'])}")


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("state", "manifest", "config", "pipeline", "out"):
        ap.add_argument("--" + name, required=True)
    a = ap.parse_args()
    state, out = Path(a.state), Path(a.out)
    if out.exists() or not (state / "credited.jsonl").exists():
        print("STOP: --out must be a NEW folder and --state a receiver's state with a ledger")
        return 2
    sys.path.insert(0, str(Path(a.pipeline).resolve()))
    import chess
    from nnloop import datagen_uci
    from nnloop.common import load_config
    g = load_config(Path(a.config))["datagen"]
    frozen = json.loads(Path(a.manifest).read_text(encoding="ascii"))["selfgame_line"]
    if game_line_of(g) != frozen:
        print(f"STOP: the config's game settings give `{game_line_of(g)}`, the manifest froze `{frozen}`")
        return 2
    if g.get("adjudicate_tablebase", False) and datagen_uci._tablebase(g) is None:
        print(f"STOP: the endgame tables did not open ({datagen_uci.TB_NOTE}); no game is written with a result that was not checked")
        return 4
    credited = [json.loads(x) for x in (state / "credited.jsonl").read_text(encoding="ascii").splitlines()]
    want = {c["id"]: c for c in credited}
    out.mkdir(parents=True)
    rep = {"games_in": 0, "rows_in": 0, "games_written": 0, "rows_written": 0, "relabelled": 0, "left_out_by_ply_limit_rule": 0,
           "by_ending": {}, "relabelled_ids": [], "left_out_ids": []}
    seen = set()
    with open(out / "games.plain", "wb") as f:
        for piece in sorted({c["piece"] for c in credited}):
            raw = state / "raw" / (piece + ".raw")
            if not raw.exists():
                print(f"STOP: {raw} is missing although the ledger credits games of it")
                return 3
            for rec in record.parse(raw.read_bytes()):
                c = want.get(rec["id"])
                if c is None or c["piece"] != piece or rec["id"] in seen:
                    continue
                seen.add(rec["id"])
                board, recs, result, by_limit, draw_adj, plies, reason = loop_args(rec, g, chess)
                text, n, _result, _plies = datagen_uci._after_game(board, recs, result, by_limit, draw_adj, plies, g)
                rep["games_in"] += 1
                rep["rows_in"] += len(recs)
                rep["by_ending"][reason] = rep["by_ending"].get(reason, 0) + 1
                if datagen_uci.LAST_ADJ is not None:
                    rep["relabelled"] += 1
                    rep["relabelled_ids"].append(rec["id"])
                if datagen_uci.LAST_SKIP is not None:
                    rep["left_out_by_ply_limit_rule"] += 1
                    rep["left_out_ids"].append(rec["id"])
                if n:
                    rep["games_written"] += 1
                    rep["rows_written"] += n
                    f.write(text.encode("ascii"))
    missing = sorted(set(want) - seen)
    if missing:
        print(f"STOP: {len(missing)} credited games are not in state/raw, first {missing[0]}")
        return 3
    (out / "report.json").write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n", encoding="ascii")
    print(f"to_round: {rep['games_in']} games, {rep['rows_in']} rows in; {rep['games_written']} games, {rep['rows_written']} rows written; "
          f"{rep['relabelled']} relabelled, {rep['left_out_by_ply_limit_rule']} left out; by ending {rep['by_ending']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
