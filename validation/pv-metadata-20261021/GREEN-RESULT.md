First actual GREEN phase: finite diagnostic PASS; production unchanged.

Exact pristine21 archive plus ONLY combined diagnostic/two-line repair patch;
76source files frozen before launch. Green search SHA256
1c97568a918cad6788ccaf6c2653b0d29d503d05e9eea40984cd757d765f6211.
The production-only proposed fix is still exactly caller tt_pv save/restore around
same-ply singular verification. No other state, heuristic, constant or network edit.

All four actual-Worker probe cases pass/exit0: PV/nonPV-hit1singular/0flagchanges;
PV/PV-hit1/0; PV/no-initial-hit0/0; null-window/TT-cut0/0. Both observed direct
singular FEN/move rows independently pass python-chess legality and preserved
in_check/PV flags. Natural bench's eight searches contain618singular calls and
zero flag changes, versus baseline RED716calls/25losses. Green bench292545nodes;
original and instrumented RED321912. The repair changes selective search, so
node parity was deliberately not a GREEN gate. Neither fewer nodes nor raw timing
establishes speed or Elo.

Driver completed all six configure/build/probe/search process steps with expected
exit0, owned groups closed, unchanged source/outer approvals and artifact hashes.
Every nonsearch archive member remains bit-identical to exact21, including NNUE.
Green result SHA25612b460968bc94ae6cac9d7961024107042d7f1d5e611090178e2b7c48fc4c6d9.
Full commands/raw streams/cleanup are under green-attempt1; outer pins and isolated
export/patch provenance were saved before execution. No engine step repeated.

A post-engine read-only audit command initially selected base python, whose chess
import failed before audit writes. Its observed tool error is preserved separately;
the existing venv interpreter then audited original evidence without engine rerun.
This audit-tool correction changes neither engine result nor source or protocol.

Scope: actual-core RED/GREEN plus actual natural-search PV-state invariant evidence.
No current production edits, Git changes, full Release/ASan/TSan/Windows candidate
qualification, equal-clock games or accepted strength result. Root independently
reviews these records before deciding permanent regression and integration.
