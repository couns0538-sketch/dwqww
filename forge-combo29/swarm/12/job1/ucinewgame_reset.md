# Suspected finding: `ucinewgame` silently resets the position to startpos

Status: **suspicion, but the behaviour itself is measured and repeatable**; what is not yet
proven is that it costs anything, or that it is unintended. It is not in the "already known"
list of FABLE_TO_swarm_1.

## The command

```
printf 'position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1\nisready\nucinewgame\nisready\ngo depth 3\nquit\n' \
  | ~/build/release/forge | grep -E "bestmove|pv "
```

Result: `bestmove a2a3` — the answer for **startpos**, not for the K+P position that was set
two commands earlier (`e2e3`/`e1d1` are the K+P moves). Without the `ucinewgame` line the same
sequence answers `bestmove e2e3`.

Source: `src/uci.cpp:254-257`

```
} else if (command == "ucinewgame") {
    stop_search();
    searcher.clear();
    (void)board.set_fen(forge::Board::StandardStartFen);
}
```

## Why this matters

The UCI protocol only says `ucinewgame` clears search state ("the engine should clear its
internal state, be ready for a new game"); the position is set by `position`, and a GUI always
sends `position` after `ucinewgame`, so in normal play this is harmless. It becomes visible to
any tool that sends `ucinewgame` between `position` and `go` — which random-sequence fuzzers and
some tuning harnesses do. Before I found this line, my own attribution harness mis-flagged 6
"illegal bestmoves" that were in fact legal moves of startpos; that is the cost in practice: a
checker that does not model this reports false faults.

## What I have NOT proven

- that the reset is unintended (it is a deliberate `set_fen` call, so it looks deliberate);
- any effect on node counts or on game play (a GUI always re-sends `position`);
- whether the reference engines do the same (not checked, out of scope for area 2).

## How to see it again

```
printf 'position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1\nisready\nucinewgame\nisready\ngo depth 1\nisready\nquit\n' \
  | ~/build/release/forge | tail -3      # -> bestmove a2a3  (startpos), not a K+P move
printf 'position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1\nisready\ngo depth 1\nisready\nquit\n' \
  | ~/build/release/forge | tail -3      # -> bestmove e2e3  (the K+P position is kept)
```
