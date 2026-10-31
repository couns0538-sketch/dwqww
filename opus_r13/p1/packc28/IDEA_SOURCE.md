# IDEA_SOURCE - packc28 port (R13 P1 item 4)
- Port: Opus R13, `D:\grok-pc-data\opus30h_inputs\packc.patch` applied to the lock tree d4f4312 with `patch -p1 -F0`
  (no fuzz); line set EQUAL to packc.patch. No new code, ideas or constants.
- The patch's own header: "Pack C switches (all default OFF). Own implementations of public ideas." Its parts:
  P8 AspFailHighReduce / AspFailHighMaxReduce (consecutive aspiration fail-highs reduce the re-search depth, main worker
  only); P9 EvalSwingMult / EvalSwingMax (the static-eval swing of the previous quiet move feeds the mover's main history);
  P10 TtCutoffHistory (a stored quiet fail-high teaches the ordering tables; not in the gate-28 line). All are public
  search ideas (aspiration fail-high reduction, eval-difference history and TT-cutoff history appear in many engines);
  GPL engines are ideas only, no code or constants taken.
- Gate-28 values (AspFailHighReduce=1, AspFailHighMaxReduce=3, EvalSwingMult=24, EvalSwingMax=200) are the crew's own
  (from `D:\grok-pc-data\forge_push\gate28_packc_h256_vs_h256e12\RUN_INFO.json`).
- Status: UNPROVEN. No Elo or speed claim.
