# PREDICTIONS — seat 10, audit of every "Known:" claim in the brief that asserts engine behaviour

Written and committed ALONE before the first measuring command of this audit.
Commit 6b98f217. Release build `~/builds/release/forge`, sha256
`e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, 4 cores, g++ 13.3.0.
Position sets from `for-fable-and-opus/kimi5-work`: O = `tests_kimi5_job3/first200.fens` (200),
G = `tests_kimi5_job5/set_G.epd` (353).

Each claim gets PASS / REFUTED / UNTESTABLE with its kill condition stated up front.

## K1 — Area 1 job 3 / FABLE-1: "an illegal move keeps the legal prefix (perft 1 = 29 after e2e4 e7e5 e1e3)"
PASS. Sending `position startpos moves e2e4 e7e5 e1e3` then `go perft 1` returns 29, and 29 is
python-chess's own legal-move count after `e2e4 e7e5` (I will compute it, not assume it).
Kill: any total other than python-chess's count after the legal prefix, or a refusal.

## K2 — Area 2 job 3 / FABLE-1: "`setoption name Hash value 0` answers `info string invalid value for option Hash`"
PASS on the message, with one correction of scope predicted: I expect the SAME message shape for
every out-of-range spin and for a VALUELESS option, so the line is not special to Hash 0. I predict the
exact text is `info string invalid value for option Hash` (no trailing detail, no "value 0" echoed).
Kill: no such line, or a different message, or the engine silently accepts Hash 0.

## K3 — Area 3 job 3: "startpos perft 5 = 4,865,609"
PASS. Already measured twice in my honesty run. Re-measured here in a fresh process for the record.
Kill: any other total.

## K4 — Area 3 job 3: "G perft 3 and the first 60 at perft 4 were equal in an earlier check"
PASS **only if "equal" means equal to python-chess**, and I predict this wording is the weak point:
it does not say equal TO WHAT. I predict G perft 3 matches python-chess on all 353 positions and the
first 60 match at perft 4, i.e. the substantive claim holds. I will state plainly that "equal" in the
brief is undefined and that I am testing it against python-chess 1.11.2.
Kill: any single position where the totals differ.

## K5 — Area 4: "Threads 2 and 4 on the first 50 of O gave 0 reports"
UNTESTABLE AS WRITTEN, predicted. "0 reports" is only a result under the brief's two-proof rule
(nm count above 0 AND a planted race counted by the same runner), and the brief cites no such artifact.
I will build TSan if the budget allows and then either convert this to PASS with both proofs or report
it as "not shown". Kill: a committed nm count + planted-race artifact already exists for that claim.

## K6 — the honesty pins: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609
PARTLY REFUTED as stated; PASS only under an unstated condition. I predict:
 (a) all four hold with DEFAULT options, confirming my honesty run;
 (b) they do NOT hold if the S14 setoptions are applied first (I measured bench 11 = 242,796 that way),
     so the brief's "use S14 unless a job says otherwise" and "the honesty check" collide;
 (c) they hold on a second, independent build of the same source (bit-identical node counts).
Kill: (a) fails, or (b) S14 gives the same numbers, or (c) two builds differ.

## K7 — STEP 2: "on a machine without AVX-512 or BMI2 add -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3"
PREDICTED PASS on the numbers: a portable x86-64-v3 build gives the SAME four pin values, i.e. the
ISA switches change speed but not the tree. This matters because most seats must build portably and
would otherwise read a differing pin as a broken checkout.
Kill: any pin differs from the pin on the v4 build.

## K8 — FABLE-1: "consecutive digits of a rank are ADDED ('17' and '44' read as 8 empty squares; '9' is refused)"
PASS. A rank written `44` where `8` belongs gives the identical board (same perft 3), `17` likewise,
and `9` is refused.
Kill: different perft, or `9` accepted.

## K9 — FABLE-1 / Area 1: "a position no game can reach is accepted (a triple check by three knights); its moves are generated right"
PASS on acceptance. I predict the engine accepts a king attacked by three knights and its perft 1
equals python-chess's legal-move count on the same (status-flagged) board. I will list the exact
attackers with my own scan, as in my earlier checks.
Kill: refused, or perft differs from python-chess.

## K10 — FABLE-1: "an unknown command is ignored without a line"
PASS for a plain garbage line, but I predict a REFUTED sub-case that matters: a garbage line that
happens to start with a KNOWN command word (e.g. `position`, `setoption`, `go banana`) does NOT stay
silent — I predict `go banana` and `setoption name` produce an `info string` line, so "unknown command
is ignored without a line" is true only for lines whose first token is unknown.
Kill: every garbage variant is silent, or the plain garbage line speaks.

## K11 — FABLE-1: "an option without a value answers info string invalid value for option X"
PASS, same message shape as K2. Kill: silence, or a different message.

## K12 — FABLE-1: "`bestmove 0000` on a position without legal moves (checkmate, stalemate)"
PASS for both a checkmated and a stalemated root, on `go depth 5`. Kill: any other bestmove, or a hang.

## K13 — the four big sums: O d12 = 9,500,069 (first three 41,311 / 24,872 / 28,574), G d12 = 18,466,239, O d14 = 21,812,100, G d14 = 43,345,893
PASS, measured with the stated protocol (plain build, S14, `ucinewgame`+`isready` before every `go`,
Threads 1, Hash 16), summing the final node count of each search. I predict the four totals match
EXACTLY, and that the three per-position numbers for O also match exactly. This is the highest-risk
claim in the brief if "plain build" is read as "default options", so I will report both readings.
Kill: any mismatch, and I will then name which of the two option regimes reproduces the numbers.

## K14 — FABLE-1: "a root restricted by searchmoves (even to every legal move) searches a different, mostly smaller tree: IIR fires at the root, and no hash entry is stored for a restricted root"
PASS on "different and smaller". I predict the node count with `searchmoves` listing all 20 legal moves
is strictly LESS than the unrestricted count on the same depth, and that repeating the restricted search
a second time in the same process shows no node reduction from a stored root entry (consistent with
"no hash entry stored"), while repeating the unrestricted search DOES show a reduction.
Kill: restricted count equals or exceeds the unrestricted count, or the restricted repeat shrinks.

## Method note
Every table in the report will be the pasted output of a committed script reading committed raw files.
All engine I/O goes through committed harness scripts; every refusal/`invalid` line is checked and
reported, not filtered.
