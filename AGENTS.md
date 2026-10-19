# Forge development

The user targets Windows on a Ryzen 7 9850X3D and wants measured playing-strength improvements. Use relevant available skills and plugins automatically. For SIMD/NNUE work, read `.agents/skills/validating-chess-simd/SKILL.md`. For match design and strength claims, read `.agents/skills/validating-chess-strength/SKILL.md`.

Use the existing isolated checkout. Do not create worktrees unless requested. Preserve existing branches, archives and evidence. Save meaningful checkpoints in Git and upload tested candidates to new branches; never force-push or replace a release with an unproven candidate.

Freeze each experiment's source, network, binaries, settings, openings, and stopping rule. Distinguish correctness, kernel speed, search speed and Elo. No accepted strength result exists for the AVX2 candidate yet. A limited Stockfish opponent is not full-strength Stockfish. Never count timeouts, crashes, illegal moves, interrupted pairs or incomplete runs as valid strength evidence.

For Forge 6.x matches, disable OwnBook when isolating search changes; `tools/match/run_match.py --disable-book` supports this. Use A/A calibration first. The Windows executable emits CRLF; Linux Fastchess needs text normalization through a wrapper when Wine is used.

Keep float operation order and `-ffp-contract=off`; do not enable fast-math to obtain a passing performance result. Run the relevant full CTest suite. Use `PYTHONDONTWRITEBYTECODE=1` because this repository contains tracked Python bytecode. Generated builds and toolchains belong outside the checkout.

Details, hashes and unresolved limitations are in `validation/nnue-avx2-9850x3d/` and `validation/clock-safety-9850x3d/`. The 6.4.1 candidate adds request-time accounting and stalemate detection before pruning. For its isolated search comparison, use clock-corrected reference `9cf3793`, not an opponent with the known late clock epoch. No Elo gain is accepted for this candidate. Preserve exact failed UCI exchanges; a last `info time` excludes unfinished later iterations and cannot identify output delay by itself. Shared-VM benchmark variance remains substantial, including CPU-time measurements.

Saved environment startup instructions describe installed tools. Running jobs and hourly reporting are not guaranteed to survive a finished or disconnected session; report actual monitoring state.

The preregistered original-ZIP comparison uses fixed 10,000-node searches and unlimited wall clocks because both timed pilots failed. A native SPRT result here applies only to that node budget and opponent; it cannot establish equal-clock, Ryzen, Windows or Stockfish superiority. Keep the exact original ZIP reference distinct from the clock-only causal reference. Run native SPRT serially with pinned Fastchess to avoid orphan pairs at an early boundary.

The next candidate is 6.4.2 underpromotions: noisy generation now includes all Q/R/B/N choices, with both-color searched-PV and unrestricted rook-choice tests. Evidence is in validation/underpromotions-9850x3d/. The previous 6.4.1 original-ZIP SPRT completed178normalgames, 66W44D68L, independentGLR -3.0256529003603494, H0accepted for[0,+20] at10knodes. No accepted gain transfers to6.4.2. Use the portable native Windows workflow for equal-clock evidence; do not start timed Wine/VM trials again. Windowsvalidator safety tests are now registered as the fifth Linux CTest suite.
