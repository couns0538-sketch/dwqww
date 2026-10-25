# S02 v2 source-hash correction — 2026-10-25

The report in commit `9999b5a20bda52eded802dc56f49e90a2b4fe019` contains a reporting error: two copies of the merged `tests/tests.cpp` SHA256 were shortened to 61 hexadecimal characters. I missed this in the report review.

The correct full SHA256, calculated directly from the supplied current L-prime source, is:

`55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c`

The native source bindings and six profile results use the correct file identity. No source or result changed, and no engine rerun is needed. The original report and sealed package remain unchanged. The accompanying proof records the original report hash, both malformed literals, direct source calculation and before/after checks.

This corrects documentation only; speed and Elo remain UNPROVEN.
