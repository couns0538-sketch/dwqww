# GrokChess SMP worker-exit research

The 10:15 compiled-JS research baseline hangs if a main/helper worker exits during search. An isolated candidate repairs this by settling pending promises and rebuilding the worker slot. The new candidate passed controlled red/green tests, actual Node worker fault injection, 36 movegen tests, 25 perft tests, and exact benchmark node checks (219323/286029). Source patch, tests and logs are in the 11:05 checkpoint ZIP. No Elo gain is claimed. This does not alter the Forge or GrokChess production branches.
