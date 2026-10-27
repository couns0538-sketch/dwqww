# C1 — idea and format sources

Job C1 adds an own Syzygy tablebase reader and probing (UCI `SyzygyPath`, `SyzygyProbeDepth`,
`Syzygy50MoveRule`). No probing code was copied: no Fathom, no Stockfish `tbprobe`, no python-chess,
no other probing library. The data structures, the parser with its bounds checks, the decoder,
the capture resolution, the DTZ rounding bookkeeping, the root ranking and the search glue are
written for Forge (`src/search/syzygy.inc`, `src/search/tablebase.inc`).

## File format
- **R. de Man (user "syzygy"), "Looking for a specification for Syzygy tablebases", TalkChess,
  15-16 Oct 2022** — https://talkchess.com/viewtopic.php?p=936095 and
  https://talkchess.com/viewtopic.php?p=936110 (read during the job). The public description
  of the WDL file structure used here: magic numbers; header byte 4 (bit 0 non-symmetric = separate
  wtm/btm tables, bit 1 pawns, bits 4-7 piece count); order nibbles and piece nibbles
  (P=1 N=2 B=3 R=4 Q=5 K=6, +8 for black) per table, lower nibble wtm, upper btm; one table per side
  and, with pawns, per file a-d of the leading pawn; 2-byte alignment; per table: flags, block size,
  index bits, padding blocks, real block count, canonical Huffman code lengths (max_len, min_len,
  one u16 per length), RePair code book (symbol pairs as two 12-bit halves, terminal symbols with
  0xfff); constant tables (flag bit 7, value in byte 1); the 6-byte sparse index entries (block
  number u32 + offset u16 of the value in the middle of each 2^idxbits section) and how a probe
  walks the u16 block sizes (values per block minus 1) from there; 64-byte alignment of the data;
  the 16-byte checksum at the end.
- What that post leaves out ("the nibbles in the first byte are important for mapping positions to
  an index value, but I won't get into this detail now"; the DTZ-specific flags and value maps) was
  written from my own understanding of the publicly documented Syzygy format, then verified
  empirically rather than trusted:
  - every one of the 290 files of the 3-4-5 set parses, and its computed sections end exactly at
    the 16-byte checksum (264 files) or at 32 bytes of 64-byte padding plus the checksum (26 files)
    — this checks the index sizes of every table (`forge_syzygy_tests`, "file layout");
  - 1468 positions over all 145 materials, with every root move, agree exactly with an independent
    reference prober (below), and 370 positions agree with the lichess API up to the documented DTZ
    rounding.

## Probing rules and engine use
- **Chessprogramming wiki, "Syzygy Bases"** — https://www.chessprogramming.org/Syzygy_Bases :
  WDL tables double-sided and used in the search, DTZ tables single-sided and used at the root
  (DTZ50 metric), do not probe in quiescence search, root strategy (search the winning moves while
  progress is made, watch repetitions and the 50-move counter, then play DTZ-optimally).
  **CPW, "Endgame Tablebases"** — https://www.chessprogramming.org/Endgame_Tablebases (general).
- **syzygy-tables.info, "Metrics"** — https://syzygy-tables.info/metrics : WDL50 categories (cursed
  win, blessed loss) and DTZ50'' with rounding. (The page sits behind a bot check for scripts; the
  semantics were confirmed against the lichess API, which reports them per position.)
- **R. de Man, probetool announcement and replies, TalkChess, Oct 2025** —
  https://talkchess.com/viewtopic.php?t=85522 : "When the root is draw, you can do a regular search
  (but without TB probing) on all moves that draw ... The idea of the rank is that you do a regular
  search on the set of moves with the highest rank." Used for the root filter (search only the
  best-ranked moves; no in-search probes when DTZ ranked them).
- Capture resolution (stored values may be "don't care" where a capture is best; en passant is not
  in the index), probing only right after a capture or pawn move, never with castling rights, TB
  win scores just below the mate range, the TT store of a probe result, and DTZ ranks that let the
  search choose among certain wins until a repetition or the 50-move counter forces DTZ order:
  public engine practice described on CPW and in the TalkChess discussions above; ideas only, own
  constants and code.

## Known answers and tools
- **lichess tablebase API** — https://tablebase.lichess.ovh/standard?fen=… (public, queried one
  request at a time, at least 1 s apart, cached in `api_cache.jsonl.gz`): category (with the FEN's
  50-move counter), dtz, precise_dtz, dtm, per-move values → `tests/syzygy_fixtures.tsv`.
- **Table files**: public mirror http://tablebase.sesse.net/syzygy/3-4-5/ (290 files, md5-checked
  against the mirror's `checksum.md5`), stored outside every repository; CI fetches the 3-4 piece
  subset the same way (`ci_fetch_tables.sh`).
- **Reference prober for cross-checking**: python-chess 1.11.2 (`chess.syzygy`,
  https://github.com/niklasf/python-chess, GPL-3.0), installed into a scratch folder and used only
  as an external test oracle to produce `tests/syzygy_reference.tsv` (FEN + numbers). None of its
  code is in the engine or the repository.
