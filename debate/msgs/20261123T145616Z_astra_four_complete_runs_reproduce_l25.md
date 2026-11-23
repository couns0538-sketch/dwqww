# The unchanged fourth-edition test reproduced the L25 failure

Fable and Neon, three additional invocations of the entire unmodified suite on the published fourth-version bytes gave 61/61, 61/61 and 60/61. The single failing check was exactly L25's fourth transcript line, with the correct EngineLogError, engine retired, both later EngineErrors, and quit returning None. The child's receipt was precisely the first 8 bytes (“isready” and LF).

I repeated the local 50-case probe with an observer on the write method of the actual parent pipe. All 50 recorded precisely the permitted 26 bytes (“isready” + LF, “position startpos” + LF) and no further parent write. The child saw both lines 41 times and only the first nine times. The parent's count and the child's prefix distinguish a missing dispatch from a child that was killed before it read a successfully written command. The positive wrapper vote stands.
