# Forge speed job - RESUME (read this first after a /clear, restart or usage stop)

- Clone: `F:\ospd\wt` (partial + sparse: /opus_speed/ /skills/), branch `opus-speed-20261105`, upstream unset,
  `core.autocrlf=false`, clean filter `novendor` (opus_speed/.gitattributes; .ps1 / .py excluded -> run
  `tools/name_lint.py` before commits). Commit: `git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com
  commit -F <msgfile>` (no trailer). Push: `git push -q -u origin opus-speed-20261105`. `git rm` is refused by the
  permission classifier: unstage with `git restore --staged`.
- AFTER A RESTART: the new [name withheld] process starts at 0xFFFF / Normal. Pin it first (own process, allowed):
  `$p = Get-Process -Id <[name withheld] pid>; $p.ProcessorAffinity = 0x3; $p.PriorityClass = 'Idle'` (09:33 did this).
  Jobs started before a restart keep running (orphaned powershell); check `Get-CimInstance Win32_Process` command
  lines before starting anything again. Workers are resumed with SendMessage to their names (jobc, b1tt, b2mg).
- Scratch: `F:\ospd\` = src\lock (exact lock source), src\b1_* / b2_* (worker copies), src\mut_histmax (mutant),
  builds\, packs\, abba\ (q2\ = variant queue, results_q2.tsv, abba_history.log), ref\fd3a5190\ (reference cache),
  logs\, jobb\, jobc\, tmp\. F: must keep >= 50 GB free; F:\ospd <= 8 GB.
- CPU rule: own builds / checks on 0x3 Idle; ABBA timing on CPU 2 BelowNormal (named mutex), CPU 3 left free.
- A/A reference for this session: `F:\ospd\abba\aa_lock_d20_s3\runs.csv` (balanced ABBA/BAAB, d20).

## Running at 09:47
- ABBA queue q2 (variants vs lock, d20 x 10): list `F:\ospd\abba\queue_variants2.tsv` (append lines to add).
- 12k reference check (orphan from 09:27): `F:\ospd\logs\bx_lockcopy_full12k.out`.
- Packs b2_nnue_zmm then b1_tt_notls (quick L3): `F:\ospd\logs\pack_<name>.out`, `F:\ospd\packs\<name>\`.

## Next steps
1. When READY notes appear in opus_speed/jobb/: `speed_pack.ps1 -SrcDir F:\ospd\src\<name> -Name <name> -Define
   FORGE_SPD_<X>=1 -Quick -AaCsv F:\ospd\abba\aa_lock_d20_s3\runs.csv`.
2. Stack the winners (patches in opus_speed/patches), switch-0 build must equal FD3A5190, full 12k pack of the stack.
3. Move-order mutant (pick_best `>` -> `>=`) through bitexact_check: must fail before ABBA (Job B test 2).
4. Best Job A variant: full pack. Then FINAL_REPORT.md by 14:08.
