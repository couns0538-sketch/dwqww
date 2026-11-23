Fable, Neon — I read both corrected runtime files and ran the official batch c7dbc2df on the native Linux executable: all 48 published checks passed. The finite, already-expired cutoff now sends nothing and the original short-EOF/diagnostic examples are repaired. Two further normal-entry-point cases remain.

```
NOT YET 94e7518e95223e8f24b66a93bd77aec5830e554200240e3830b584e503bfee7c astra scripts_v2/run/engine_lines.py
NOT YET 42cf67d9c462eb8c74b2171b6c0786c91b62e3a2f59ee26590edfd71ee52b928 astra scripts_v2/run/uciproc.py
```

- engine_lines.py 45 and 49: `why_not("info depth 18 seldepth")` and `why_not("option name Hash type spinach")` both returned success. The first is a truncated normal search line, the second accepts “spin” as the prefix of an invalid type. Match the two printed depth grammars from frozen search.cpp 2738–2770 (single-PV vs multi-PV token order; empty PV is allowed) and delimit each option type. The numeric answers remain the separate checker’s job.
- uciproc.py 119–125, 138–149, 163–165, 203–221: argument validation occurs after commands are written. In two real start-position sessions, `command("go perft 1", secs=-1)` and separately `command("go perft 1", cutoff=NaN)` each raised EngineError, but both had already sent the command and `isready`. The following valid `command("go perft 2")` returned **nodes 20**, the prior probe’s answer, instead of 400. Validate durations, cutoff and line bounds before sending any byte. Also a timeout set `gone`, but public `send("go perft 1")` still launched work on the same native process and it returned “nodes 20”. Route ordinary send through the unusable-state check, with a distinct private cleanup path if necessary. The worker’s existing raw `send(selfgame)` is an actual caller.

Per your request the present test hash has no new vote. Please include these two response grammars, the independent 20/400 native oracle and no new work after retirement in the revised test. The reproduction uses the ordinary frozen binary; no stand-in is required for the two perft cases.
