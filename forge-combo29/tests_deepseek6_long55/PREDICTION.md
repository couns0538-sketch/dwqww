long 55 prediction (FEN fuzz, 20,000 mutated FENs under ASan+UBSan) -- own commit before the runs

1. The planted control (a 3,000-character first field) is REFUSED and does not crash. Kill:
   accepted, or a crash.
2. The class sizes: the REFUSED class dominates (my long-37 evidence: the validator refuses
   broken fields/rules); the accepted+python-chess-VALID class is the second; the
   accepted+pc-INVALID class is SMALL but NONZERO (long 33/37's accepted-while-invalid pattern:
   the impossible-castling FEN and the triple-check FEN are both accepted -- both are in G's
   mutation neighbourhoods). Kill: accepted+pc-INVALID == 0, or it is the biggest class.
3. ZERO crashes and ZERO sanitizer lines across all 40 batches. Kill: any.
4. ZERO illegal bestmoves among the accepted pc-valid FENs (the generator is sound -- long 33).
   Kill: any.
5. The knowns re-fire inside the fuzz: some mutated FENs land near long 33's castling form and
   long 37's triple-check form and are accepted -- the special_invalid_accepted.txt lists them.
   Kill: the file empty.
