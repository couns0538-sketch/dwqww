# IDEA_SOURCE - SingularNonCut (deep-research card T04-01)

## Source
- Engine: Caissa (Witek902/Caissa), MIT licence.
- Commit: 1b7a871236e20d85fd193f07bb2a62dceb2f9e35 "Search: Run singular search as non-cut-node"
  (author date 2025-12-28 21:31:39 UTC), https://github.com/Witek902/Caissa/commit/1b7a871236e20d85fd193f07bb2a62dceb2f9e35
- Its OpenBench block (from the commit message, Caissa's own result, not a Forge result):
  10.0+0.10 s, Threads=1, Hash=16MB, SPRT [0.00, 2.00], LLR 2.94, N 25,044 (W 5993 L 5690 D 13361),
  Penta [78, 2877, 6347, 3104, 116], Elo +4.20 +- 2.23 (95 %). No LTC run is logged.
- Found by the research job: branch opus-deepres-20261104 (tip 2231439c), card
  `opus_deepres/cards/T04/T04-01-singular-search-noncut.md`, spec `opus_deepres/notes/SPEC_SEARCH.md` section
  "T04-01 SingularNonCut". The licence row is in `opus_deepres/notes/T04/licences.md` (Caissa @57cae7ef71: MIT).
- Licence re-read for this job at the idea commit itself (`gh api repos/Witek902/Caissa/contents/LICENSE?ref=1b7a871...`,
  2026-11-06 01:2x PC clock): MIT, text below.

## What was taken
The idea only. In Caissa's diff (`src/backend/Search.cpp`, singular-extension block of `NegaMax`) the node's cut-node
flag is set to false for the singular verification search and restored afterwards. Forge's version is own code: one
argument of the verification call `search(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node)`
becomes `false` when the new option `SingularNonCut` is 1. `cut_node` is a by-value parameter in Forge, so nothing has to
be restored. No Caissa code, names, constants or comments are copied. No GPL code (Stockfish or others) was read or
used for this job.

Caveat (from the card): Caissa runs null move only in cut nodes, so part of its +4.20 may come from a null-move change
further down the verification tree. Forge's null move has no cut-node condition. Inside Forge's verification frame,
`cut_node` drives the LMR `r += 2` term, the child flags of the full-depth re-searches and (rarely) IIR. Forge
estimate: 0 to +3 Elo at STC, **UNPROVEN** (no Forge gate has run).

## Licence notice (Caissa, MIT, verbatim at 1b7a871)

```
MIT License

Copyright (c) 2021 Michał Witanowski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
