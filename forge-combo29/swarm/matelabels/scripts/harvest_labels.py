#!/usr/bin/env python3
"""Harvest mate-labelled positions from the repo's own search corpus.

Sampling frame: the engine's OWN mate labels at a fixed, recorded configuration.
That is the population the finding is about -- "a label the engine emits" -- and
it is the only population a length filter is ever applied to.

Every row records the engine build, the full option set, the depth, the score,
the PV, and the node count, so no row is a number without its provenance.
"""
import json
import os
import random
import sys
import time

sys.path.insert(0, "/tmp/fw")
import chess
import uci

ENGINE = "/tmp/fw/base/forge-combo29/build/forge"
CORPUS = "/tmp/fw/base/forge-combo29/soak_all/search_corpus.txt"
TARGET = 300

# The configuration under test. Identical to the depth-12 boards in findings S4.
OPTIONS = {
    "Hash": 32,
    "Threads": 1,
    "MultiPV": 1,
    "OwnBook": "false",
    "UseNNUE": "true",
    "Ponder": "false",
}
DEPTH = 12
SEED = 20261117


def load_corpus():
    fens = []
    with open(CORPUS) as f:
        for line in f:
            line = line.strip()
            if line:
                fens.append(line)
    return fens


def pv_length_ok(mate_value, pv_len):
    """Findings section 4 filter: 2|N|-1 for a win, 2|N| for a loss."""
    n = abs(mate_value)
    want = 2 * n - 1 if mate_value > 0 else 2 * n
    return pv_len == want, want


def main():
    fens = load_corpus()
    rng = random.Random(SEED)
    rng.shuffle(fens)
    print(f"corpus {len(fens)} positions, target {TARGET} mate labels", flush=True)

    out_path = "/tmp/fw/harvest.jsonl"
    done = 0
    if os.path.exists(out_path):
        with open(out_path) as f:
            done = sum(1 for _ in f)
        print(f"resuming, {done} rows already present", flush=True)

    kept = done
    scanned = 0
    skipped_refused = 0
    skipped_invalid = 0
    t0 = time.time()

    with open(out_path, "a") as out:
        for fen in fens:
            if kept >= TARGET:
                break
            scanned += 1

            # Rule 4: python-chess first. An illegal fixture manufactures a pass.
            board = chess.Board(fen)
            if not board.is_valid():
                skipped_invalid += 1
                continue
            if board.is_game_over():
                continue

            e = uci.Uci(ENGINE, OPTIONS)
            e.position(fen)
            best, info, elapsed, timed_out = e.search(f"go depth {DEPTH}", timeout=120)
            refused = any("invalid FEN" in l for l in e.stderr_lines) or any(
                "invalid FEN" in l for l in info
            )
            e.quit()

            if refused:
                skipped_refused += 1
                print(f"  ENGINE REFUSED a python-chess-valid FEN: {fen}", flush=True)
                continue
            if timed_out or not info:
                continue

            last = uci.last_score_per_multipv(info)
            cand = [v for v in last.values() if v["multipv"] == 1]
            if not cand:
                continue
            v = cand[0]
            if v["kind"] != "mate" or v["value"] == 0:
                continue

            pv = v["pv"]
            ok, want = pv_length_ok(v["value"], len(pv))

            # Replay the PV with python-chess: the filter's premise is that the
            # PV is legal. Record whether it is.
            replay = chess.Board(fen)
            legal_pv = True
            for mv in pv:
                try:
                    replay.push_uci(mv)
                except ValueError:
                    legal_pv = False
                    break
            ends_in_mate = replay.is_checkmate()

            row = {
                "id": f"H{kept:04d}",
                "fen": fen,
                "engine_sha256": "e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83",
                "engine_id": "Chess Engine Forge 6.4.24 candidate",
                "base_commit": "6b98f2170a3210e71beed04bbd2553972c253ed7",
                "options": OPTIONS,
                "depth": v["depth"],
                "bestmove": best,
                "score_kind": v["kind"],
                "score_value": v["value"],
                "nodes": v["nodes"],
                "pv": pv,
                "pv_len": len(pv),
                "pv_len_filter_pass": ok,
                "pv_len_wanted": want,
                "pv_legal": legal_pv,
                "pv_ends_in_mate": ends_in_mate,
                "elapsed_s": round(elapsed, 3),
                "side_to_move": "w" if board.turn == chess.WHITE else "b",
            }
            out.write(json.dumps(row) + "\n")
            out.flush()
            kept += 1
            if kept % 20 == 0:
                rate = kept / scanned
                eta = (TARGET - kept) / max(rate, 1e-9) * (time.time() - t0) / max(scanned, 1)
                print(f"  {kept}/{TARGET}  scanned {scanned}  rate {rate:.3f}  "
                      f"wall {time.time()-t0:.0f}s  eta {eta:.0f}s", flush=True)

    print(f"\nkept {kept}  scanned {scanned}  refused {skipped_refused}  invalid {skipped_invalid}")
    print(f"harvest rate {kept/max(scanned,1):.4f}  wall {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
