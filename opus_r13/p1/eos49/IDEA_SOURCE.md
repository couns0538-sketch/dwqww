# IDEA_SOURCE - eos49 port (R13 P1 item 5)
- Port: Opus R13. src/search.cpp and include/forge/search.hpp of `D:\grok-pc-data\opus30h_inputs\packe2r_h256e12_src.zip`
  (fc_packe2r_h256e12) copied onto the lock tree d4f4312; they are the only source files that differ from the lock
  (the h256e12 base has the lock's search code and another net). Byte-equal to the zip's files.
- Contents (crew's packe2r, unchanged): Pack E2 P15 ContHist4Pct (4-ply continuation history in quiet ordering; not in the
  gate-49 line, default 0) and P17 EvalOnlyStore (store the raw static eval in the TT before early pruning), plus
  EvalOnlyStoreMinDepth (Engine Coder's own idea: depth threshold for that store). Idea sources quoted from the crew's
  packae2r IDEA_SOURCE.md: EvalOnlyStoreMinDepth is a generic depth-gated TT write, no engine source used; the P15 / P17
  idea sources are in fc_packe2_h256e12/IDEA_SOURCE.md (not among the R13 inputs). No code from other engines.
- Status: UNPROVEN. No Elo or speed claim.
