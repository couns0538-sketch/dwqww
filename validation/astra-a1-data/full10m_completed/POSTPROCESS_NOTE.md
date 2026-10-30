# Resource aggregation correction

The first report-aggregation command raised `KeyError: rss_sum_kib` because the monitor final completion record has no RSS sample. The original resources.jsonl is preserved. The corrected aggregation selects records containing rss_sum_kib and retains all other records explicitly in resource_summary.json. No engine, dataset, monitor log or running validation was modified. This is a reporting harness correction, not a native failure.
