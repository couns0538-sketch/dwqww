# Native full-state relabel proof — UNPROVEN

The reviewed harness ran successfully under the full protected-roots launcher:
`run01-launch/result.json`, exit 0, Idle priority, CPU3 affinity, one worker,
no capture errors or disk-floor breach. Main agent performed the launch; this
agent did not launch a duplicate run.

Candidate harness SHA256:
`C27384266D2938259EE562CD56B8B0E875FEFA7C2586E2663A6B52580F30545F`.
The focused reviewer caught two `utf8-sig` codec spellings before execution;
both were corrected to `utf-8-sig`. No other blocking defect was identified.
Production converter/relabel/state files were unchanged by this proof.

Input: frozen `source001/forge_selfplay_001.txt`, SHA256
`de27d81720c0e33f10e0fa95e48b1f619b1325bf35675cd2fcd016fe48f338a2`.
The first 16 physical rows passed legal/nonterminal selection. Each row retains
its physical source index, original raw-line hash and source-file hash. No
shuffle or random seed was used. All 16 authentic game IDs are missing and remain
**UNVERIFIED**; physical row numbers are not game identities.

The actual auxiliary native probe SHA256 is
`64b8199ebe4368f1935d1d855bdffa14a83e9ff7b63fa936dba2cf910b251616`.
`--version` returned protocol `forge-data-probe-v1`, T1, default OFF options.
The previous build diagnostic `--describe` exited 2 because that flag is invalid;
its original logs remain preserved. This is auxiliary tool qualification, not a
kit candidate build or an engine-strength handover.

The probe was built against the frozen AL1/R9 `D:/a10/c1` source with the existing
`forge_data_probe.cpp`; the build receipt reports input hashes unchanged. The
recorded command uses `-std=c++20 -O2 -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off
-fno-fast-math -march=znver5 -static -pthread`. Compiler, translation units,
headers and embedded-table hashes are bound in `probe01/command.json`. The sole
compiler warning was the benign `NOMINMAX` macro redefinition; its original
stderr is preserved. No rebuild or production-source modification was performed.

The real `relabel_positions.run` used its unchanged native `ProbePool` path:
2,048 nodes per position, T1, Hash1, 16 requests and responses, process exit 0,
binary unchanged. Total work was 32,768 nodes; completed search depths were 4–7.
No fixture factory, training or GPU was involved.

All six FEN fields match the source exactly after relabeling: **0 mismatches**.
The sample includes 15 positions with castling rights and 3 with legal
noncapturable EP squares. Capturable EP coverage is zero in this native sample;
the separate fixture suite covers that case. Original rights and clocks survive.
Neither budget nor this small sample establishes label quality or Elo.

Evidence under `D:/a10/job3/native-relabel01/`:

- `REPORT.json`: `A459B3CA75087969E76018E72D0ABE9E662DD177A29A9FA03DC82F4FF3200B78`
- `input-provenance.json`: `3F91A1C9CA242D006D6A31CBD6E78ACF22663B759FED175E986ECE4C399C1803`
- `relabel/relabeled.pos`: `055a98f4b2d4ce8fa83802e00a2695d8b907e50eb992c72bf6a45cfcc7b8175d`
- `relabel/relabeled.fen`: `56ae676834d7f4c079438b5ee1b74ab555244888fb7c23f2379a6d42bc3cc35d`
- `relabel/relabeled.hce`: `4afa501d1f55c87f6834563db06c1cb7bf3860e5699c8850928755774c5022ac`

The provenance receipt is ready for the separate real-converter restart proof
with `upstream_scope=native-relabel`. The earlier three-row resume proof remains
correctly attributed to the GREEN01 fixture-probe output. Neither run supplies
complete holdout or authentic game-ID clearance. All strength claims: UNPROVEN.
