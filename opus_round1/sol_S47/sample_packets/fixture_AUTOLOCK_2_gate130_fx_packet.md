# AUTO-LOCK audit packet: AUTOLOCK_2_gate130_fx

Tool: S47 autolock_audit 2026-10-27 v1. Old lock: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\locks\AUTOLOCK_1_gate120_fx`. New lock: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\locks\AUTOLOCK_2_gate130_fx`.

**Overall: ALL_CHECKS_PASS**. Evidence for Code Review only: this packet is NOT a CR approval and the tool never writes CR_PASS_AUTOLOCK_<n>.txt. MISSING means the input was not supplied or not found; nothing is guessed.

| id | check | status | evidence |
|---|---|---|---|
| A1 | new lock in a NEW dir AUTOLOCK_<n>_<tag>, consistent LOCK.json, no orphan lower-n dir | PASS | name n=2, old lock AUTOLOCK_1_gate120_fx n=1; LOCK.json n 2 tag AUTOLOCK_2_gate130_fx parent AUTOLOCK_1_gate120_fx kind net; sibling AUTOLOCK dirs: ['AUTOLOCK_1_gate120_fx', 'AUTOLOCK_2_gate130_fx'] |
| A2 | old lock files unchanged (sha256 vs the hash list recorded before the promote) | PASS | 4 listed files re-hashed under F:\opus_scratch\sol_s47\ev_36837\sp\partB\locks\AUTOLOCK_1_gate120_fx\source; changed none; missing none; old exe forge_fx_old.exe 2d4ae20f0f719aad018af6a80bfa0d16377c2c7677017005a4f31faff70ede46 vs recorded 2d4ae20f0f719aad018af6a80bfa0d16377c2c7677017005a4f31faff70ede46 |
| A3 | net md5 = the gated pack net | PASS | nnue_weights.inc md5 d8867c5ba5b0ad2d2c8123d6a2a8eb85; gated pack net d8867c5ba5b0ad2d2c8123d6a2a8eb85 |
| A4 | exe sha256 = the gated exe (gate and confirm RUN_INFO) | PASS | forge_fx_new.exe 0bb063723cdad670a18df5b04a89843480156035b76eaff19f458bb625169aaa; gate RUN_INFO candidate 0bb063723cdad670a18df5b04a89843480156035b76eaff19f458bb625169aaa; confirm RUN_INFO candidate 0bb063723cdad670a18df5b04a89843480156035b76eaff19f458bb625169aaa |
| A5 | bench d11-d22 node-exact, run twice identical | PASS | runs [[445320, 1123540, 4197338, 14179708, 28577307], [445320, 1123540, 4197338, 14179708, 28577307]]; = gated prebench [445320, 1123540, 4197338, 14179708, 28577307]; differs from old lock bench [312866, 862329, 3024920, 12389307, 34048354] |
| A6 | perft5 4865609 / kiwipete5 193690690 / FMA 0 | PASS | perft5 4865609 kiwipete5 193690690 FMA 0 |
| A7 | uci option list equal to the old lock | PASS | 3 new / 3 old option lines |
| A8 | confirm srand and openings start differ from the gate | PASS | gate srand 344808634 start 321001; confirm srand 1983003762 start 348001 |
| A9 | gate and confirm verdicts H1 accepted, not VOID | PASS | {'gate': 'H1 accepted (SPRT [0,10] normalized)', 'confirm': 'H1 accepted (SPRT [0,10] normalized)'} |
| A10 | pins unchanged except allow-listed reviewed diffs (attached, not applied) | PASS | e48f006_pin_rerecord_PROPOSED.diff = allow-listed reviewed diff a1df583a... (attached, not applied); tests/ identical (1 files) |
| A11 | Code Review record (INFO only; this tool never writes or grants CR_PASS) | INFO | CR_PASS_AUTOLOCK_2.txt not found in F:\opus_scratch\sol_s47\ev_36837\sp\partB\cr; CR decides, not this tool |

## Missing (flagged, not guessed)

- none

## Inputs (read-only)

- confirm RESULT.md: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\confirm\RESULT.md` sha256 f7fd997421f40833ef3f24347b65e3a61d42094ea2a60c87f93dc4c6eae46441 (143 B)
- confirm RUN_INFO.json: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\confirm\RUN_INFO.json` sha256 b9b4d94984008cf8a7f933262c3f2516ae63c93922aa4aa37ff7b5a586ae2415 (283 B)
- confirm record: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\confirm\record.json` sha256 192cbf817f839ce47e5f7920f3655047009ef9f2962f21ef5e3bd0e8024ab9b2 (181 B)
- gate RESULT.md: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\gate\RESULT.md` sha256 9e98a13890b582c2cac5a8e1f8d11f5f592fa0da1e93f556a7213179e9b5dde4 (134 B)
- gate RUN_INFO.json: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\gate\RUN_INFO.json` sha256 10c462a250b3035ad5c15b2edffe31beaec6517a896a235bb4e0fcec1123263b (282 B)
- gate record: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\gate\record.json` sha256 70cb0a04516f183002f04b0b445b4115cf78c03b483079c40f9258f9498cdc16 (172 B)
- new LOCK.json: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\locks\AUTOLOCK_2_gate130_fx\LOCK.json` sha256 41dfed5c2df3a38cead3df3867a812c780a55ed9025c44a3056550d3fc2fb3ed (583 B)
- old LOCK.json: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\locks\AUTOLOCK_1_gate120_fx\LOCK.json` sha256 5ef710be6ac0aabcae6cb7eafe5c49ec55b98f027bdfb996f8bee2b071af4114 (343 B)
- old hash list: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\locks\AUTOLOCK_1_gate120_fx\SOURCES.sha256` sha256 3a27ac7adbe625fcbc070e5ef00af4c4f65bbfd72f34ed042338b722951d6616 (333 B)
- pin allow-list: `F:\opus_scratch\sol_s47\ev_36837\sp\partB\pin_allow.json` sha256 27bbd8badf6ef9a201792aa3acf1dc7cdd48ca00d597ffad2c20a22e414ff643 (134 B)
