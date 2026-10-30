# QA Final2 7B — reserve 32 GiB

Converter and holdout audit defaults are now 32768 MiB. The runbook and planner use the same value. Existing explicit command-line overrides remain available for controlled tests.

Command: `python3 -m unittest discover -s tests/data2 -p test_reserve_defaults.py -v`. Red proves the old reserve accepted a mocked 25 GiB disk and the audit default was 20480; green has 3 passing cases. No actual PC capacity measurement or full-shard-fit claim.

IDEA_SOURCE: QA Final2 7B requirement to raise D: reserve above 20000 MiB.
