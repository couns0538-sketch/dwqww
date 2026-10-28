# R3-6Q — idea and sources

- **Question** (R3-6 UNVERIFIED list, `opus_r3/R3-6/REPORT.md`): does `SmpHelpersPastDepth` (helpers keep
  searching past the target depth in `go depth N` searches) shorten Lazy SMP time-to-depth? On the loaded PC
  (the engine got 1.4-2.1 CPUs) the effect was not measurable: offP/off 0.99 [0.80..1.21] at T2 and
  1.03 [0.86..1.20] at T3, one repetition only. R3-6 asked for a quiet machine with at least 3 free cores.
- **Idea**: run the same protocol (R3-6 `positions30.tsv`, Hash 64, fresh process per run, shuffled order,
  `summarize.py` paired ratios with bootstrap CIs over positions) on quiet GitHub ubuntu-24.04 runners
  (4 vCPUs), three independent repetitions as three matrix jobs, one shared binary.
- **Port**: `smp_ttd_linux.py` is `opus_r3/R3-6/smp_ttd.py` with Linux timing (/proc/<pid>/stat CPU,
  /proc/stat system load and steal, os.wait4 rusage) and the same JSONL fields.
- **Sources**: R3-6 (harness, positions, summarize.py, PC numbers); `opus_round1/ci/run_ci.sh` (release box
  recipe) and `opus_round1/ci/uci_check.py` (lock pins); `.github/workflows/opus-r3-switches.yml` (runner
  setup). Lazy SMP background: the Stockfish/Ethereal practice of letting helper threads search deeper
  than the main thread (depth skipping), which R3-6's fix approximates for fixed-depth searches.
