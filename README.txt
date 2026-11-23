FORGE 6.5
=========

This branch holds the chess engine Forge exactly as the training loop on the owner's PC plays it on
23 November 2026: the full source, the Windows program built for his processor, the neural net, and the
settings. Nothing here is the old "combo29 lock"; this is the engine with everything that was added since.

Made by Fable (Claude) on the owner's order of 23 November 2026. Every file on this branch is listed with
its sha256 in HASHES.sha256.


WHAT IS IN HERE

  loop/forge.exe               The engine program, byte for byte the one the training loop uses
                               (sha256 cef2f21589102392...). Built on 20 November 2026 for an AMD Ryzen 7
                               9850X3D (clang 23.1.5, -march=znver5, AVX-512, ThinLTO, profile-guided).
                               It will not start on a processor without AVX-512.
  loop/forge65_r0067.fnn3      The net (sha256 737f197808fef489...): 768 wide, 8 king buckets, format
                               FORGENN3. It is the candidate of training round 67 and has been the loop's
                               best net since then (rounds 68 to 135 did not beat it).
  loop/LOOP_OPTIONS.txt        The 24 settings the loop sends to the engine, as "setoption" lines, written
                               from the loop's own code.
  loop/build_clang.log         The log of the build that made loop/forge.exe.
  loop/source/                 The full source that loop/forge.exe was built from (tree "r15dsg":
                               13 .cpp files, 15 headers, CMakeLists.txt, notes). Its own hash list is
                               loop/source/SOURCE_INPUTS.sha256.
  loop/build_recipe/           The scripts that built it, as they are on the PC. They name folders of
                               that PC (C:/nnue-lab/...) and are here so that the recipe can be read.


AN EASIER PROGRAM IS COMING

loop/forge.exe needs its 24 settings and the path of the net typed into the chess program by hand.
A second program, Forge65.exe, with the net and the settings already inside (nothing to set), is being
built and checked now and will be added to this branch at the top, with its source.


HOW TO USE loop/forge.exe UNTIL THEN

 1. Download this branch (green "Code" button, "Download ZIP") and unpack it.
 2. In a chess program that takes UCI engines (Arena, Cute Chess, Banksia, En Croissant ...) add
    loop/forge.exe as a new engine.
 3. In that engine's settings set every line of loop/LOOP_OPTIONS.txt. Two of them matter most:
        NNUEArchFile = the full path of forge65_r0067.fnn3   (set this one first)
        NNUEArch     = true
    Without these two the engine plays with an older, much weaker evaluation and says nothing.
    Threads and Hash are yours to choose (the loop uses 1 and 16).
 4. The engine confirms the net with the line "info string NNUE v3 active: ...".


WHAT WAS CHECKED

 - loop/forge.exe prints the three reference numbers of this engine family with its built-in settings:
   bench 11 = 312866 nodes, bench 13 = 862329 nodes, perft 5 = 4865609 (run on 23 November 2026).
 - Every file of loop/source/ matches the hash list of the tree the exe was built from (29 of 29).
 - With this net and the same search code, on the clock at 6 seconds + 0.06 a move (19 November 2026,
   single thread, UHO openings; a difference in such a match is an estimate, not a rating):
       against Stockfish 19 limited to 3100:   224 wins, 87 losses, 89 draws   (+124 Elo, +/- 28)
       against Stockfish 11 at full strength:  141 wins, 70 losses, 89 draws   (+84 Elo, +/- 28)
       against Stockfish 10 at full strength:  169 wins, 56 losses, 75 draws   (+138 Elo, +/- 31)


WHAT THE ENGINE IS

A C++20 UCI chess engine: bitboards, alpha-beta search with the usual pruning and reductions, a
king-bucket NNUE evaluation loaded from a file, and a built-in game loop for self-play ("selfgame").
The net was trained on the PC from the engine's own self-play games (about 380 million positions in the
training window), round after round, each new net tested against the best one by thousands of games.
