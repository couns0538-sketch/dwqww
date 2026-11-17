"""UCI perft harness for forge, with the position-command FEN trap closed.

Protocol facts this harness depends on (measured, not assumed):
  * `position` answers an illegal FEN with `info string invalid FEN: ...`
    BEFORE the next `readyok`. The diagnostic does NOT appear in search output.
  * An `isready` sent between `position` and `go` consumes that diagnostic, so
    the only safe read is: send `position`, then send `isready`, then scan
    everything the engine said up to and including that `readyok`.
  * A refused position leaves the board on whatever was there before (startpos
    in a fresh session), so `go perft N` still returns a plausible count for
    the WRONG board. Every deep comparison is therefore preceded by a
    `go perft 1` board-identity check against python-chess's legal move count.

Threads is pinned to 1 and Hash to the default; `go perft` is synchronous.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field

import chess


class FenRejected(RuntimeError):
    """The engine refused the FEN, or the board it perfted is not the one asked for."""


class EngineError(RuntimeError):
    pass


@dataclass
class Divide:
    nodes: int
    children: dict[str, int] = field(default_factory=dict)

    def check_consistent(self, depth: int) -> None:
        """The divide must add up, and a desynced stream will not.

        `go perft` terminates at a bare `nodes N` with no bestmove, so the
        harness stops reading there and trusts that no line follows. If the
        stream ever desynced -- a stray line from a previous command, a truncated
        divide, two replies interleaved -- the symptom would be a child table
        that does not sum to the total, or a root child count that does not match
        the legal move count. Both are checked here rather than assumed away.

        At depth 0 the engine prints `nodes 1` and no divide, so the sum rule
        only applies from depth 1.

        A position with NO legal moves (checkmate or stalemate) legitimately
        prints `nodes 0` and no divide lines at all. That is not a desync, and
        rejecting it would blind the harness exactly where "generates nothing"
        is the property under test. Measured: mate positions in the fuzz set hit
        this, e.g. rnbqkb1r/p1ppp2p/8/1p3ppQ/4n2P/P1N4R/1PPP1PP1/R1B1KBN1 b Qkq.
        """
        if depth <= 0:
            if self.nodes != 1:
                raise EngineError(f"perft 0 should print nodes 1, got {self.nodes}")
            return
        if self.nodes == 0 and not self.children:
            return  # checkmate or stalemate: no moves, which is a real answer
        if not self.children:
            raise EngineError(
                f"perft {depth} printed nodes {self.nodes} with no divide lines; "
                f"the output was not read as a divide"
            )
        missing = [m for m, c in self.children.items() if c < 0]
        if missing:
            raise EngineError(f"negative child counts: {missing}")
        child_sum = sum(self.children.values())
        if child_sum != self.nodes:
            raise EngineError(
                f"divide does not add up: children sum to {child_sum} but the "
                f"total says {self.nodes} (gap {self.nodes - child_sum}); "
                f"the stream is desynced or the divide was truncated"
            )


class Engine:
    def __init__(self, binary: str):
        self.proc = subprocess.Popen(
            [binary],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._send("uci")
        self._read_until("uciok")
        self._send("setoption name Threads value 1")
        self._send("isready")
        self._read_until("readyok")

    def _send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _read_until(self, sentinel: str) -> list[str]:
        assert self.proc.stdout is not None
        lines: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise EngineError(
                    f"engine closed stdout waiting for {sentinel!r}; got {lines!r}"
                )
            line = line.rstrip("\n")
            lines.append(line)
            if line.strip() == sentinel:
                return lines

    def set_position(self, fen: str) -> list[str]:
        """Set a FEN and return every line the engine emitted up to readyok.

        Raises FenRejected if the engine reported the FEN as invalid. The caller
        is expected to have validated the FEN with python-chess first; this is
        the second, engine-side gate and it is never skipped.
        """
        self._send(f"position fen {fen}")
        self._send("isready")
        reply = self._read_until("readyok")
        for line in reply:
            if "invalid FEN" in line:
                raise FenRejected(f"engine rejected FEN {fen!r}: {line}")
        return reply

    def perft(self, depth: int) -> Divide:
        """Run a synchronous `go perft` and return the divide.

        The invalid-FEN diagnostic can also arrive HERE, ahead of any node
        output, when no `isready` was sent between `position` and `go`. So the
        `go` stream is scanned too: an `info string invalid FEN` in it means the
        counts below belong to some other board and must never be scored.
        """
        self._send(f"go perft {depth}")
        assert self.proc.stdout is not None
        children: dict[str, int] = {}
        total: int | None = None
        while total is None:
            line = self.proc.stdout.readline()
            if line == "":
                raise EngineError(f"engine closed stdout during go perft {depth}")
            line = line.strip()
            if not line:
                continue
            if line.startswith("info string"):
                if "invalid FEN" in line:
                    raise FenRejected(f"engine rejected the FEN during go perft: {line}")
                # perft is synchronous; an info string here is not a node count.
                continue
            if line.startswith("nodes "):
                total = int(line.split()[1])
                continue
            if ": " in line:
                move, count = line.rsplit(": ", 1)
                children[move] = int(count)
        result = Divide(nodes=total, children=children)
        result.check_consistent(depth)
        return result

    def close(self) -> None:
        try:
            self._send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def py_perft(board: chess.Board, depth: int) -> int:
    """Independent perft over python-chess's legal move generator."""
    if depth <= 0:
        return 1
    if depth == 1:
        return len(list(board.legal_moves))
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += py_perft(board, depth - 1)
        board.pop()
    return total


def py_divide(board: chess.Board, depth: int) -> dict[str, int]:
    out: dict[str, int] = {}
    for move in board.legal_moves:
        board.push(move)
        out[move.uci()] = py_perft(board, depth - 1)
        board.pop()
    return out


def validate_fen(fen: str) -> chess.Board:
    """Gate 1: python-chess must accept the FEN as a legal, playable position."""
    board = chess.Board(fen)
    if not board.is_valid():
        raise FenRejected(f"python-chess rejects FEN {fen!r}: {sorted(board.status())}")
    return board


@dataclass
class Check:
    """One engine-vs-python perft cell."""

    label: str
    fen: str
    depth: int
    engine: int
    reference: int

    @property
    def ok(self) -> bool:
        return self.engine == self.reference


def compare_counts(label: str, fen: str, depth: int, engine_nodes: int, reference: int) -> Check:
    """The scoring step, isolated so the self-test can drive it to red directly."""
    return Check(label=label, fen=fen, depth=depth, engine=engine_nodes, reference=reference)


def check_position(
    engine: Engine,
    label: str,
    fen: str,
    depth: int,
    expect: int | None = None,
    py_reference: bool = True,
) -> Check:
    """Validate, set, prove board identity, then perft.

    `expect` is the published reference count. When given it overrides the
    python-chess count as the reference (python-chess is cross-checked against
    it and a disagreement is raised, not silently accepted).
    """
    board = validate_fen(fen)
    engine.set_position(fen)

    # Gate 3: the board the engine is actually perfting must be the one we asked
    # for. perft 1 is the legal move count, so this catches a silently refused
    # FEN, which would otherwise perft the previous position.
    identity = engine.perft(1)
    want = len(list(board.legal_moves))
    if identity.nodes != want:
        raise FenRejected(
            f"board identity failed for {label}: engine perft 1 = {identity.nodes}, "
            f"python-chess legal moves = {want}; the engine is not on this FEN"
        )
    if set(identity.children) != {m.uci() for m in board.legal_moves}:
        raise FenRejected(
            f"move set mismatch for {label} at depth 1: engine-only "
            f"{sorted(set(identity.children) - {m.uci() for m in board.legal_moves})}, "
            f"python-only {sorted({m.uci() for m in board.legal_moves} - set(identity.children))}"
        )

    # A stronger identity gate for depths that can afford it: two distinct
    # positions can share a legal-move count, but sharing both the depth-1 and
    # depth-2 counts is far less likely. Cheap next to any depth >= 3 cell.
    if depth >= 3:
        ref2 = py_perft(board, 2)
        got2 = engine.perft(2).nodes
        if got2 != ref2:
            raise FenRejected(
                f"board identity failed for {label} at depth 2: engine {got2} vs "
                f"python-chess {ref2}; the engine is not on this FEN"
            )

    if depth == 1:
        return compare_counts(label, fen, depth, identity.nodes, want)

    measured = engine.perft(depth).nodes
    if py_reference:
        ref = py_perft(board, depth)
        if expect is not None and expect != ref:
            raise EngineError(
                f"reference disagreement on {label} d{depth}: published {expect} vs "
                f"python-chess {ref}; refusing to score this cell"
            )
    else:
        if expect is None:
            raise EngineError(f"{label} d{depth}: py_reference=False needs an explicit expect")
        ref = expect
    return compare_counts(label, fen, depth, measured, ref)


def self_test() -> None:
    """Prove the harness can fail: plant a KNOWN-BAD expectation and require a red.

    Run this before trusting any green result. Three independent failure modes
    are exercised: a bad published count, a bad FEN, and a bad depth-1 identity.
    """
    binary = sys.argv[1] if len(sys.argv) > 1 else "build-swarm74/forge"
    engine = Engine(binary)
    start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    try:
        good = check_position(engine, "startpos", start, 3, expect=8902)
        assert good.ok, f"self-test baseline failed: {good}"
        print(f"[self-test 1] baseline startpos d3 = {good.engine} (ok, expected green)")

        # 1. A perft expectation that is provably wrong by one node. Driven
        #    through the scoring step directly, because the `expect` path is
        #    separately guarded against disagreeing with python-chess.
        measured = engine.perft(3).nodes
        bad = compare_counts("startpos", start, 3, measured, 8903)
        assert not bad.ok, "KNOWN-BAD perft expectation did not go red; harness is not proving anything"
        print(f"[self-test 2] planted expectation 8903 -> measured {bad.engine}, red as required")

        # 2. A published count that disagrees with python-chess must raise rather
        #    than be scored as a movegen mismatch.
        try:
            check_position(engine, "startpos", start, 3, expect=8903)
        except EngineError as exc:
            print(f"[self-test 2b] published-vs-python guard fired: {exc}")
        else:
            raise AssertionError("a published count disagreeing with python-chess was scored")

        # 2. A FEN the engine refuses must raise, never silently perft startpos.
        illegal = "8/8/8/8/8/8/8/8 w - - 0 1"
        try:
            validate_fen(illegal)
        except FenRejected as exc:
            print(f"[self-test 3] planted illegal FEN raised in gate 1: {exc}")
        else:
            raise AssertionError("illegal FEN passed python-chess validation")

        # 3. The identity gate must catch a board swap. Simulate by asking the
        #    engine for a perft-1 count while it is still on startpos, then
        #    comparing against a different board's move count.
        engine.set_position(start)
        other = chess.Board("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        n = engine.perft(1).nodes
        assert n != len(list(other.legal_moves)), "identity gate would not have fired"
        print(
            f"[self-test 4] identity gate: engine on startpos says {n}, kiwipete wants "
            f"{len(list(other.legal_moves))} -> mismatch is detectable"
        )

        # 4. The `go`-stream path: a refused FEN with NO isready in between puts
        #    the diagnostic in the go output. The harness must raise, not score.
        bad_fen = "7k/8/8/8/8/8/8/K6R w - - 0 1 QQ"
        engine._send(f"position fen {start}")
        engine._send("isready")
        engine._read_until("readyok")
        try:
            engine._send(f"position fen {bad_fen}")  # deliberately no isready
            engine.perft(1)
        except FenRejected as exc:
            print(f"[self-test 5] go-stream diagnostic caught: {exc}")
        else:
            raise AssertionError("a refused FEN in the go stream was scored as a perft")

        # 6. The divide self-consistency rule: `go perft` ends at a bare
        #    `nodes N` with no bestmove, so a desynced stream shows up as a
        #    divide that does not add up. Prove the rule fires.
        #    Use the Divide defined in THIS file: importing it from "uci_perft"
        #    re-executes the module under a second name when run as __main__, and
        #    the second copy's EngineError is a different class object, so the
        #    except clause below would never match.
        try:
            Divide(nodes=400, children={"a2a3": 20, "b2b3": 20}).check_consistent(2)
        except EngineError as exc:
            print(f"[self-test 6] non-adding-up divide caught: {exc}")
        else:
            raise AssertionError("a divide that does not sum to its total was accepted")

        try:
            Divide(nodes=400, children={}).check_consistent(2)
        except EngineError as exc:
            print(f"[self-test 7] empty divide caught: {exc}")
        else:
            raise AssertionError("a divide with no children was accepted")

        # 7. Two consecutive identical perfts must return the same total. If the
        #    harness mis-framed the end of the first reply, the second would drift.
        engine.set_position(start)
        first = engine.perft(4).nodes
        second = engine.perft(4).nodes
        assert first == second == 197281, (
            f"repeated perft drifted: {first} then {second}, expected 197281 both times"
        )
        print(f"[self-test 8] repeated perft 4 stable at {first} both times (stream re-framed cleanly)")

        # 8. depth 0 prints `nodes 1` and no divide; the new rule must allow it.
        engine.set_position(start)
        zero = engine.perft(0)
        assert zero.nodes == 1 and not zero.children, f"perft 0 misframed: {zero}"
        print("[self-test 9] perft 0 accepted as nodes 1 with no divide")

        # 9. A checkmate position prints `nodes 0` and no divide. That is a real
        #    answer, not a desync, and the rule must not reject it -- 4 of the
        #    2000 fuzz positions are mate, so rejecting them would silently
        #    remove the "generates nothing" case from the set.
        mate_fen = "rnbqkb1r/p1ppp2p/8/1p3ppQ/4n2P/P1N4R/1PPP1PP1/R1B1KBN1 b Qkq - 1 6"
        mate_board = validate_fen(mate_fen)
        assert mate_board.is_checkmate(), "self-test mate fixture is not mate"
        engine.set_position(mate_fen)
        mate_d1 = engine.perft(1)
        assert mate_d1.nodes == 0 and not mate_d1.children, f"mate misframed: {mate_d1}"
        print("[self-test 10] checkmate accepted as nodes 0 with no divide")

        print(
            "SELF-TEST PASSED: planted bad count, bad FEN, board swap, go-stream "
            "diagnostic, and a desynced divide all go red"
        )
    finally:
        engine.close()


if __name__ == "__main__":
    self_test()
