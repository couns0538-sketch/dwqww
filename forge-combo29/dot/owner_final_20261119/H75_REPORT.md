# Owner-final H75 enabled-option evidence

Finite coverage, not an “all states tested” claim. Scope approved in owner-final plan3157180c420a167bb6960b8019576285bd3927df. Source frozen before counted runs; H75 patchSHA59df740bd9fb2f2889e0365ee6d791f2671d95f6471a9ec690677a36fba73f92.

## Six unchanged baseline gates
Fresh no-option/no-net processes: r15d and kF each bench11=312866, bench13=862329, perft5=4865609. Local gate_summary and six raw logs.

## Guard versus full recognition
H75 verifies the new no-pawn/rook/queen prefilter's Boolean against a64-square piece-array oracle. It does not independently reimplement all endgame scores. Existing H32 now exercises the enabled branch and compares old unguarded fullrecognition/score with guarded dispatch. The real enabled engine comparisons and separate direct-helper test add finite original-versus-current recognition evidence.

## Enabled real-engine suite
60 legal finite positions: all8 pawn/rook/queen presence combinations and7 minor patterns, mirrored strong side and both sides to move. Existing python-chess validates every position. Threads1,Hash16,PC20,synthetic v3hidden768 net checksum30ab43b4ba5db5f3,DeadMaterial=true,depth4,ucinewgame/reset per position. Exact inputs and scripts retained. No other strength/timing claim.
All four engines have60searches and16,287 last-completed-depth nodes. Bestmove and every last-info field exceptONLYtime/nps match r15d, includinghashfull/PV. No normal differences in42counters. Old39 differences remain0 in wrong build; only deliberate new references differ.

| Build | Binary SHA256 | Searches | Last-depth nodes |
|---|---|---:|---:|
| r15d | bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 | 60 | 16287 |
| kf | 340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea | 60 | 16287 |
| count | fbd034fd0b72ba6227f05fa6091a3bca67b8bd613df16784ae9286cae84972c1 | 60 | 16287 |
| wrong | 68c1e73cde1c836b7902a6b171fbbd7f9c3add8fc3ed84d2eda08ae7ec6feda5 | 60 | 16287 |

| Counter | Normal uses/differ | Wrong uses/differ |
|---|---:|---:|
| B1 | 10186/0 | 10186/0 |
| B2 | 10452/0 | 10452/0 |
| B5 | 10309/0 | 10309/0 |
| B6 | 15662/0 | 15662/0 |
| S-B1 | 10186/0 | 10186/0 |
| S-B2 | 10452/0 | 10452/0 |
| S-B4 | 10186/0 | 10186/0 |
| S-B7 | 15626/0 | 15626/0 |
| H28 | 1893/0 | 1893/0 |
| H18 | 10222/0 | 10222/0 |
| H25 | 17242/0 | 17242/0 |
| H27 | 5040/0 | 5040/0 |
| H82 | 26364/0 | 26364/0 |
| H30 | 1422/0 | 1422/0 |
| H3 | 13052/0 | 13052/0 |
| H71 | 3604/0 | 3604/0 |
| H12 | 6191/0 | 6191/0 |
| H36 | 12004/0 | 12004/0 |
| H11 | 4305/0 | 4305/0 |
| H29 | 3149/0 | 3149/0 |
| H86 | 16287/0 | 16287/0 |
| H37 | 1903/0 | 1903/0 |
| H32 | 5583/0 | 5583/0 |
| H35 | 4/0 | 4/0 |
| H52 | 48/0 | 48/0 |
| H33 | 15777/0 | 15777/0 |
| H42 | 12853/0 | 12853/0 |
| H47 | 3474/0 | 3474/0 |
| H2 | 0/0 | 0/0 |
| H20 | 5189/0 | 5189/0 |
| H39 | 3355/0 | 3355/0 |
| H84 | 119/0 | 119/0 |
| H17 | 0/0 | 0/0 |
| H24 | 3456/0 | 3456/0 |
| H38 | 14094/0 | 14094/0 |
| H40 | 8499/0 | 8499/0 |
| H41 | 8401/0 | 8401/0 |
| H45 | 7788/0 | 7788/0 |
| H46 | 7741/0 | 7741/0 |
| H47F | 4155/0 | 4155/2212 |
| H51 | 0/0 | 0/0 |
| H75 | 17349/0 | 17349/8781 |

## H75 real-search reach
Normal17,349uses/0differences; WRONG22 has17,349uses/8,781differences, exactlyWhite and a strict subset.
| Class | Uses |
|---|---:|
| white | 8781 |
| black | 8568 |
| allow | 6464 |
| block | 10885 |
| blockers0 | 6464 |
| blockers1 | 922 |
| blockers2 | 1269 |
| blockers3 | 1513 |
| blockers4 | 1892 |
| blockers5 | 1969 |
| blockers6 | 1657 |
| blockers7 | 1663 |
| blocked | 10885 |
| bare | 0 |
| single | 0 |
| two_knights_vs_bare | 771 |
| bishop_knight_vs_bare | 1878 |
| other | 3815 |

Overlapping class families must not be added together. All8blocker masks reached. Production bare/single classes are0:12insufficient-material roots exit before search, so these roots are NOT passing guard uses. Two-knight, bishop-knight and other candidate patterns are search-reached.

H32 enabled class totals (normal differences0):
```json
{
  "white": 2860,
  "black": 2723,
  "disabled": 0,
  "guard_rejected": 3385,
  "candidate_unrecognized": 1214,
  "recognized": 984,
  "dead_return": 984,
  "inactive": 0,
  "v1": 0,
  "v3": 4599
}
```

## Separate direct-helper micro-test
Scratch executable linked against each frozen build's existing objects except UCI main. Same60valid inputs, direct candidate guard once per position for kF/count/wrong, then fullrecognition only if accepted. Original r15d lacks this guard and calls its fullrecognizer directly. Compare recognitionBoolean and score, NOT the nonexistent r15d candidate field. Original guardcall count is0; new builds each60. All original/new recognitionBoolean and score outputs match (20recognized cases each). For unrecognized cases score retains sentinel1234567, also compared.
Normal diagnostic H75=60uses/0differences; White control=60uses/30differences. Independent Python squaremap predicate also matches allnew candidate Booleans. Unit-only bare4/single8/two-knights4/bishop-knight4/other12,blocked28, all8blocker patterns. These direct calls do not imply corresponding production search reach.

| Micro build | Binary SHA256 | Cases | Recognized | Guard calls |
|---|---|---:|---:|---:|
| r15d | 0216c071cca222a35eb5cf592f53a552741e55ef40047bf8ea77e3f95eb1581a | 60 | 20 | 0 |
| kf | 11bbabf4fdd33dc44583fe379c512cc642c0d5aefe93ca8d4a94149e0a776fff | 60 | 20 | 60 |
| count | 6e7a8308549046864e83903f780e4bda3c12f8560f8666b6147e76d57dc17136 | 60 | 20 | 60 |
| wrong | 6cc52ec60cc31e56d609b1654af2fd9517f2ceff0f899a80921fcecb7ed35c06 | 60 | 20 | 60 |

Micro sourceSHA47e0d9fab17d71b25f5027879cc1549d97e5779c9ba8e0682ba06c2400ce2491; build commands/flags/objectpaths/logs preserved individually.

## Raw manifest
```text
H75_engine_r15d.raw.txt sha256 905dea371317323ef58217a415080fd2e25f36af579b51b66efd9beb16cbeafb bytes 36827 lines 794
H75_engine_kf.raw.txt sha256 0317f69b081f68977d581c640ec43869c09c199eb7e8a0b987e098e0978f19c7 bytes 36822 lines 794
H75_engine_count.raw.txt sha256 18045c2222b345e0ca38ce00822d573e8fdc948e32579dc6de90f9a998827057 bytes 390386 lines 5774
H75_engine_wrong.raw.txt sha256 3b549ad430f04dffeee1f7016066e6a634edfd048752ff77862f9f86ae979ab2 bytes 390971 lines 5779
H75_micro_r15d.raw.txt sha256 6a793259cffaec9eb159ee694dec7ea8d764788bc5fe6ee937186bff6370a169 bytes 2738 lines 61
H75_micro_kf.raw.txt sha256 7c6931736efad03aec78f7bb0f7d0ffa11564f4b8d380611a93536a1a5865780 bytes 2738 lines 61
H75_micro_count.raw.txt sha256 2f8d1393afe5d839980ba6a809d3e1f1d262c65ed00f6ff4a8bf8f5468acecf0 bytes 8299 lines 144
H75_micro_wrong.raw.txt sha256 477c787b24a52a6233db0a76f0e9013d9d1e72e9c1b8a10cd2534c18f76f8feb bytes 8749 lines 149
```

## Independent QA
UTC 2026-11-19T01:41:06.326070+00:00
PASS: independent raw parse all4engine transcripts60searches each and exact60valid inputpositions, fullcanonical includinghashfull/PV excepttime/nps, bestmoves/nodes16287; all42aggregatecounts and H75/H32/H47Fclasssums, old39diff0, wrongH75exactWhite. Production12insufficientroots zero H75; no fabricated bare/single reach. Separate all4micro transcripts60unitsrecognitionbool/score equivalent originalfullrecognizer, guard vs Python squaremap predicate, 60/0 normal and60/30 control. Eight wholetranscript hashes/bytes/lines manifest. No new native experiment during QA.

## Limits
Finite legal endgames, this compiler/net/CPU, one thread and these settings only. Shared Board representation and original recognition implementation can hide common errors. No exhaustive promotion/castling/en-passant/tree or all-fiftymove/repetition proof. Production insufficient roots remain deliberately early returns. No engine source repository changes or binary/net publication. No new native experiment during independent QA. H75 can be marked PARTIAL_DIRECT with both production-enabled and explicitly separate unit evidence, no longer universally NONE or “all tested.”
