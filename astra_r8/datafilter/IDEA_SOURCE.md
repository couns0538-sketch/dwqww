# Idea sources and licence boundary — UNPROVEN

Credit Code Review and Engine Coder for filtering proposals, and Engine NNUE for
result-aware training and the w4/s12 baseline recipe. Couns supplied the acceptance
criteria, execution limits and review/fix/verification policy.

The production converter at `C:/Users/Administrator/grok-pc/nnue/convert_forge.py`
and its two owned helpers were copied under the explicit task authorization.
Their exact original bytes and SHA256 values are preserved in `baseline/` and
`evidence/baseline_hashes.json`. These source files contain no licence notice;
we do not invent a permissive third-party licence for them or authorize external
redistribution. No third-party permissive implementation was copied.

Normalization, filtering, adapter, audit and tests in this directory are original
task code. The installed python-chess, NumPy, PyTorch, psutil and npt packages are called
through their APIs, not vendored. In particular, no GPL/AGPL npt, Stockfish,
binpack-tool or Leela/Lc0 implementation was copied into Forge. Native npt feature
extraction, model and loss remain in their separately installed environment.

Data used by the matched recipes is owned Forge self-play text, closed shards
001 then 002.
Holdout sources are the complete owned shards 013 and 014, read only. No external
Lichess corpus is included: handling is demonstrated with authored synthetic
records and unknown outcomes. No Leela/Lc0 data is used; uncertain-licence data
is excluded. No claim is made that an arbitrary Lichess dump is licensed merely
because the parser can read it.

The six-hour descriptive audit expands read-only inspection to all 37 closed
owned self-play shards 001–039 excluding 013/014. Producer MD5 sidecars, full-source
SHA256 and source identities are recorded. Audit reservoirs are evidence only;
the ready-to-run recipes retain the original cleared 001/002 cohort above.

This work does not modify FD3A5190. The task lock is OFF bench
312866/862329/3024920/12389307/34048354. The first follow-up used a bounded UCI
handshake. The later 30-minute audit also reproduced all five bench counts and
62 perft2 results on the exact executable, with the crew's recorded options.
The six-hour continuation expands that proof to 9,486 perft2 checks from the
4,736-row all-source reservoir, seven edge cases and their mirrors, and repeats
all five bench pins. Original-line label replay separately verifies the reservoir.
That establishes those compatibility checks, not full engine or strength qualification.

The separate capture audit uses completed owned Forge gate PGNs under
`F:/forge_push/`: uhoT2_sf26b14, uhoSF26bit1_razor_e417_vs_AL1lp,
uhoE3a_evalmatscale12_vs_AL1lp, uhoE3b_evaloptimism40_vs_AL1lp and
uhoE3c_evalrule50damp30_vs_AL1lp. Their original RUN_INFO/RESULT receipts,
UHO opening provenance, entire source hashes and source-row identities are
retained in the new capture manifest. Only exact-baseline searched moves qualify;
no external corpus is imported and these positions are not training inputs.

Fastchess's local MIT-licensed source was inspected to establish that stored
bestmove/score/depth describe the position before the played move. No Fastchess
implementation was copied. `audit_capture_cohort.py` records source paths and
SHA256 values for match.cpp, pgn_builder.cpp, uci_engine.cpp and LICENSE under
`C:/Users/Administrator/grok-pc/tools/fastchess`. This source inspection does not
relicense other datasets or authorize copying GPL/AGPL implementations.

The strict PGN preflight is original code. The installed python-chess parser and
its public visitor API were inspected, along with [upstream parser documentation](https://github.com/niklasf/python-chess/blob/master/chess/pgn.py)
via Context7, to understand forgiving recovery and variant handling. No parser
implementation was copied; the library still handles SAN legality and game trees.

The additional developer-tool investigation is documented in
DEV_TOOLS_RESEARCH.md. Ruff (MIT) is used from its existing installation.
Hypothesis 6.170.14 (MPL-2.0), Coverage.py 7.17.0 (Apache-2.0) and
sortedcontainers 2.4.0 (Apache-2.0) are separate, unmodified test-tool packages
under C:/astra8_data/extension3h_20261103, with complete wheel licences preserved.
They are not vendored into this repository or Forge; the generated-case harness
and regressions are original task code. Exact download URLs, SHA256 values and
sizes are retained in tools_install.json. No GPL/AGPL engine/training code or
external chess dataset was copied for these checks.

Pyright 1.1.414 (MIT) is a separate unmodified developer tool, extracted under
the C: artifact root from its exact public npm archive after SHA512 integrity
verification. Full package licence and third-party notices remain with the
tool; no implementation is copied into Forge or this repository. The isolated
installer and receipt retain the URL, SHA256, size and method; lifecycle scripts
were not run. Existing Node is used without global package installation.
The added native/PGN boundary fixtures are original synthetic test inputs and
are never included in training recipes or described as genuine game outcomes.

The [official Lichess database page](https://database.lichess.org/) states:
“Database exports are released under the Creative Commons CC0 license.”
This identifies that export's data licence, not the licence of Lichess's code
or an arbitrary third-party mirror. No external corpus has been downloaded or
added to these recipes. Lichess exporter/eval-cache source was inspected to
establish field semantics and White-relative scores; its AGPL implementation
is ideas-only and was not copied. Exact source links and inspected blob IDs,
along with the unresolved four-field FEN limitation, are recorded in
LICHESS_INPUT_REVIEW.md. The repair fixtures remain authored synthetic data.

Installed npt `data_loader/cpp/lib/chess.h` and its C ABI wrapper were inspected
to establish actual FEN parsing, failure handling and counter widths. Their
implementation remains separately installed and unchanged; no GPL/AGPL source
is copied. The boundary repairs use original Python validation/argument
construction in the local adapter, documented in NATIVE_INPUT_REVIEW.md.
