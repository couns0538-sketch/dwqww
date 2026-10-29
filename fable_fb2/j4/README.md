# FB2-J4: time management v2 (branch `fable-fb2-j4`, UCI option `TimeManV2`, default false)

With the option off the engine is the lock (OFF identity pins: `logs/identity_off_j4.log`). With it on, a
clock-managed search (`go wtime/btime/...`) uses `forge::timeman::decide_v2` (`include/forge/timeman.hpp`):

1. the lock's allocation (`timeman::allocate`, the same formula and `tune::Tm*` constants) gives soft and hard ms;
2. after every iteration the soft time x scale factor (stability, effort, score drop: `timeman::scale_factor`, the
   lock's rules) becomes a node budget at the speed measured so far; the search stops when the budget is spent or
   when `nodes + 50% x predicted next iteration` (EBF from the last two iterations) would overshoot it;
3. inside the next iteration a soft node limit (budget x 130%) stops the search at a clock-read point;
4. the hard deadline is read every 1024 nodes far away and every 64..512 nodes close to it
   (`timeman::check_mask`), in the main search and in quiescence, so the search returns at most one interval after
   `hard_ms` (which is itself `<= time_left - Move Overhead`).

## Tools
- `forge_timeman_sim [games] [--seed N] [--stall-ms M --stall-prob P] [--nps N] [--csv file]` (CTest
  `forge_timeman_sim 2000`): simulated games at 1+0.01 and 10+0.1 for the lock's rule (v1) and v2 with the real
  decision functions; the search is modelled (iteration growth with a random EBF, +-25% speed per move, +-10% per
  iteration, optional stalls, 1 ms GUI latency, Move Overhead 10). Reports flag losses, moves beyond the hard
  deadline, the maximal overshoot, the minimal remaining clock, used/soft fractions and mean depth; exit 1 on any v2
  flag loss.
- `tools/timeman/fable_timeman_games.py <exe> --tc 1+0.01 --games 100 --opt-white TimeManV2=true --opt-black
  TimeManV2=true`: real games over UCI with GUI-style wall-clock charging (python-chess legality, random 6-ply
  openings); flag losses, max used, min clock, result distribution (`logs/games_*.json`).

## Evidence
`logs/sim_2000*.log` (three scenarios x 2000 games x 2 time controls x 2 managers), `logs/games_1s_v2.*`,
`logs/games_1s_v1.*`, `logs/games_10s_v2.*`, build / identity / ctest logs. No Elo claim: a gate decides whether
v2 plays better; the harness only proves it never loses on time in these scenarios.
