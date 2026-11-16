# `score mate 0` on a checkmated root — closed as documentation, not a defect

**Seat 01, area 1, 2026-11-16. This withdraws my own S-F32 and S-F38.**

## The question
I reported, following seat 21, that a checkmated root answers `info depth N … score mate 0 … pv` and
`bestmove 0000`, and called it an open door. Seat 21 later withdrew the same claim (its 21-F11). Two seats
were left disagreeing, so the coordinator asked me to settle it by asking **what consumes the output**.

## 1. The output is the correct UCI encoding — measured, not argued
One harness, four boards, fresh process each, on PC r15 (PC20, Threads 1, Hash 16) and on base:

| board | python-chess says | engine score | engine bestmove |
|---|---|---|---|
| already checkmated (`4R1k1/5ppp/8/8/8/8/5PPP/6K1 b`) | checkmate, 0 legal moves | `mate 0` | `0000` |
| can mate in 1 (`6k1/5ppp/8/8/8/8/5PPP/R5K1 w`) | 20 legal moves | `mate 1` | `a1a8` |
| stalemated (`7k/5Q2/8/8/8/8/8/K7 b`) | stalemate, 0 legal moves | `cp 0` | `0000` |
| losing (`6k1/5ppp/8/8/8/8/5PPP/1R4K1 b`) | 8 legal moves | `cp -984` | `h7h5` |

Four answers, one consistent scale: `mate <y>` is "mate in y moves for the side to move", so a side that is
mated **now** is `mate 0`, and with no legal move the only `bestmove` is `0000`.

The formatter confirms the encoding rather than the code merely happening to agree
(`src/search.cpp:353`):

```cpp
std::string format_score(int score) {
    if (is_mate_score(score)) {
        const int distance = MateValue - std::abs(score);
        const int mate = (distance + 1) / 2;
        return "mate " + std::to_string(score > 0 ? mate : -mate);
    }
    return "cp " + std::to_string(score);
}
```

`mate 0` is printed exactly when `distance == 0`, i.e. the side to move is at `-MateValue`: mated already.

## 2. Nothing in the repository consumes it — checked, not assumed
- The repository has only two tooling files that could read engine output: `verify.py` (parses training-curve
  `scores` arrays, never UCI text) and `replay-work.js` (asserts move-ordering buffers, never UCI text).
- `grep -rn "score mate\|Mate(0)\|mate_score == 0"` over the engine source, `scripts/`, `windows/`,
  `windows_build/` finds **no parser**.
- The helper branches that actually run games (`deepseek6-work`, `glmflash5-work-cb5c`) contain no `.py`
  file matching `score mate` or `score cp`.

So no engine code, script, training tool or helper game-runner reads that number, and nothing can misread it
as a loss.

## 3. Verdict
**The output is correct per the UCI encoding and harmless per the repository. It is documentation, not a
defect, and I withdraw S-F32 and S-F38.** The finding would have been a real one only if a consumer had
misread it; this note records that none does, with the searches that show it.

The one thing worth keeping from the original report: a *mated* root and a *stalemated* root both answer
`bestmove 0000`, so anything that wants to tell them apart must look at the score (`mate 0` vs `cp 0`), not
at the bestmove.
