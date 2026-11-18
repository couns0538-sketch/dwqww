#!/usr/bin/env python3
"""Capture the unchanged hard-budget UCI response at book line 2197, ply 57."""

from contextlib import contextmanager
from pathlib import Path
import sys

import chess

from compare_games34 import position
from whole_games34 import Engine, NODES_FIELD, settings, utc_now


ROOT = Path(__file__).resolve().parent
BOOK_LINE, TARGET_PLY = 2197, 57
SEARCH = "go nodes 2000"
TARGET_REPLY = ["bestmove c6c5"]


@contextmanager
def start(build, attempt, net, output):
    with (output / f"{build}-{attempt}.uci.txt").open("x", encoding="utf-8") as script, \
            (output / f"{build}-{attempt}.out.txt").open("x", encoding="utf-8") as terminal, \
            Engine(ROOT / build / "forge", 15) as engine:
        def send(line, expect=None):
            script.write(line + "\n")
            terminal.write(f"> {line}\n")
            engine.send(line)
            if expect is not None:
                reply = engine.until(expect)
                terminal.writelines(f"< {line}\n" for line in reply)
                return reply
            return []

        send("uci", "uciok")
        for name, value in settings(net, 93):
            send(f"setoption name {name} value {value}")
        setup = send("isready", "readyok")
        for state in ("loaded", "active"):
            assert any(line.startswith(f"info string NNUE v3 {state}:") and "checksum 30ab43b4ba5db5f3" in line
                       for line in setup), (build, attempt, state)
        yield send
        script.write("quit\n")
        terminal.write("> quit\n")


def reset(send):
    send("ucinewgame")
    send("isready", "readyok")


def search(send, fen, moves):
    send(position(fen, moves))
    return send(SEARCH, "bestmove")


def last_result(reply):
    info = next((line for line in reversed(reply) if line.startswith("info ")), "")
    values = NODES_FIELD.findall(info)
    return reply[-1].split()[1], int(values[0]) if len(values) == 1 else None


def dynamic_prefix(send, fen):
    reset(send)
    board = chess.Board(fen)
    moves = []
    for _ in range(TARGET_PLY):
        assert not board.is_game_over(claim_draw=True)
        reply = search(send, fen, moves)
        move, nodes = last_result(reply)
        assert nodes is not None, (len(moves), reply)
        board.push_uci(move)
        moves.append(move)
    assert not board.is_game_over(claim_draw=True)
    return moves, search(send, fen, moves)


def reproduce_preceding_games(send, build, book):
    game = None
    moves = []
    for row in (ROOT / "raw" / f"T2-{build}.records.txt").read_text().splitlines():
        number, ply, move, nodes = row.split()
        number = int(number)
        if number != game:
            game, moves = number, []
            reset(send)
        assert int(ply) == len(moves)
        assert last_result(search(send, book[game], moves)) == (move, int(nodes)), row
        moves.append(move)


def main():
    book_path, net, output = map(Path, sys.argv[1:])
    with book_path.open() as source:
        book = {index: line.strip() for index, line in zip(range(1, BOOK_LINE + 1), source)}
    net = net.resolve(strict=True)
    output.mkdir(parents=True, exist_ok=True)
    fen = book[BOOK_LINE]
    with (output / "result.txt").open("x", encoding="utf-8") as report:
        report.write(f"{utc_now()} Diagnostic, unchanged {SEARCH}. Book line {BOOK_LINE}, zero-based ply {TARGET_PLY}.\n")
        for build in ("r15d", "kF"):
            with start(build, "fresh-game", net, output) as send:
                moves, reply = dynamic_prefix(send, fen)
            report.write(f"{build} fresh game exact target reply {reply!r}.\n")
            if reply != TARGET_REPLY:
                with start(build, "prior-games", net, output) as send:
                    reproduce_preceding_games(send, build, book)
                    moves, reply = dynamic_prefix(send, fen)
                report.write(f"{build} after exact preceding-game records target reply {reply!r}.\n")
            assert reply == TARGET_REPLY, (build, reply)
            report.write(f"{build} original FEN {fen}\n{build} preceding moves {' '.join(moves)}\n")

            board = chess.Board(fen)
            for move in moves:
                board.push_uci(move)
            assert chess.Move.from_uci("c6c5") in board.legal_moves
            report.write(f"{build} reached FEN {board.fen(en_passant='fen')}\n")
            for attempt, replay_fen, replay_moves in (
                ("target-fen", board.fen(en_passant="fen"), []),
                ("target-with-history", fen, moves),
            ):
                with start(build, attempt, net, output) as send:
                    reset(send)
                    response = search(send, replay_fen, replay_moves)
                report.write(f"{build} {attempt}: {response!r}.\n")
                if response == TARGET_REPLY:
                    break
            report.flush()
    print((output / "result.txt").read_text(), end="")


if __name__ == "__main__":
    main()
