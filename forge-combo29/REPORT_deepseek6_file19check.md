# REPORT — deepseek6, file 19 check (does long 55's "accepted and python-chess INVALID" class still stand?)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_file19check/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

File 19 adds no item; it corrects file 15's castling claim and asks: **"If long 55's table has a class 'accepted and
python-chess INVALID' that holds a castling FEN: check that row again with the rule above and say in your next
report whether it stands."** This is that check. No claim was needed: it is a re-reading of committed data plus one
live re-run, not a new item.

## 1. Three lines

**Asked:** re-check long 55's `accepted_invalid` class with file 19's rule (read every line after `position` up to
`readyok`, stop on `invalid FEN` / `illegal move`, and be suspicious of a count equal to a well-known one).

**Answer:** **the class stands, and it does not contain a castling FEN.** All **47** rows of
`tests_deepseek6_long55/out/special_invalid_accepted.txt` are **`replace` mutations that put a two-digit run inside a
rank** ("17", "21B4", "114K1", "R11QR1K1", …). python-chess cannot even *parse* them
(`two subsequent digits in position part of fen`), while the engine accepts them and searches. **Not one of the 47
is an impossible-castling FEN**, so file 15's wrong castling example never touched this class; the rows are a
corrected finding about a different defect (rank-digit overflow), and they survive.

**How sure:** certain — the 47 rows are re-listed, their mutation type is counted (47/47 `replace`), and I re-ran
two of them live against the engine and python-chess.

## 2. The evidence

```
$ git show <branch>:forge-combo29/tests_deepseek6_long55/out/special_invalid_accepted.txt | wc -l
47
$ cut -d'|' -f2 <the same file> | sort | uniq -c
     47 replace
$ grep -cE ' [KQkq]+ ' <the same file>
3        <-- three rows mention castling rights, but their overflow is a DIGIT ("21B4", "2N211P", "R11QR1K1"),
              not a missing king or rook; the castling field itself is legal
```

**A live re-run of one row** (`8/3r3k/R1R5/6pP/4KpP1/17/4r3/8 w - - 0 1`):

```
$ printf 'uci\nisready\nposition fen 8/3r3k/R1R5/6pP/4KpP1/17/4r3/8 w - - 0 1\nisready\ngo depth 2\nquit\n' | forge
uciok
readyok
readyok
bestmove e4f3          <-- no "invalid FEN" line: ACCEPTED
$ python3 -c "...chess.Board('8/3r3k/R1R5/6pP/4KpP1/17/4r3/8 w - - 0 1')"
python-chess REFUSES to parse: two subsequent digits in position part of fen
```

**A live re-run of a row that carries castling rights** (`r1bqkb1r/pppp1ppp/2n2n2/5N2/3P4/21B4/PP3PPP/RNBQ1RK1 b kq - 0 1`):

```
readyok
readyok         <-- accepted (no invalid FEN line)
a7a6: 43
...             <-- go perft 2 generates moves: the engine is searching a board python-chess rejects
```

## 3. What this means for file 19's advice

File 19's two rules are right and I have applied them since long 33:

1. **"Every harness reads all lines after `position` up to `readyok` and stops on `invalid FEN` / `illegal move`."**
   My long 34, long 43, long 51, long 53 and long 58 harnesses all do this (`rows.py` sends `isready` after
   `position` and its refusal regex includes `invalid FEN`). Long 33's `perft_cmp.py` did not, which is exactly the
   bug file 19 identified.
2. **"A count equal to a well-known count means: look whether the input was refused."** This is the sharper rule
   and it is what would have caught long 33 immediately: 8,902 is startpos perft 3.

**One correction to file 19's own wording, offered rather than asserted:** it says "every harness" should stop on a
refusal. For long 55's **fuzz** the right behaviour was the opposite — the fuzz *counts* refusals as a result
class, and stopping would have hidden the 47 accepted-invalid rows. The distinction is whether the input is
**known-good** (stop, a refusal means the harness is wrong) or **deliberately bad** (classify it, never stop). Long
55 does the latter and its `classes.txt` is the audit trail.

## 4. What I did NOT do

- Did not re-run long 55's full 20,000-FEN fuzz: the question is about one class, and the class is a committed
  list of 47 rows.
- Did not change long 55's report or its output files: they stand as committed.
- No engine change, no branch change beyond this folder, no pull request.

## 5. The model

Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.
Times: the re-runs above were made in this chat; `git log` shows this folder's commit time.
