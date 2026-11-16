long 56 prediction (the UCI fuzz: 2,000 random sequences under ASan+UBSan) -- own commit before the runs

1. ZERO crashes and ZERO hangs: every sequence's isready gets its readyok within the 20 s window
   (long 46's twelve cases were clean; the grammar's commands are all handled). Kill: any.
2. ZERO sanitizer lines across 2,000 sequences. Kill: any.
3. ZERO illegal bestmoves (with the same classification rules as long 55: 0000 on a finished
   position is correct; the engine's illegal-prefix skip (long 46) handled; a position
   python-chess cannot parse is excluded from the check). Kill: any.
4. Every sequence's exit is 0 or a clean quit. Kill: any other exit code.
