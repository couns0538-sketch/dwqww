# opus_singular_noncut - SingularNonCut (deep-research card T04-01), gate-ready, default OFF

## What it is
- One search change on top of the live lock trial_w6. The singular-extension verification search
  (`search(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node)`, trial_w6 `src/search.cpp:1327`;
  the spec's lock line :1095) gets `false` instead of the node's inherited `cut_node` when the UCI option
  `SingularNonCut` is 1.
- Inside the verification frame, `cut_node` drives:
  - LMR `r += 2`;
  - the child flags of the full-depth re-searches (`!cut_node`);
  - rarely, IIR.
- Idea: Caissa 1b7a871 (MIT), see `IDEA_SOURCE.md`. Spec: `opus_deepres/notes/SPEC_SEARCH.md` "T04-01 SingularNonCut"
  on branch opus-deepres-20261104.
- Only `include/forge/search.hpp` and `src/search.cpp` change. uci.cpp is untouched. No other option or switch is
  touched (the six trial_w6 switches keep their trial_w6 values; NmpCutOnly, HistoryLmp, TtMoveHistLmr, FracLmr,
  HindsightDepth do not exist in this source).

## Switches
- Compile macro `FORGE_SINGULAR_NONCUT`, default 0. At 0 the source preprocesses to trial_w6's token stream, and the
  lp_v1 exe is trial_w6 4181A589 byte for byte (BENCH.md).
- At 1, the build gets:
  - `tune::SingularNonCut` (int, default 0);
  - one `parameters()` row `{"SingularNonCut", &SingularNonCut, 0, 1}`, so the option is accepted by `setoption`
    and, in -Expose builds (`FORGE_EXPOSE_TUNABLES`, the kit default), advertised as
    `option name SingularNonCut type spin default 0 min 0 max 1`;
  - the verification call passes `tune::SingularNonCut > 0 ? false : cut_node`.
- Runtime 0 = trial_w6 node for node. Runtime 1 = the change. A non-Expose build accepts the option but does not
  advertise it, and the crew's runner checks that options are advertised: use the -Expose exe below.

## Files
| file | what |
|---|---|
| `singular_noncut_after_w6.patch` | the change on the trial_w6 source tree (switch defaults 0), `patch -p1 -F0` |
| `singular_noncut_stack.patch` | lock source (FD3A5190 tree, `F:\ospd\src\lock`) -> the same tree in one step |
| `tools/snc_controls.sh` | builds `snc_id` (six flipped, macro 0) and `snc_gate` (six + macro 1) from `D:\opus_singular_noncut\src\snc` |
| `tools/smoke_run.ps1` | fastchess crash / time-loss smoke, gate exe ON vs trial_w6 (not a verdict) |
| `BENCH.md` | identity proof, OFF pins, ON nodes, perft |
| `IDEA_SOURCE.md` | source commit, licence notice (MIT), what was taken |
| `STATUS.md` | done / in progress / next step / resume commands / unproven claims |
| `logs/` | build summaries, bitexact logs, preprocessor check, smoke summaries |

## Exes
- Gate exe (candidate): `D:\opus_singular_noncut\pack\forge_singular_noncut_gate_5f6be7c5.exe`, sha256
  5f6be7c55ba318790c26690b0a96edec678aab786334247a8e7a630c5610d117. Built with QA kit v2.3 lines (`build_variants
  lp_v1`), pc1 = pc2.
- Base: trial_w6 `C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe`, sha256
  4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0 (= this pack's identity build).

## Gate line (for QA / Strength after Code Review; nothing is queued by this job)
```
cand: forge_singular_noncut_gate_5f6be7c5.exe   setoption name SingularNonCut value 1
base: forge_ltopgo_x_al1s198_trial_w6.exe (4181A589)   no options
```
- fastchess form: `option.SingularNonCut=1` on the candidate.
- TC, book, bounds and Threads per the owner / crew decision (spec Common parts: UHO SPRT at STC, then LTC; the
  card proposed [0, 5]).
- The gate exe at its default (0) searches trial_w6's nodes, so a gate of the gate exe without the option is an A/A.

## Notes for Code Review
- The PGO profile is trained with the option at 0 (the kit's frozen workload). The ON path is cold-optimised, so ON
  nps can be a little lower than OFF. It is not measured; the SPRT includes it.
- `cut_node` is a by-value parameter: the flip affects only the verification call, and the node's own flag stays as it
  was (Caissa had to restore its field; Forge has nothing to restore).
- Not done (crew items):
  - the spec's counter build (FORGE_SPEC_COUNTERS: singular tries, outcomes, nodes inside the verification);
  - the mate probe OFF / ON;
  - the sanitizer level L4;
  - Threads > 1 with ON (beyond the smoke).

## Rebuild
1. Copy `F:\ospd\src\lock` to `D:\opus_singular_noncut\src\snc` and check it with `sha256sum -c
   F:/ospd/src/lock_SOURCES.sha256`.
2. Apply `patch -p1 -F0 < singular_noncut_stack.patch`.
3. Run `bash opus_singular_noncut/tools/snc_controls.sh`.
4. From Git Bash: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File opus_speed/tools/build_variants.ps1
   -SrcDir D:\opus_singular_noncut\src\snc_gate -Tag <new tag> -Variant lp_v1 -Twice -Work D:\opus_singular_noncut\build`.
   It must print `REPRO` with sha256 5f6be7c5....
