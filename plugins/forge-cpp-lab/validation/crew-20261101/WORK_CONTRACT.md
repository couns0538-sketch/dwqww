# Crew skill extension — 2026-11-01

Base: published Forge C++ Lab 1.0.0 branch `astra-cpp-chess-plugin-20261031`; this task uses isolated `astra-crew-skills-20261101`. The old /tmp worktree is no longer present, so recovery uses GitHub, not an older engine source. User requested exactly seven skills and crew installation commands. No engine, live trainer, queue or grok-pc run is authorized by this skill-authoring task.

Deliverables: forge-lock-proof-set, eval-exact-simd-port, abba-nps-timing, npt-data-holdout-check, resumable-shard-job, grok-pc-safe-run and gate-handover-pack. Each gets a scoped SKILL.md, CLI/examples, helpers where they enforce a check, and tests. Extend existing plugin to1.1.0; retain old skill and evidence. No duplicate exact-named existing skill was found in the recovered package.

Shared rules: use current caller-supplied pins/hashes; capture original native receipts; no fabricated native outcomes or Elo; no silent reconstructed FEN/castling/EP; game-ID absence leaves game separation UNVERIFIED; no implicit pruning; immutable output and verified publication. T4 is incompatible with a two-worker grok-pc run, so use a separately authorized test host or mark that check incomplete. Helpers validate explicit adapter evidence and cannot prove that arbitrary native adapters are honest or that arbitrary child programs are sandboxed.

Proof interface for gate consumption: schema1,status PASS|FAIL, baseline_commit,candidate_commit,contract_sha256, checks with name/status/evidence[{path,sha256}]. Required rows: build_a,build_b,reproducible_builds,off_pins,on_active,perft,smoke_t1,smoke_t4,asan_ubsan. A missing or unverified required row blocks a gate-ready claim.

Native Windows, real13/14 holdouts, actual LTO+PGO builds and training/gate use are separate qualification; this session validates the new helper code and scenarios in its available environment. Installed/discovered/behavior-tested states remain distinct. No client plugin installation is attempted.

IDEA_SOURCE: user's seven explicit workflow requirements, existing Forge C++ Lab and past QA corrections.
