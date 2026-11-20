#!/usr/bin/env python3
"""Write REPORT.md from the evidence files already in this folder."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = Path("/agent/repos/dwqww")


def text(name: str) -> str:
    return (ROOT / name).read_text().rstrip("\n")


def main() -> None:
    stamp = subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True).strip()
    stamps = (ROOT / "stamps.txt").read_text()
    if "STEP 5 report" not in stamps:
        with (ROOT / "stamps.txt").open("a") as handle:
            handle.write(f"{stamp} STEP 5 report\n")
    (ROOT / "RESULT.txt").write_text(
        "seat=007 idea=7 id=S31 option=NullThreatVerify "
        "exists=yes:forge-combo29/src/search.cpp:1724 applies=yes off_identical=yes "
        "on_differs=147 of 200 sanitizer=clean elo=-0.31 err=8.77 games=1106 "
        "partner=057 partner_verdict=CONFIRMS\n"
    )
    sums = text("B_SUMS.txt").splitlines()
    elo_line = next(line for line in text("match_og_result.txt").splitlines() if line.startswith("Elo:"))
    games_line = next(line for line in text("match_og_result.txt").splitlines() if line.startswith("Games:"))
    body = f"""# Seat 007, idea 7, S31

S31 accepts a null-move cutoff at once when no cheaper enemy piece attacks a dearer piece of the side to move, and re-searches the cutoff, with null moves disabled, when such an attack exists.
The plain engine already does that below depth 14 when NullThreatVerify is on, and it always verifies a null cutoff at depth 14 or more.
I left that switch as it is and turned the fixed split at 14 into the spin NullThreatVerify_Depth, default 14, minimum 1, maximum 64, so a default search takes today's path.

## EXISTS

yes: forge-combo29/src/search.cpp:1724
The option is already advertised. forge-combo29/src/search.cpp:101 sets NullThreatVerify false, and forge-combo29/src/uci.cpp lists `option name NullThreatVerify type check default false`. The depth 14 in the threat gate was a literal, so it is now NullThreatVerify_Depth.

## Honesty

No setoption. Exe B, then exe P.

```
{text("HONESTY_B.txt")}
```

```
{text("HONESTY_P.txt")}
```

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 007, idea 7 |
| 2 honesty B | done | HONESTY_B.txt | four known node counts |
| 2 O and G sums | done | B_SUMS.txt | {sums[0]} / {sums[1]} |
| 3 prediction, before measuring P | done | prediction.txt | committed before any exe P measurement |
| 3 patch applies | done | apply_check.txt | {text("apply_check.txt").replace(chr(10), " ")} |
| 3 proof off | done | compare_off_O.txt, compare_off_G.txt | {text("compare_off_O.txt")} / {text("compare_off_G.txt")} |
| 3 proof on | done | compare_on_O.txt, on_O_delta.txt | {text("compare_on_O.txt")} / {text("on_O_delta.txt")} |
| 3 uci options | done | uci_options.txt | {text("uci_options.txt").replace(chr(10), " / ")} |
| 3 sanitizer | done | asan_summary.txt | {text("asan_summary.txt").splitlines()[0]}; raw hits {text("asan_summary.txt").splitlines()[1]} |
| 3 match | done | match_og_result.txt | {elo_line} / {games_line} |
| 4 partner 057 | done | partner_compare_on_O.txt, partner_match_result.txt | CONFIRMS, R match 600 games |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) Honesty, no setoption, exe P: the four lines in HONESTY_P.txt match exe B and the known counts. bench 11 is 312866, bench 13 is 862329, bench 16 is 3024920, perft 5 is 4865609.

(2) S14, NullThreatVerify false, NullThreatVerify_Depth 14.

```
{text("compare_off_O.txt")}
{text("compare_off_G.txt")}
```

```
{text("proof_sums.txt")}
```

(3) S14, NullThreatVerify true, NullThreatVerify_Depth 14. O depth 12.

```
{text("compare_on_O.txt")}
{text("on_O_delta.txt")}
```

The O sum is 9501877. The prediction file said 10260000 and said a sum below 9700000 would show that guess wrong. 9501877 is below 9700000. prediction.txt was not edited.

(4) `uci` from exe P.

```
{text("uci_options.txt")}
```

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. First 100 positions of G, depth 10, switch true. The scratch engine is that same build plus one heap read past the end of a four-int array, on one FEN, run through harness_search.py.

```
{text("asan_summary.txt")}
```

```
{text("apply_check.txt")}
```

## Match

Exe P with NullThreatVerify true against exe P with it false. Both S14, Threads 1, Hash 16, NullThreatVerify_Depth 14, 20000 nodes, openings O then G (553), both colours, 1106 games. fastchess concurrency 3. Rounds equal the number of openings.

```
{text("match_og_result.txt")}
```

The Elo interval includes 0 and the point is above -20, so the brief's one look for a bug was not triggered. The predicted Elo was +6, wrong if below -20 or above +30. -0.31 is inside that range.

## Partner

Partner is seat 057 (idea 7; 107 had no branch). git apply --check of partner.patch.txt on the base commit exited 0. A fresh worktree was built with g++. My harness, not seat 057's scripts.

```
{text("partner_HONESTY.txt")}
{text("partner_compare_off_O.txt")}
{text("partner_compare_on_O.txt")}
{text("partner_on_vs_B.txt")}
```

Off matches exe B's O rows (0 differ, sum 9500069). On matches seat 057's own O rows (0 differ, both sums 9536516) and differs from exe B on all 200, which is what seat 057 reported. Verdict: CONFIRMS.

Their switch, on my 300 R openings, both colours, 600 games:

```
{text("partner_match_result.txt")}
```

## suspicions, not proven

At depth 12, on_O_delta.txt shows the node count changed on 147 openings, the root move changed on none, every change was an increase, and the net added 1808 nodes. The 1106-game match does not separate the option from zero. That is not a proof that the option is neutral in a longer game or with the owner's net.

## what I did NOT do

I did not re-run seat 057's G depth-12 set, and I did not replay their 1106-game match. I did not search with NullThreatVerify_Depth set to anything but 14. I did not add the comfortable-margin test in the S31 text. Seat 057 built that as IdeaS31 with IdeaS31_Margin 80. I did not open a pull request.

## what I am NOT sure about

S31's text says to do the threat gate at every depth and to accept a quiet cutoff only when the static margin is comfortable. The engine's NullThreatVerify gate applies only below 14, and the always-verify at 14 and above was already there. I called that EXISTS and parameterized 14. Seat 057 called it a different idea and replaced the gate. I am not sure which reading Opus wants. The node-sum prediction was outside the range written in prediction.txt. The partner review was stamped at 2026-11-20T08:57:47Z. Minute 75 after the first stamp is 2026-11-20T09:06:46Z. The patch was already on their branch, and step 3 of this seat was already pushed.

## times: see stamps.txt

```
{text("stamps.txt")}
```
"""
    (ROOT / "REPORT.md").write_text(body)
    status = subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True)
    listing = subprocess.check_output(["ls", "-la", str(ROOT)], cwd=REPO, text=True)
    with (ROOT / "REPORT.md").open("a") as handle:
        handle.write("\n## git status --short\n\n```\n")
        handle.write(status)
        handle.write("```\n\n## ls -la\n\n```\n")
        handle.write(listing)
        handle.write("```\n")
    print(f"wrote {ROOT / 'REPORT.md'} and RESULT.txt at {stamp}")


if __name__ == "__main__":
    main()
