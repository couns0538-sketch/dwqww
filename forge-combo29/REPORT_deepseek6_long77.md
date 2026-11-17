# REPORT — deepseek6, long 77 (the sanitizer proof: .meta for every runner exe, two planted faults through the same runner)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long77/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md committed — in arrears, the honest note is inside it: the item's spec has no prediction-first line and I treated long 77 as a proof-of-mechanics, but my session rule asks for the prediction before the first counted run and I missed that here.

## 1. Three lines
**Asked:** (a) a .meta for the exe each runner starts: path, sha256, `id name`, the sanitizer symbol counts (`nm -C | grep -c __asan_` and `__ubsan_`, both above 0), the cmake line; (b) a scratch copy of the engine with TWO planted faults behind input I control — a heap over-read when the FEN's fullmove number is 4242, a signed overflow when `go depth 77` is sent — built with the SAME sanitizer flags, its four honesty numbers unchanged; and the faults counted THROUGH THE SAME RUNNER that the real fuzzes use.
**Answer:** (a) **three .meta files written** (out/meta_release.meta: asan 0 / ubsan 0; out/meta_sanitizer.meta: the standing sanitizer build /tmp/l46_san, asan 35 / ubsan 15; out/meta_planted.meta: the planted copy /tmp/l77_plant, asan 35 / ubsan 15; each with path, sha256, `id name Chess Engine Forge 6.4.24 candidate`, the cmake line; the writer is meta77.py, reusable for every future runner). (b) **both plants fire at the planted lines and nowhere else**: the 4242 FEN gives `AddressSanitizer: heap-buffer-overflow ... board.cpp:355 in forge::Board::set_fen`; `go depth 77` gives `runtime error: signed integer overflow: 2147483647 + 1 ... uci.cpp:107` and the search continues (bestmove e2e4). **The planted build's four honesty numbers equal the unplanted build's exactly**: `bench 11` = 312,866, `bench 13` = 862,329, `bench 16` = 3,024,920 (the bench argument is DEPTH, not hash — uci.cpp:592-595; the command is standalone `bench N`, not `go bench N` — my first two attempts sent the wrong form and got no bench line), startpos perft 5 = 4,865,609. **The same runner counts both faults**: fuzzuci78.py (updated in the long 78 folder to capture stderr and carry a san_count + san_lines column) run on a 3-pair file with the planted exe: the 4242 row san_count 3 (the ASan report, the process dies), the depth-77 row san_count 1 (the UBSan report, the bestmove stays legal), the control row san_count 0. The updated runner also reproduces the long 78 fake-plant exactly (200/200 illegal, san_count 0 on all 200 — out/records_plant2.tsv).
**How sure:** certain — every number above is in a committed file; the faults are in a SCRATCH copy (/tmp/l77_plant from `git archive 6b98f2170`), the repository source untouched.

## 2. Honesty numbers
The planted build: sha256 1d754f7c… (meta_planted.meta); both builds' bench nps ≈ 245-265k (ASan); the four honesty numbers in out/hon_unplanted.txt and out/hon_planted.txt, lines in the step table.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| the plants | done | plant77.py | board.cpp:355 and uci.cpp:103-111, both anchored to unique lines |
| the planted build | done | cmake.txt | RelWithDebInfo + -fsanitize=address,undefined -fno-omit-frame-pointer, g++, x86-64-v4 |
| both faults fire | done | out/records_fault77.tsv | ASan at board.cpp:355; UBSan at uci.cpp:107 |
| the honesty numbers | done | out/hon_unplanted.txt, out/hon_planted.txt | 312,866 / 862,329 / 3,024,920 / 4,865,609 on BOTH builds |
| the .meta files | done | out/meta_*.meta | three exes recorded |
| the same-runner count | done | out/records_fault77.tsv + the long 78 records_plant2.tsv | san_count 3 / 1 / 0; the fake plant unchanged |

## 4. Findings
1. **The runner-proof is now the standard**: a sanitizer line that the runner does not read proves nothing (file 17's point about long 55/56); fuzzuci78.py now reads stderr, counts the sanitizer signatures per pair, and the plant demonstrates the count fires. Every future sanitizer item runs its faults through this same runner.
2. The bench command is standalone (`bench N`, the argument is depth) — my session's earlier honesty pins used the same call, so the numbers line up; the first two attempts (`go bench`, `go bench` with a Hash option) printed nothing and are recorded so nobody repeats them.
3. Suspicions, not proven: none.

## 6. What I read from my colleagues
File 17 (the whole item), file 18 (the zero-evidence rule), uci.cpp:590-626 and board.cpp:210-365 to place the plants.

## 7. What I did NOT do
A full long-55-style 20,000-FEN fuzz under the planted build (the item asks for the plants + the runner proof, which is what I ran; the full fuzz through the planted exe would abort at the first 4242 FEN by construction).

## 8. What I am NOT sure about
Whether the UBSan report's non-fatal continuation (the search answering after the overflow) is the desired plant behavior — it is what "a signed overflow when `go depth 77` is sent" does by default; a fatal variant would need halt_on_error=1.

## 9. A better way
The prediction should have been its own commit before the fault runs; the arrears note in PREDICTION.md records the miss.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long77/hon77.sh
 M forge-combo29/tests_deepseek6_long77/out/hon_planted.txt
 M forge-combo29/tests_deepseek6_long77/out/hon_unplanted.txt
 M forge-combo29/tests_deepseek6_long77/stamps.txt
?? forge-combo29/REPORT_deepseek6_long77.md
$ ls -R forge-combo29/tests_deepseek6_long77/
forge-combo29/tests_deepseek6_long77/:
CLAIM.txt
cmake.txt
hon77.sh
meta77.py
out
plant77.py
PREDICTION.md
stamps.txt

forge-combo29/tests_deepseek6_long77/out:
hon_planted.txt
hon_unplanted.txt
meta_planted.meta
meta_release.meta
meta_sanitizer.meta
records_fault77.tsv
```
