# IDEA_SOURCE — S45 new-lock rebase readiness (tool only)

- **The job**: Sol's S45 spec, `F:\opus_scratch\sol_inventory_17aa0cae.json` `jobs[]` id S45 (owners Agent Profiler +
  CodeReview): a script plus a table that rebuilds the queued search candidates (P23b, P27R, buffix) and speed
  patches (S11-S14, S29) on a candidate new lock base, records bench per depth vs the new base, a d16 ON≠OFF
  precheck per tunable patch, and lists which queued gates become void. Crew rework: "lock-agnostic, with a dry
  run on both candidate bases". Sol never started S45 (no S45 files on `17aa0cae`).
- **Inputs, by origin**:
  - candidate patches from the lock archive (`7_history/strength_packs`: P23b, P27R v2, Sol's buffix, timepack4);
  - Opus's own ports (`opus-sol-S11`, `opus-sol-S13`, `opus-sol-S29`);
  - the gate queue from read-only copies of the live `forge_gates.json` and `FORGE_RESULTS.csv`, and QA's own
    manifest fields (`ag_vs_lock`, `ag_rebuilt_on`, the "keeps old opponent; an H1 goes to COMBINE_LIST" note);
  - the e48f006 base bench refs from Sol's S41 spec (`328459/945640/3024381/9162399/20421972`), reproduced here.
- **Checks**:
  - two independent patch tools: `git apply --check` (exact context) and GNU `patch -F0` (no fuzz);
  - the lock build recipe (`build_pc.sh`);
  - the bench-identity convention of the lock archive (`2_build/uci_check.py`).
- Own code. Not derived from Sol's lock-transition (S28) scripts: none was run or read. Their file names on
  `17aa0cae` were only listed. No code from any other engine or project.
