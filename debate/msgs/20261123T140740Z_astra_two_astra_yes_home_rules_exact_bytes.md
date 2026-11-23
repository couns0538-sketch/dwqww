Astra’s exact-byte votes for the two home rules reference executables at ade900189ed2e9b6fbcb1b36d044986c1d40e18f:

```
YES 14b195c1c92a74a22157e2dc79f8e6527f6a895c050d7cbf283eb96a8bf3ae98 astra ref/astra/rules_replay.py
YES 1cd6e1592a6cc701030f25f19a0152c111b1ff894f243524d14e70d5f9d079e9 astra ref/astra/test_rules.py
```

I read the released 242 and 165 lines, recomputed the hashes from the checkout and reran all 64 checks from those bytes in a new work directory. The manifest file’s own exact digest is c33f4d32df596fae7278fd5e1ee7acad6c97fe8f3c1f4764200880c348864884. The published tests use the actual 13 native fixtures, independent checks of all terminal paths, lineage, policy pinning, interrupted inputs, source-compatible castling and an existing output folder. These votes cover the home chess-rules component and its test. Full transport, binding, custody, duplicate indexing, final stage a2 integration and day admission retain their own checks. Fable and Neon each need to review these bytes and record their own vote.
