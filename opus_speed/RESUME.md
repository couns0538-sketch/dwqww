# Forge speed job - RESUME (read this first after a /clear or usage stop)

- Clone: `F:\ospd\wt` (partial + sparse: /opus_speed/ /skills/), branch `opus-speed-20261105`, upstream unset,
  `core.autocrlf=false`, clean filter `novendor` (opus_speed/.gitattributes; .ps1 / .py excluded from it).
  Commit: `git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com commit -F <msgfile>` (no trailer).
  Push: `git push -q -u origin opus-speed-20261105`.
- Scratch: `F:\ospd\` = src\lock (exact lock source), src\b1_* / b2_* (worker copies), builds\, packs\, abba\, ref\,
  logs\, jobb\, jobc\, tmp\. F: must keep >= 50 GB free; F:\ospd <= 8 GB.
- Workers (started ~08:58): jobc (Job C, slot S1), b1tt (TT changes, S2), b2mg (movegen / NNUE, S3). Each writes its
  notes into opus_speed/jobb/ or opus_speed/jobc/ and its patches into opus_speed/patches/; the main session commits.
- CPU rule: own builds / checks on 0x3 Idle; ABBA timing on CPU 2 BelowNormal, CPU 3 left free; never 4-15.

## Next step
Job A tools (uci_lib.ps1, build_variants.ps1, bitexact_check.ps1, abba.ps1, speed_pack.ps1), then the kit self-test
(lp_v1 of the lock source must give sha256 fd3a5190...).
