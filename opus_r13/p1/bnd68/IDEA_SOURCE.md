# IDEA_SOURCE - bnd68 port (R13 P1 item 3: gate 68 bundle g43 + g33 + g49)
- Port: Opus R13. include/forge/{board,search}.hpp, src/{board,search}.cpp and tests/{nonpawn_key,pack_e}_tests.cpp of
  `D:\grok-pc-data\opus30h_inputs\packae2r_h256e12_src.zip` (fc_packae2r_h256e12) copied onto the lock tree d4f4312;
  they are the only source files that differ from the lock. Byte-equal to the zip's files; the src/include line set equals
  packa (item 2) + packe2r (item 5) exactly (logs/bnd68_lineset.txt).
- Idea sources: packa (NonPawnCorr, PawnHist) see ../packa_w50/IDEA_SOURCE.md; packe2r (ContHist4Pct, EvalOnlyStore,
  EvalOnlyStoreMinDepth) see ../eos49/IDEA_SOURCE.md. The crew's packae2r note: hand merge of the CR-passed Pack A code into
  fc_packe2r_h256e12, no new code, ideas or constants. Gate values are the crew's own (g43 / g33 / g49).
- Status: UNPROVEN. No Elo or speed claim.
