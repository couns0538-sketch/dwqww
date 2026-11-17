"""Determinism matrix runner (swarm seat 69).

One cell = one engine invocation under a named environment variant, on one position,
with one fixed budget. The cell records the reported node count, bestmove, score and
depth. Comparing cells is the whole experiment: any input that changes those four
numbers is a harness trap.

A cell is REFUSED, never recorded as a measurement, when python-chess rejects the FEN
or the engine answers `invalid FEN` in either stream. A refused FEN would otherwise
give a perfectly reproducible node count for a different board.
"""

import argparse
import json
import os
import sys
import time

import chess

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
PC_EXE = "/home/ubuntu/builds/pc-build/forge"


def cell_key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def run_cell(exe, fen, go_cmd, options, prefix=None, cwd=None, env=None, timeout=180.0,
             engine=None):
    """Run one cell. `prefix` is an argv prefix (taskset/nice/bash -c 'ulimit ...').

    `engine` is an already-open ucih.Engine reused across cells (the TT-reuse cases);
    when it is None a fresh process is started and closed.
    """
    owned = engine is None
    eng = engine if engine is not None else ucih.Engine(
        exe, cwd=cwd, env=env, timeout=timeout, prefix=prefix)
    try:
        if not eng.name:
            eng.uci()
            for name, value in options:
                eng.setoption(name, value)
        if fen is None:
            eng.position_startpos()
        else:
            try:
                chess.Board(fen)
            except Exception as exc:  # noqa: BLE001
                raise ucih.EngineError("python-chess rejects FEN: %s" % exc)
            eng.position_fen(fen)
        return eng.go(go_cmd)
    finally:
        if owned:
            eng.close()


def summarize(res):
    return {
        "nodes": res["nodes"],
        "bestmove": res["bestmove"],
        "score": res["score"],
        "depth": res["depth"],
        "n_info": res["n_info"],
    }
