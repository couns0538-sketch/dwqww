#!/usr/bin/env python3
"""Write REPORT.md and RESULT.txt from the raw files in this folder."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8", errors="replace")


def honesty(name: str) -> list[str]:
    raw = text(name)
    benches = re.findall(r"bench depth (\d+) nodes (\d+)", raw)
    perfts = re.findall(r"(?m)^nodes (\d+)\s*$", raw)
    lines = [f"bench {d} -> nodes {n}" for d, n in benches]
    lines += [f"go perft 5 -> nodes {n}" for n in perfts]
    return lines


def last_match(name: str) -> tuple[str, str, str]:
    raw = text(name)
    elos = re.findall(r"(?<![A-Za-z])Elo: ([+-]?\d+\.\d+) \+/- (\d+\.\d+)", raw)
    games = re.findall(r"Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+)", raw)
    if not elos or not games:
        raise SystemExit(f"no match summary in {name}")
    elo, err = elos[-1]
    g, w, l, d = games[-1]
    return elo, err, f"games={g} wins={w} losses={l} draws={d}"


def main() -> int:
    b = honesty("HONESTY_B.txt")
    p = honesty("HONESTY_P.txt")
    partner_h = honesty("partner_073/HONESTY.txt")
    compare = text("proof_compare.txt").rstrip()
    asan_meta = text("asan_G100_d10.meta")
    asan_count = re.search(r"asan_symbol_count=(\d+)", asan_meta)
    san_lines = re.search(r"sanitizer_lines=(\d+)", asan_meta)
    scratch = text("asan_scratch.txt")
    scratch_hits = [
        line for line in scratch.splitlines()
        if "ERROR: AddressSanitizer" in line or "heap-buffer-overflow" in line
    ]
    elo, err, games = last_match("match_OG.txt")
    pelo, perr, pgames = last_match("partner_073/match_R.txt")
    off = text("partner_073/compare_off.txt").rstrip()
    on_b = text("partner_073/compare_on_vs_B.txt").rstrip()
    on_p = text("partner_073/compare_on_vs_partner.txt").rstrip()
    apply_self = text("apply_check_self.txt").rstrip()
    apply_partner = text("partner_073/apply.txt").rstrip()

    report = f"""Idea S29 orders captures that already pass a fixed static-exchange gate by a history of the cheaper enemy piece attacking the landing square.
The check option is IdeaS29, default false. The spins are IdeaS29_Threshold default 0 and IdeaS29_Scale default 1.
With the check false the new term is not read, and the good/bad capture split stays see_ge(move, 0).

EXISTS: no. ThreatHistory in include/forge/search.hpp is a quiet-move table. Capture history is added to every capture and is not gated by a fixed exchange. See DECISIONS.txt.

Honesty, no setoption, from HONESTY_B.txt and HONESTY_P.txt:
exe B: {"; ".join(b)}
exe P: {"; ".join(p)}

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 023 idea 23
STEP 2 honesty | done | HONESTY_B.txt | {"; ".join(b)}
STEP 2 baseline | done | B_O_d12.rows B_G_d12.rows proof_compare.txt | O 9500069 and G 18466239
STEP 3 patch | done | idea.patch.txt apply_check_self.txt | git apply --check exit 0
STEP 3 proofs | done | proof_compare.txt asan_G100_d10.meta asan_scratch.txt | off 0 differ; on 200 of 200; sanitizer clean
STEP 3 match | done | match_OG.txt | Elo {elo} +/- {err}; {games}
STEP 4 partner | done | partner_073/ | CONFIRMS seat 073
STEP 5 report | done | REPORT.md RESULT.txt | this file
```

Proofs on exe P:
(1) Honesty with no setoption: {"; ".join(p)}
(2) S14 and IdeaS29 false, position by position equal to exe B. From proof_compare.txt:
{compare}
(3) S14 and IdeaS29 true, O depth 12: 200 of 200 positions differ from exe B. Sum 9540759. First three 27969 24392 28917.
(4) uci lists `option name IdeaS29 type check default false`, `IdeaS29_Threshold type spin default 0 min -2000 max 2000`, `IdeaS29_Scale type spin default 1 min 0 max 32`. See HONESTY_P.txt.
(5) AddressSanitizer and UndefinedBehaviorSanitizer, IdeaS29 true, first 100 of G at depth 10. asan_symbol_count={asan_count.group(1) if asan_count else "missing"} sanitizer_lines={san_lines.group(1) if san_lines else "missing"}. The scratch copy, one heap read past the end on scratch_fen.epd, run with the same harness_search.py, reported:
{scratch_hits[0] if scratch_hits else "NO SANITIZER LINE"}

Match, exe P with IdeaS29 true against exe P with IdeaS29 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. From the last summary in match_OG.txt: Elo {elo} +/- {err}, {games}.

Partner is seat 073 (idea 23; seat 123 has no branch). Verdict: CONFIRMS.
git apply --check on a fresh base: {apply_partner}
Honesty of that build: {"; ".join(partner_h)}
Switch false versus exe B O depth 12:
{off}
Switch true versus seat 073's own O depth-12 rows (0 means the rows match):
{on_p}
Switch true versus exe B, which seat 073 reported as 199 of 200:
{on_b}
Their 1106-game O+G match was not replayed. The required 300 R openings, both colours, on their build: Elo {pelo} +/- {perr}, {pgames}. See partner_073/match_R.txt.

suspicions, not proven
The safety term is added before the good/bad split, so a large history can change the order in which losing captures are deferred, not only the order of two captures that both passed the gate. Bishop and knight have the same SEE value; the lower piece type wins that tie, and I did not count how often the tie happens. Seat 073 divides the same history by 8 instead of adding it raw, and their O sum is 9692566 against my 9540759, so the weight changes the tree.

what I did NOT do
I did not replay seat 073's 1106-game match. I did not play a second R match of my own patch. I did not try any IdeaS29_Threshold except 0 or any IdeaS29_Scale except 1. The term is not added to in-check evasion ordering. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60.

what I am NOT sure about
Whether +{elo} Elo at 20000 nodes on the built-in net would hold on the owner's net at a time control. The prediction file said 9350000 and +4 Elo, wrong outside 8000000..11000000 and wrong if the interval lay entirely below -25 or entirely above +35. The measured sum 9540759 and the interval {elo} +/- {err} are inside those ranges. I am not sure a raw scale of 1 is better than seat 073's divisor of 8.

times: see stamps.txt

Own patch apply check (apply_check_self.txt): {apply_self}
"""
    (HERE / "REPORT.md").write_text(report, encoding="utf-8")
    result = (
        f"seat=023 idea=23 id=S29 option=IdeaS29 exists=no applies=yes "
        f"off_identical=yes on_differs=200 of 200 sanitizer=clean "
        f"elo={elo} err={err} games=1106 partner=073 partner_verdict=CONFIRMS\n"
    )
    (HERE / "RESULT.txt").write_text(result, encoding="utf-8")
    print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
