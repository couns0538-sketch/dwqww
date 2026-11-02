# R13 Phase 5 - relabel pipeline - RUNNING (UNPROVEN)

- relabel_job.py: sharded, resumable Windows driver (Idle, CPU 3, 1 worker, run id r13p5-20261101-a) around Astra's relabel_positions / forge_probe (unchanged copies).
- Input: D:\grok-pc-data\r11_nnue\astra\forge_filtered.pos (9,206,371 rows, Astra's filtered 10M slice), reconstructed FENs (no sidecar extracted), 20k nodes, shards of 20,000 rows.
- Probe: forge_data_probe.cpp built against the lock source d4f4312 (znver5, static), sha256 ed76de96..., 1 harmless warning (NOMINMAX redefined).
- Job dir C:\o13\p5\job1 (job.json, status.json, shards.tsv with per-shard output sha256 + run id). Started 2026-11-01 ~11:10, runs until 12:25.
- TODO: positions/hour from status.json, 50M cost, RELABEL_HANDOFF.md.
