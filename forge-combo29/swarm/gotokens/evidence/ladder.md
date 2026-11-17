# `go nodes abc` vs `go infinite`, identical-window comparison

Build: base@6b98f217 (g++ 13.3.0, sha256 e06310ec).

| command | lines in 6 s | depths seen | bestmove after `stop` |
|---|---|---|---|
| `go infinite` | 24 | 1..24 | `e1g1` |
| `go nodes abc` | 24 | 1..24 | `e1g1` |
| `go nodes` | 25 | 1..25 | `e1g1` |
| `go mate abc` | 24 | 1..24 | `e1g1` |
