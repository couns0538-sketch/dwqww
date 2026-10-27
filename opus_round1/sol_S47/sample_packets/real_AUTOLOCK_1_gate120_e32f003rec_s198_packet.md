# AUTO-LOCK audit packet: AUTOLOCK_1_gate120_e32f003rec_s198

Tool: S47 autolock_audit 2026-10-27 v1. Old lock: `F:\opus_scratch\sol_s47\real\old_h256_e12`. New lock: `F:\opus_scratch\sol_s47\real\AUTOLOCK_1_gate120_e32f003rec_s198`.

**Overall: INCOMPLETE**. Evidence for Code Review only: this packet is NOT a CR approval and the tool never writes CR_PASS_AUTOLOCK_<n>.txt. MISSING means the input was not supplied or not found; nothing is guessed.

| id | check | status | evidence |
|---|---|---|---|
| A1 | new lock in a NEW dir AUTOLOCK_<n>_<tag>, consistent LOCK.json, no orphan lower-n dir | PASS | name n=1, old lock h256_e12 n=0; LOCK.json n 1 tag AUTOLOCK_1_gate120_e32f003rec_s198 parent h256_e12 kind net; sibling AUTOLOCK dirs: ['AUTOLOCK_1_gate120_e32f003rec_s198'] |
| A2 | old lock files unchanged (sha256 vs the hash list recorded before the promote) | PASS | 73 listed files re-hashed under F:\opus_scratch\sol_s47\real\old_h256_e12\source; changed none; missing none; old exe forge_h256_e12.exe 456743d9c065d2dec2d9a52ef23992f36908efc1243b6916edab9a8ab3c7fdfa vs recorded 456743d9c065d2dec2d9a52ef23992f36908efc1243b6916edab9a8ab3c7fdfa |
| A3 | net md5 = the gated pack net | PASS | nnue_weights.inc md5 22b4b9e2c61b37c0450f13a3a92c19b3; gated pack net 22b4b9e2c61b37c0450f13a3a92c19b3 |
| A4 | exe sha256 = the gated exe (gate and confirm RUN_INFO) | PASS | forge_h256_s198.exe 833c47f3209dceecf662e8b1d4587435e44702fbd3ab9ddf278a49172d9122b3; gate RUN_INFO candidate 833c47f3209dceecf662e8b1d4587435e44702fbd3ab9ddf278a49172d9122b3; confirm RUN_INFO candidate 833c47f3209dceecf662e8b1d4587435e44702fbd3ab9ddf278a49172d9122b3 |
| A5 | bench d11-d22 node-exact, run twice identical | PASS | runs [[312866, 862329, 3024920, 12389307, 34048354], [312866, 862329, 3024920, 12389307, 34048354]]; = gated prebench [312866, 862329, 3024920, 12389307, 34048354]; differs from old lock bench [308972, 745494, 2460422, 11901452, 31111774] |
| A6 | perft5 4865609 / kiwipete5 193690690 / FMA 0 | PASS | perft5 4865609 kiwipete5 193690690 FMA 0 |
| A7 | uci option list equal to the old lock | MISSING | new list found (F:\opus_scratch\sol_s47\real\AUTOLOCK_1_gate120_e32f003rec_s198\UCI_OPTIONS.txt); old list MISSING (F:\opus_scratch\sol_s47\real\old_h256_e12\UCI_OPTIONS.txt) |
| A8 | confirm srand and openings start differ from the gate | PASS | gate srand 344808634 start 321001; confirm srand 1983003762 start 348001 |
| A9 | gate and confirm verdicts H1 accepted, not VOID | PASS | {'gate': 'H1 accepted (SPRT [0,10] normalized, a=b=0.05: no measurable regression; not an Elo claim; needs a confirm gate before lock)', 'confirm': 'H1 accepted (SPRT [0,10] normalized, a=b=0.05: no measurable regression; not an Elo claim; needs a confirm gate before lock)'} |
| A10 | pins unchanged except allow-listed reviewed diffs (attached, not applied) | PASS | no pins/ attachments in the new lock; no tests/ tree in both lock dirs (pins live in the engine repo; nothing applied here) |
| A11 | Code Review record (INFO only; this tool never writes or grants CR_PASS) | INFO | CR_PASS_AUTOLOCK_1.txt present (sha256 169011e56790fdc8...); CR decides, not this tool |

## Missing (flagged, not guessed)

- A7: new list found (F:\opus_scratch\sol_s47\real\AUTOLOCK_1_gate120_e32f003rec_s198\UCI_OPTIONS.txt); old list MISSING (F:\opus_scratch\sol_s47\real\old_h256_e12\UCI_OPTIONS.txt)

## Inputs (read-only)

- confirm RESULT.md: `F:\opus_scratch\sol_s47\real\g120c\RESULT.md` sha256 0cc1c5dac3414611ce2945a004e7f423e88b5e8a78eaedafbc53da74f619cd2a (2689 B)
- confirm RUN_INFO.json: `F:\opus_scratch\sol_s47\real\g120c\RUN_INFO.json` sha256 a60b51766090bf6a9d9eb6c31c90e2513f8f71c6b308457a1216c212ef5e61af (3587 B)
- confirm record: `F:\opus_scratch\sol_s47\real\g120c\record.json` sha256 998d88ecbb4c1b06f5e04dd64a9a3de8155735db0a0c583b5b7491d3d6850ebe (296 B)
- gate RESULT.md: `F:\opus_scratch\sol_s47\real\g120\RESULT.md` sha256 906f1cad790d0859cd51629a3683a2e4cf7d15b93dbe7d43d7e243b232fc7274 (2643 B)
- gate RUN_INFO.json: `F:\opus_scratch\sol_s47\real\g120\RUN_INFO.json` sha256 6681a5f5f6836e218c98636b467e3baac7aa9b871f5feccddf4aa5d2aee8c159 (3542 B)
- gate record: `F:\opus_scratch\sol_s47\real\g120\record.json` sha256 c9f14059fd77cd7dad76d1e8494741aa5808c3d4fe0647ca317fa98548a2f629 (287 B)
- new LOCK.json: `F:\opus_scratch\sol_s47\real\AUTOLOCK_1_gate120_e32f003rec_s198\LOCK.json` sha256 8ed6f16fd7888f6a7c1f4726328a72c9c0368b3f79885626335f31208cc8c8ec (10125 B)
- old LOCK.json: `F:\opus_scratch\sol_s47\real\old_h256_e12\LOCK.json` MISSING
- old bench reference: `F:\opus_scratch\sol_s47\real\g120\PREBENCH.txt` sha256 c9f6cf37f5045380ec83017f28720bd7f1da796d2692cb3615f5c6831a51eac4 (393 B)
- old hash list: `F:\opus_scratch\sol_s47\real\h256_e12_sources.sha256` sha256 44f18e7f4558f44a4fe3bdcb5c4a5b40bbcdf826593eb82ddddd2c8bab56851e (6719 B)
- pin allow-list: `F:\opus_scratch\sol_s47\real\pin_allow_e48f006.json` sha256 295a0671d4a567118e3bcabc79142a4dba04186b8d15cddab1b261e9fa6a1cbd (281 B)
