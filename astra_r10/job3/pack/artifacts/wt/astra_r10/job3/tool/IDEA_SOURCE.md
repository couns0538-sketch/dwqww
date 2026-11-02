# Sources

- Same Forge repository, frozen source commit `d8982bc0`: the seven copied files
  are individually identified in `SOURCE_COPY.json`. Original docstrings and
  notices are retained. `filter_lichess_rec.py`, `signcheck.py`,
  `forge_pos.py` and `forge_probe.py` are copied without source changes.
- R10 original glue: `full_state.py`, regression tests, explicit JSON game-ID
  retention in `records.py`, and optional converter / relabel interfaces.
  Uses Python standard-library hashing, JSON and hard links;
  the installed python-chess package is imported, not copied.
- No GPL/AGPL implementation, constants or translated code were copied. No
  installed npt code was copied or changed, and no P5 work was included.

All strength claims: UNPROVEN.
