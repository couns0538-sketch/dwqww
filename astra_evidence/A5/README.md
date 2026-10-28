# A5 perft CI qualification

Existing Forge perft fixtures already cover both requested cases. Existing opus-ci only triggers on opus-* pushes. Added a dedicated astra-* push / relevant pull-request / manual workflow using the original suite, with no engine changes or new expected values.

Local replay executed the actual workflow run blocks (only source/build paths relocated): Release GCC 14.2, strict FP, h256; target forge_perft_suite; CTest forge_perft_cpw with --max-depth 5 --max-nodes 5000000. PASS: startpos d5 **4865609**, kiwipete d4 **4085603**; all 5 selected cases PASS, total **15623917** nodes. The workflow explicitly requires both lines in addition to CTest success.

Negative control: a temporary fixture with startpos expectation increased by one correctly exits 1 and prints the mismatch; tracked fixtures unchanged. Original build/test logs retained here. Existing compiler warnings were not changed by this workflow-only job.

Hosted GitHub Actions execution **UNVERIFIED**: API access returned Forbidden. The local workflow replay and YAML parse passed; this is not a claim that a hosted run passed.

IDEA_SOURCE: Owner A5 and existing Forge perft suite only.
