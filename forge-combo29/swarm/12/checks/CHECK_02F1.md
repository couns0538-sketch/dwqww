## S-C2 — CONFIRMS seat 02's S-F1 (the engine ignores argv entirely)

Seat 02's S-F1: the engine takes no command-line arguments, `main()` is
`return forge::uci_loop(std::cin);`, so `EXE bench 13` prints nothing and exits 0 and any harness
driving the exe by argv measures an engine that never received the command.

**Verdict: CONFIRMS, on both builds.** My own harness (`checks/argv_check.py`), my own builds and
settings, **Threads 1** (no setoption sent).

| case | base stdout | PC r15 stdout | exit |
|---|---|---|---|
| A `EXE bench 13`, stdin at /dev/null | **0 bytes** | **0 bytes** | 0 |
| B `EXE bench 13`, stdin empty | 0 bytes | 0 bytes | 0 |
| **C `EXE` with `bench 13` on stdin (CONTROL)** | **61 bytes**, `info string bench depth 13 nodes 862329` | **61 bytes**, same nodes | 0 |
| D `EXE --help`, stdin closed | 0 bytes | 0 bytes | 0 |
| E `EXE`, stdin closed (immediate EOF) | 0 bytes | 0 bytes | 0 |

**The control is case C and it is the reason this result is worth anything:** without it, "A printed
nothing" could mean my binary was broken or the path was wrong. C prints 61 bytes and the correct
862329 nodes on the same binary, so the exe works and argv is what it ignores. Case D shows it is not
just `bench` being special: `--help` is ignored too, silently, with exit code 0.

Both builds behave identically, so this is not a PC-patch regression — it is how the engine is
built, on both trees.

### Why it matters (seat 02's point, which I agree with)

A harness that runs `forge bench 13` gets an empty stdout and exit 0. If it then counts lines or
parses nodes and treats "no output" as "no fault", it reports a clean result from a run that never
happened — the same silent-zero failure mode seat 19 warned about, one level lower: not a parser
finding no number, but the engine never being asked anything.

### Files

`checks/argv_check.py` (the harness, re-runnable), raw output in `checks/argv_check_base.txt` and
`checks/argv_check_pc.txt`.

### What I am NOT claiming

Not that any particular harness in this swarm has made this mistake — I did not audit the others'
drivers for it. Only that the behaviour is real on both builds and that the argv/stdin pair above
distinguishes it.
