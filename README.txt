FORGE 6.5
=========

This branch holds the chess engine Forge exactly as the training loop on the owner's PC plays it on
23 November 2026: the full source, the Windows programs built for his processor, the neural net, and the
settings. Nothing here is the old "combo29 lock"; this is the engine with everything that was added since.

Author: couns0538-sketch.
Co-authored by Fable and Opus and other AIs. The branch was put together on the author's order of
23 November 2026 and checked twice, the second time apart from the first.
Every file on this branch is listed with its sha256 in HASHES.sha256.


HOW TO PLAY IT: Forge65.exe

 1. Download this branch (green "Code" button, "Download ZIP") and unpack it.
 2. In a chess program that takes UCI engines (Arena, Cute Chess, Banksia, En Croissant ...) add
    Forge65.exe as a new engine.
 3. Play. Nothing has to be set: the net is inside the program and the loop's 24 settings are active
    from the start. The engine says so in its first lines: "info string NNUE v3 active: v3 <forge65> ...".

Good to know:
 - It starts with 16 MB of memory for its search table (the setting "Hash"), as the loop does. For games
   with more than a few seconds a move, raise Hash in the chess program (256 or more).
 - It thinks with one processor thread (the setting "Threads"), as in every measurement on this page.
   More threads work, but their strength was never measured.
 - Its own opening book is switched off (the setting "OwnBook"), as in the loop and in every match:
   every move comes from the search with the net.
 - The program names itself "Forge 6.5" by "Couns".
 - It was built for an AMD Ryzen 7 9850X3D and will not start on a processor without AVX-512.


WHAT IS IN HERE

  Forge65.exe                  The program to play with (sha256 9ba55d4669acb64b...). The same search code
                               as loop/forge.exe, with the net and the loop's settings inside. Built on
                               23 November 2026 with the loop exe's own recipe (clang 23.1.5, -march=znver5,
                               AVX-512, ThinLTO, profile-guided).
  source/                      The full source Forge65.exe was built from: tree "r65" = the loop's tree
                               "r15dsg" plus one compile switch, FORGE65 (9 .cpp files + forge65.cpp,
                               4 .inc data files, 15 headers + forge65.hpp, CMakeLists.txt, notes).
                               source/R65_NOTE.txt says what the switch changes (nothing in the search)
                               and lists every check.
                               The net's bytes are source/src/forge65_net.fnn3. Hash list of the build's
                               inputs: source/SOURCE_INPUTS.sha256.
  Forge65_build/               The script that built Forge65.exe and the log of that build.
  loop/forge.exe               The engine program byte for byte as the training loop uses it
                               (sha256 cef2f21589102392...; built on 20 November 2026). It needs its
                               settings and the net's path sent to it; Forge65.exe does not.
  loop/forge65_r0067.fnn3      The net (sha256 737f197808fef489...): 768 wide, 8 king buckets, format
                               FORGENN3. It is the candidate of training round 67 and has been the loop's
                               best net since then (rounds 68 to 135 did not beat it).
  loop/LOOP_OPTIONS.txt        The 24 settings the loop sends to the engine, as "setoption" lines, written
                               from the loop's own code.
  loop/build_clang.log         The log of the build that made loop/forge.exe.
  loop/source/                 The full source that loop/forge.exe was built from (tree "r15dsg").
                               Its own hash list is loop/source/SOURCE_INPUTS.sha256.
  loop/build_recipe/           The scripts that built it, as they are on the PC. They name folders of
                               that PC (C:/nnue-lab/...) and are here so that the recipe can be read.


WHAT WAS CHECKED (23 November 2026, on the owner's PC)

Forge65.exe:
 - Started with nothing set, it searches the same trees as loop/forge.exe with its 24 settings and the
   net: the same node counts (bench 11 = 226187, bench 13 = 616966; these two numbers were written down
   from loop/forge.exe before Forge65.exe ran).
 - Opus's own check, made apart from Fable's: on 600 positions (200 openings and 400 positions from
   games, searched to depth 12) Forge65.exe with nothing set and loop/forge.exe with its 24 settings
   give the same node count and the same best move on 600 of 600 (32,126,911 nodes on both sides).
 - Put back to the engine's built-in settings it prints the three reference numbers of this engine
   family (bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609).
 - Its list of settings shows what is really active (all 24 equal to the loop's), and a chess program
   that sends every listed value back changes nothing (same node counts, nothing refused).
 - A real UCI client (python-chess) starts it, reads its settings and gets searched moves.
 - Move rules: 12 of 12 published perft counts.
 - With the switch FORGE65 off, source/ compiles to the same text as loop/source/, and the 24 start-up
   lines in source/src/forge65.cpp equal loop/LOOP_OPTIONS.txt (the net's path aside).
loop/forge.exe:
 - It prints the three reference numbers with its built-in settings, and every file of loop/source/
   matches the hash list of the tree the exe was built from.
Strength, with this net and the same search code, on the clock at 6 seconds + 0.06 a move
(19 November 2026, one thread, Hash 16, UHO openings; a difference in such a match is an estimate,
not a rating):
       against Stockfish 19 limited to 3100:   224 wins, 87 losses, 89 draws   (+124 Elo, +/- 28)
       against Stockfish 11 at full strength:  141 wins, 70 losses, 89 draws   (+84 Elo, +/- 28)
       against Stockfish 10 at full strength:  169 wins, 56 losses, 75 draws   (+138 Elo, +/- 31)


WHAT THE ENGINE IS

A C++20 UCI chess engine: bitboards, alpha-beta search with the usual pruning and reductions, a
king-bucket NNUE evaluation, and a built-in game loop for self-play ("selfgame").
The net was trained on the PC from the engine's own self-play games (about 380 million positions in the
training window), round after round, each new net tested against the best one by thousands of games.
