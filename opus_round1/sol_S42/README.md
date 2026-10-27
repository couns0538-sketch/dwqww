# S42 Higher-variance opening book study (proposal + stats only)

Goal (Sol's S42): a candidate book whose exits sit at about |eval| 0.6-1.2. It is scored at a fixed depth by OUR engine
only, with both colours per pair, to cut games-to-decision (58 % of G119 pairs were 1-1). **Nothing here plays a game or
touches a gate or a live book.** Adopting a book is a crew vote plus a validation replay.

## Tools
| file | what it does |
|---|---|
| `forge_sol_S42_book_v2_20261027.py build` | Builds the candidate book from the current book's lines (`8moves_v3.pgn`). In a seeded order, each line gets ONE seeded random legal deviation: either it replaces the line's last book move, or it is played right after the exit. The tool skips checks, game-over positions, any current-book exit and repeats, scores the new exit with the AL1 lock exe at depth 12 (Threads=1, Hash=16, `ucinewgame` before every position, Idle), and keeps it when 60 <= abs(eval) <= 120 cp. It writes `forge_sol_S42_book_v2_20261027.epd` (6-field FENs, fastchess `format=epd`), a metadata CSV, every scored candidate, `build_summary.json` (deterministic) and `run_info.json`. |
| `... sample` | A seeded sample of current-book exits scored the same way: the current book's eval histogram. |
| `... gate` | Reads a gate PGN (a read-only copy). It pairs games by Round, finds each pair's book exit (moves commented `{book}`), checks the pentanomial against the RESULT, scores every exit at depth 12, and writes per-game rows plus a table by abs(exit eval). |
| `forge_sol_S42_power_20261027.py` | Fits an ordered-logistic game model on the gate's games (strength Delta, opening-eval slope c, White bonus w, draw width d; MLE, Hessian SEs, a likelihood-ratio test of the eval term). It checks the predicted pentanomial against the observed one, predicts profiles for each book, and runs **Sol's S33 planner unchanged** (`sol_S33/`, sha-pinned) on them. The planner's true Elo is set to each profile's own logistic Elo (identity tilt), so books are compared at the same model strength. It also writes a sensitivity table for books at fixed abs(eval). |
| `scipy_shim/` + `check_scipy_shim_s42.py` | The venv has no SciPy and nothing may be installed, so a numpy-only stand-in supplies the 4 functions the planner imports. Validated: Sol's six frozen validation cells reproduce **exactly** (MC) and to 7.5e-15 (analytic). |
| `fake_uci_engine_s42.py` | A SYNTHETIC UCI engine for the tests (deterministic hash scores). |

## Run (the PC's read-only NNUE venv: Python 3.10.22, numpy 1.26.4, python-chess 1.11.2)
```
E=<copy of forge_h256_s198.exe (AL1 lock, sha256 5d4df7f1...)>; B=<copy of 8moves_v3.pgn (sha256 5835239f...)>
nice -n 19 <python> -I -B forge_sol_S42_book_v2_20261027.py build  --book $B --engine $E --depth 12 --lo 60 --hi 120 --target 1000 --seed 20261027 --out <NEW>
nice -n 19 <python> -I -B forge_sol_S42_book_v2_20261027.py sample --book $B --engine $E --depth 12 --n 2000 --seed 20261027 --out <NEW>
nice -n 19 <python> -I -B forge_sol_S42_book_v2_20261027.py gate   --pgn <G119 pgn copy> --cand cand_h256_e32f003rec_s197 --engine $E --depth 12 --expect-ptnml 9,130,435,163,13 --out <NEW>
nice -n 19 <python> -I -B forge_sol_S42_power_20261027.py --gate-games <gate csv> --observed-ptnml 9,130,435,163,13 \
       --current-sample <sample csv> --new-book-meta <book meta csv> --runs 20000 --out <NEW>
<python> -I -B check_scipy_shim_s42.py ; <python> -I -B test_forge_sol_S42_20261027.py ; <python> -I -B mutation_check_s42.py <scratch>
```
Engine use is small: about 40 ms per position at depth 12, one core at Idle (the 1,000-position build scored 5,193
candidates). `--lo/--hi` set the band and `--target` the size, so a wider-band variant needs no code change.

## Limitations
- Power numbers are a MODEL calibrated on G119's games (one gate, concurrency 5, s197 vs h256_e12). Pairs are treated as
  independent games given the opening, and the model reproduces G119's pentanomial (chi-square 0.43, 4 df). Not
  measured: the ≤200-game box sample the spec asks for. No engine games were played (instructions), so that sample is
  UNVERIFIED and is the first thing a validation replay should measure.
- The depth-12 evals are our engine's scale; "0.6-1.2" is read as 60-120 cp of the AL1 lock at depth 12.
- The deviation is a random legal move, so some positions look odd, though their exits are within the band at depth 12.
