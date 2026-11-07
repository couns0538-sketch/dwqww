# T3 profiling: PC-specific ideas for the crew

1. **Recording without installs:** `wpr -start CPU -filemode`, run the workload, `wpr -stop <file>.etl`.
   - Then `samply import --save-only -o profile.json.gz <file>.etl --symbol-dir <pdb dir>`.
   - Table: `tools/t3_samply_top.py` (headless), or `samply load profile.json.gz` (Firefox Profiler on 127.0.0.1).
2. **Keep traces short and rare.** WPR records the whole PC: a 6 s trace was 354 MB here and sampled the live gates
   too. Start it only around the program of interest, and never during an official QA timing.
3. **Real-game profiles for free.** The same system-wide trace contains every engine that the gates run. With
   `--process <gate exe name>`, the lock's profile at 10+0.1 / Threads 2 comes out of any short trace. That needs no
   extra games, and it sees what the bench misses (time checks, TT pressure at gate Hash 16, SMP).
4. **Symbols.**
   - The kit's g++ exes keep a COFF symbol table: function names, but no inline frames.
   - For inline detail, build the same source with llvm-mingw + MSYS2 libstdc++ and `-g -gcodeview -Wl,--pdb=<file>`
     (T2 shows such a build is node-identical).
   - Or add `-g` to a g++ build. DWARF in a PE is read by llvm-symbolizer, but samply's importer expects PDB.
5. **Sampling rate.** WPR's CPU profile samples at 1 kHz. For short benches, `wpr -setprofint` (units of 100 ns, as
   admin) can raise it, e.g. `wpr -setprofint 1221` = 8 kHz. Untested here.
6. **Hardware counters** (cache misses, branch mispredicts on Zen 5) need AMD uProf (catalog D5), a system install
   with a driver. That is the owner's decision; WPR / samply give time only.
7. **Next profiling targets** (from RESULT.md):
   - the MovePicker sort (3.6-4.8 %),
   - `Move::operator==` (3.4 %),
   - HCE `evaluate_pieces` (6.4 %),
   - the NNUE update path (`nnue::update` 5.1 % + `Accumulator::add` 2.1 %).
