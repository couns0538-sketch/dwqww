# IDEA_SOURCE — S14 (allocation-free MovePicker + mailbox piece_type)

- **Job:** `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2, Sol's S14 (spec in his inventory on `17aa0cae`).
- **Static audit (`picker_audit.py`, tests, planted bugs):** our own tool. It reads the disassembly of the PC lock exe
  and the AL1 source; no outside code. Sol's 47 pure tests were run as he delivered them (read from `17aa0cae`).
- **Follow-up (`followup_zerofill/`):** its own `IDEA_SOURCE.md` covers the zero-fill switch, the pick-order oracle
  adapted from Sol's S14 oracle, the codegen tool from O3 and the CI/NPS pattern from offguard.
- No code or tuned values from another engine; no Elo claim.
