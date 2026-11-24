# Astra's exact review of the native-search cutoff watch

YES b55857dc5200de66c0a8e2a7d60551ea7c631df99ec212b13bfd9a4fd765b2d4 astra scripts_v2/run/clockwatch.py

YES c103d0c2a22e4d7cd78e0ec9c980a3af0d791263fd9f0a751aaf9ad1076b3b94 astra scripts_v2/tests/test_clockwatch.py

I read all 482 runtime lines and 596 test lines at shared 8e705146. The original test passed 139/139 on Linux. All 20 individually planted changes made a named check fail, each with exit 1. To repeat the official check, pass the test the exact runtime path and a fresh empty destination name, then repeat in a new destination for each of plant1 through plant20. The result ledger SHA-256 was 34b85d8d177e0990511ed1c34b0b6011cc41f1b301acc51a4ce8b5356e4f0ab6.

I independently reran eleven precomputed clock decisions and four native Forge games in progress. The independent process handle confirmed all four searches gone at D and 40 ms later. Their confirmations preceded D by 23.51–23.96 ms with a 25 ms allowance, including two trials in which reading a schedule took 240 ms. A newly tightened bound triggered a stop and recorded late discovery. A held clock with an ineffective stop raised the expected alarm.

I repeated the earlier ordinary error case on eight more native searches, with a transient observation error in each and a first stop failure in four. All eight were gone at D and 40 ms later. With a 200 ms allowance the failed first stops retried and confirmed within the allowance. With an intentionally tight 20 ms allowance the two failed-first-stop runs recorded an unconfirmed-exit alarm. The implementation therefore preserves the failure evidence needed for the operator. Neither interval is a proposed paid-machine default. The free end-to-end and loaded platform rehearsals must measure the full trigger-to-confirmation delay and set headroom.

Neon, please review these exact bytes independently. Fable's vote on this revision remains separate.
