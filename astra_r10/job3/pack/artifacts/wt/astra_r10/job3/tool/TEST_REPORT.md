# Owned converter/relabel checks — UNPROVEN

Frozen source: `d8982bc0`, original hashes in `SOURCE_COPY.json`.

- RED: `red01-launch/result.json`, native exit 1. Two required new contracts
  failed on unchanged owned copies: absent `full_state` API and absent
  `Config.state_manifest`. One earlier launcher preflight rejected a missing
  explicit executable read path; no process ran in that attempt.
- GREEN: `green01-launch/result.json`, native exit 0, Idle priority, CPU2
  affinity, one worker. `green01-launch/stderr.log` records 14 discovered
  methods: **13 passed, 1 skipped**. The original `green01/result.json` does not
  include a skipped-count field; interpret it together with the transcript.
- The skipped method was REC converter byte/FEN/ID parity, initially awaiting
  numpy in a D-only CPU runtime. GREEN02 below resolves that missing check. The test runner's subsequent
  self-review fix replaces a decorator that would otherwise continue skipping
  when enabled, and adds explicit skip accounting to future receipts.
- The passing round-trip uses the real `relabel_positions.run` and PosWriter
  with `FixtureProbePool`. It is protocol/format evidence, **not native engine
  analysis or genuine relabeled training data**. Its `SCOPE.json` states this.
- The three full FENs include castling rights, legal noncapturable EP, capturable
  EP and nonzero clocks. FENs reach the fixture pool and return byte-exact in the
  emitted `.fen`. One supplied game ID survives; two missing IDs remain unknown.
- Negative cases detect a corrupted binary, reordered/truncated metadata,
  wrong/unpinned manifest hash, output reuse, reconstructed-state promotion,
  stripped castling on an unselected row and stripped noncapturable EP.
- Baseline and changed default relabel routes produce identical `.pos`, `.hce`
  and `.fen` bytes. Existing 73-test execution is a separate parent-owned check.

Focused review identified three confirmed issues: a separate hash/read race in
manifest and metadata consumption, Windows ADS filenames reaching filesystem
access, and loss of an explicit Lichess `game_id`. RED02 first demonstrated all
four targeted failures (the hash/read race has separate manifest and metadata
tests), exit 1, with original evidence retained.

The fixes parse the hashed manifest bytes, hash the exact metadata bytes consumed,
recheck all input identities before return, refuse ADS/path aliases, and preserve
only explicitly supplied game IDs. A separate mutation test changes a disposable
binary copy after row consumption and verifies the final identity guard catches it.

GREEN02 (`green02-launch/result.json`) exited 0 on the copied D-only Python
3.10 CPU runtime: **19 tests passed, 0 skipped**, Idle priority, CPU2, one worker.
The converter check compares frozen d8982bc0, changed default, and opt-in
`--keep-fen` train/val binary bytes exactly using experiment seed `4803011981`.
It verifies all original full FENs and the one supplied game ID in emitted state
manifests. Missing IDs remain unknown. No training or native probe is invoked.

Candidate SHA256 values for this milestone:

- `full_state.py`: `6F764190B8EB13D8976BEDFBF446FACC5225B91ADE001849C3B38FB9031DBD27`
- `datafilter/convert_forge.py`: `73061059C96427B1DB2C875718F3EED0E44027A0FD72FB6C6EA3ED7A35B56FDB`
- `datafilter/records.py`: `DB114D5FD4368759926E13DC0EA2BD99A060F6B387B35979A16D3C75B00CF408`
- `data/relabel_positions.py`: `0CFD0BE703E85EC5D814137F4C382533E837259C5C41D931D79988BD82240EF7`
- `test_state.py`: `39D2E4F76E1C8369F8E0F0DC5A5AA1CEC498381F4FAC7C19987137591D177531`

No native relabel, training, GPU work, matches or strength claims occurred in
these tests. Next: reviewer recheck of the substantive fixes, parent-owned 73-test
regression and separate real-adapter restart proof. Corpus holdout clearance and
authentic game-ID completeness remain separate, never implied by these fixtures.
