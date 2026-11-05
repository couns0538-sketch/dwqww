# Fixes for the independent tool review (REVIEW_TOOLS_INDEPENDENT.md, worker toolrev, 2026-11-05)

The review found no BLOCKER. Each finding and what was done (12:0x-12:1x PC clock; tools re-parsed with PS 5.1):

| finding | action |
|---|---|
| SHOULD 1 reuse source check one-directional | speed_pack: the reused `src_copy` include\ + src\ must not hold a file the pack's source lacks (both directions now) |
| SHOULD 2 patch md5 cited by name only | speed_pack: re-diffs `lock` against the pack source (Git's diff.exe, from F:\ospd\src) and compares the hunks with the patch file (header lines ignored); the candidate file says "verified" or "WARNING: DOES NOT MATCH" |
| SHOULD 3 ASan N/A hidden in the verdict text | speed_pack: the State line now reads "BIT-EXACT with L4 = UBSan only (ASan N/A ...)" and names the quick L3 subset; (c) "is the ON path under a GCC-only guard" is NOT automated - listed as a limit in FINAL_REPORT |
| SHOULD 4 two verdicts of equal standing | abba.ps1 VERDICT line names wall as the PROTOCOL verdict and cpu as advisory (line format kept for the parsers); abba_table.py sorts by the wall median; FINAL_REPORT cites protocol (wall) verdicts and lists cpu-only wins as advisory; TT no-TLS re-timed with 16 rounds; a stack of the protocol winners only (stack_w1 = NZM2 + SPEED2) was built and timed |
| LOW 1 empty = empty passes | Verdict-Line requires both values non-empty |
| LOW 2 shared reference uci logs | logs named per TSV leaf / signature + PID |
| LOW 3 MSVC reference cache key | key includes the cl.exe version line, the flag set and -SanNdebug |
| LOW 4 resume ignores FEN file / depth | the reused L3 line must carry the same FEN md5 prefix and `go depth` |
| LOW 5 -AaCsv checked late | checked before the first run |
| LOW 6 cpu metric wording | comment and VERDICT text: preemption only, SMT sibling and 15.625 ms ticks remain |
| LOW 7 queue left on CPU 2 | abba_queue re-pins itself to 0x3 Idle after every run |
| LOW 8 bare-bestmove rows | documented as fail-closed by design (none in the 12k set) |
| LOW 9 make_stack regex / diff exit / overwrite | CR stripped before counting, diff exit code checked, an existing patch file is refused (tested: one-patch stack OK, second run refused) |
| LOW 10 commit gate missed staged files | commit_push lints modified + untracked + staged code files |
| LOW 11 nits | pack exe sha256 must equal the REPRO sha256 (asserted); BOM / spaces-in-path / Local\ mutex / o3 timestamp flag documented here, not changed |

Runs started before these edits used the earlier code; their records stand as written (the review found no wrong
verdict in them).
