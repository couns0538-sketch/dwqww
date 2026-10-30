# QA Final2 7C — measured probe-log allowance

The estimator now charges 128 bytes per filtered input row, replacing 2048. QA's reported observed size was about 70 bytes per row; 128 is an allowance, not a guarantee. Periodic live free-space guards and the 32 GiB reserve remain in effect. This saves 19.2 GB of estimated headroom per 10M-row shard; it does not alter or remove any existing log.

Commands:
- `python3 -m unittest discover -s tests/data2 -p test_probe_budget.py -v` — red then green (1 passing case).
- `python3 -m unittest discover -s tests/data2 -p test_converter_disk.py -v` — existing disk-guard regressions, including a threshold that passes without log space but refuses with it. Fixture-only explicit cleanup tests operate only on their own temporary directories.

IDEA_SOURCE: QA Final2 7C measurement and requested allowance.
