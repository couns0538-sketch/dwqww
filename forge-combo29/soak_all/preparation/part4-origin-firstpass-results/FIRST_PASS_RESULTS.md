The first pass reproduced the known KRK output unchanged and identified the admitted TT writes preceding the endpoint read. It establishes this recorded payload history; it does **not** establish whether the underlying search result is sound, whether mate17 is optimal, or which deeper search decision first caused the value.

The pinned unmodified baseline and two fresh traced processes all completed with exit0 and no timeout. Settings were Threads1, Hash16, OwnBook false, UseNNUE false, `go depth 13`, from `8/8/8/8/8/1R6/2k5/5K2 w - - 0 1`. All three reported **mate17, 25568 nodes, seldepth22, bestmove b3f3**, and the same complete reported PV:

```text
b3f3 c2d2 f1f2 d2d1 f2e3 d1c2 e3e2 c2c1 f3c3 c1b2 e2d3 b2b1 d3d2 b1b2 c3f3
```

“Complete reported PV” means equality of the full output field, not a complete line to checkmate. Timing and NPS differed and are not performance evidence.

The saved comparison exited0 with **all 11 checks true**: completion, known root identity, expected settings, pinned baseline artifact, repeated trace key, repeated trace artifact, known endpoint presence, empty baseline stderr, expected/untruncated trace stderr, full stdout equality after removing numeric time/NPS, and full repeated trace equality after consistent table-address relabeling. Exact commands/results are in [first-pass/native-logs/](first-pass/native-logs/), with raw stdout/stderr/input traffic and run summaries under [first-pass/runs/](first-pass/runs/). [IDENTITY_CHECKS.json.txt](IDENTITY_CHECKS.json.txt) extracts the existing comparison result without rerunning it.

The native key query returned target key `6827293331010548038` for `8/8/8/8/8/5R2/1k1K4/8 b - - 15 8`. The trace contains 520 numbered events, without truncation. The relevant table identity in trace-r1 is `0x7ffde1fcd500`, epoch5, generation1, physical cluster97021, slot0, verification key2890330438. The address is process-specific; slot/payload/frame history remains identical in the repeat after address relabeling.

| Recorded step | Exact evidence | What the record establishes |
| --- | --- | --- |
| First admitted mate payload for this watched key/slot | frame23225; seq361–370, especially STORE_AFTER seq368 | Main search at root depth13, ply9, entry depth6, window `[-495,-477]`, current clock9. It probed a nonmate Upper payload `-509`, later returned `-31973`, and admitted raw `-31982`, depth6, Upper (`bound=1`), at MAIN_FINAL. This is the first mate-valued admitted write in the captured target ledger. |
| Last admitted writer before the endpoint read | frame25044; seq483–492, especially STORE_AFTER seq490 | Main search at root depth13, ply9, entry depth9, window `[-31966,-31965]`, clock9. It returned `-31973` and admitted raw `-31982`, depth9, Upper, eval `-432`, at MAIN_FINAL. The stored move remained `b2b1`; the attempted move was none. |
| Endpoint consumer | frame25109; seq493–502, especially WORKER_PROBE seq496 | Qsearch at root depth13, ply15, current clock15, window `[-31971,-31965]` reads that depth9/Upper payload with stored clock9. Raw `-31982` adjusts to `-31967`; the recorded score-usability predicate is true. |
| Endpoint use and attempted write | TT_SUBSTITUTION seq497; STORE_AFTER seq500; RETURN seq501 | Qsearch replaces prior eval `-440` with `-31967`, attempts a depth0 Upper store, and receives `admitted=0`. The depth9 payload remains. It returns `-31967` through QS_FINAL with `pv_length=0`; this is not recorded as a direct QS_TT cutoff. |

The last writer's full board state is `8/8/8/8/8/5R2/1k1K4/8 b - - 9 5`; the consumer's state is the same keyed placement at clock15/fullmove8. Their full histories and ancestry are preserved in the raw events. No intervening store appears between admitted write seq490 and consumer probe seq495. The consumer's rejected write is therefore not the earlier payload producer.

[TRACE_PROVENANCE_EXCERPT.txt](TRACE_PROVENANCE_EXCERPT.txt) preserves exact trace-r1 events seq359–370 and seq483–502; these are extracts, not rewritten events. [first-pass/origin-ledger.json.txt](first-pass/origin-ledger.json.txt) retains the previously prepared ledger, including 28 accepted writes for the target and the matched consumer/probe/last-writer records. The raw trace remains the primary evidence. Frame23225 identifies the first captured mate-payload producer for this target; its untraced child dependencies remain a separate investigation.

The post-native input verification at **2026-11-14 17:23:25.327 UTC** reports **all14 monitored inputs unchanged**: the pinned search/UCI sources, search header, release baseline, eight release objects, flags, and link recipe. The original record is copied unchanged as [first-pass/readonly-inputs-after-firstpass.json.txt](first-pass/readonly-inputs-after-firstpass.json.txt). This is the recorded post-run comparison, not a claim to have hashed every repository file.

The baseline SHA256 is `e2788a101d11acfca637b14471e2b067ae11e551500cfb0656019a193ec2cb3e`; both trace summaries identify `c76fde7dee0cc63a2f22b27b040f3bc4c57a3176da3ff19ee04ca331761e82c9`. No binary or object is published here. [EXCLUDED_BINARY_ARTIFACTS.json.txt](EXCLUDED_BINARY_ARTIFACTS.json.txt) lists the three excluded scratch native artifacts and nine external baseline/object inputs by hash.

The separate [remote-review/REUSE_UPDATE.md](remote-review/REUSE_UPDATE.md) summarizes frozen r3/r4 source reuse candidates. Remote branch test, match, sanitizer, and replay outcomes remain branch-reported and unverified by that static review. They provide no conclusion about this observed writer's correctness and do not restore the eight low-clock equality differences. No strength or speed conclusion is made.
