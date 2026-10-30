# Optional binpack decoder CRLF transport regression

The converter compared decoder stdout bytes directly with canonical LF sidecar
lines. A Linux fixture executable emitting literal Windows-style CRLF reproduced
rejection of otherwise identical records. The pre-fix run has two failures and
21 passing tests; its source and raw logs are preserved here.

Verification now changes only one terminal CRLF pair to LF on each decoded
line. FEN, score, result, embedded carriage returns, and all other whitespace
still receive exact byte comparison. Extra rows and unterminated final rows
remain rejected. The seven new cases cover the valid transport and these
corruptions. Output encodings, sealed files, conversion counts, and disk/index
behavior are unchanged.

`green_all_data2.stderr`: 93 tests passed with the external native adapter
explicitly enabled. `native_linux_verify.stdout`: the real native adapter decoded
the previously sealed one-row binpack and passed exact sidecar comparison.
These are Linux tests; Windows runtime remains unverified.

Source SHA-256 before this change:
`563f638bb6c2293ca06e01c5917851562b7694483c71c329c8c5c99aa1a6171e`

Source SHA-256 after this change:
`2adda9552fdd43c9e7d87f295a4ec9eefd6a3a90c23fa9b84329f9b0bdfa7ff4`

Earlier bounded disk measurements and their recorded source hashes remain
historical evidence; this follow-up changes only optional decoded-line comparison.
