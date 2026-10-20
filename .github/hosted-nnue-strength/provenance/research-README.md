# Frozen prospective opening input

Recommended source: official-stockfish/books `8moves_v3.pgn.zip`, commit
`a804a97e709f40aa75a00f9d19e84915b7a3a45c`, file blob
`572bcf2eff104c51c64e796313f0589ce97e7044`.

Archive: 807,558 bytes; SHA256
`7e1e9dd118b4bb97d8a8b5b8a790c86e21f8509d59a27d2883767d94477be02e`.
PGN: 8,037,438 bytes, 416,400 newlines; SHA256
`5835239f88cc2c7511b177c32392a69f3ede21819cf0616f80a7f907cd21d17e`.
Upstream root LICENSE is CC0-1.0 and is preserved as `LICENSE-upstream`, alongside
the upstream README and metadata. Attribute the suite to Stockfish developers /
official-stockfish/books; the first PGN headers identify Stockfish versus
Stockfish dated2013.11.02, with no individual author named in the README.

Python-chess1.11.2 replayed all34,700 games; all have16legal plies and valid
nonterminal final boards. All34,700 four-field final positions are unique.
3,097 have an actual final EP square and were excluded without alteration.
31,603 positions already have EP='-' under strict FEN semantics and remain after
excluding42 discovered workspace registries, all historical frozen tails, and
the explicit new164position confirmation selection. Overlap is zero.

`report.json` preserves registry paths/hashes and the complete prospective
selection. The fixed seed is
`20261019-official-stockfish-8moves-v3-long-strength-v1`.
Rank by ascending SHA256(UTF-8 seed + LF + unchanged four-field final FEN).
First4 positions are prospective A/A; next1024 are prospective SPRT opening
pairs. These1028 positions are reserved together; do not reselect after outcomes.

`prospective-aa.epd`: SHA256
`38942f59ae6885cde300a058ef1a74aecb26e84395ee0f95357217772964d768`.
`prospective-sprt.epd`: SHA256
`6ed9523af006b3b0889b6bfe4aa5a1f3c481d45bfac13913afda151a7b7f9e20`.

This is input prerequisite research only. No match, workflow, engine evaluation,
build, repository edit, branch, commit or launch was performed. Engines, clocks,
calibration and stopping rules still require a separate frozen protocol. The
suite is not claimed to be balanced or a representative human opening sample.

The unauthenticated GitHub API request was denied; the public shallow filtered
Git route succeeded. Only commit/tree metadata, README, LICENSE, books.json and
the small8moves archive were fetched. Fetched Git object directory size is
823,729bytes, comfortably below the32MiB download budget. Expanded PGN bytes are
local decompression. Reproduction script is `check_openings.py`; it reads the
workspace registries and writes only into this research directory.
