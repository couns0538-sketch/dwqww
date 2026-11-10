# IDEA_SOURCE: opus_spsa_resume

Where each idea or piece of code comes from, and on what licence terms. GPL/AGPL implementations are used as ideas only: no source, constants, tables or weights are copied from them.

| Item | Source | Licence / terms | How it is used |
|---|---|---|---|
| SPSA tuner base (`r9_spsa.py`, report, SVG, sim test) | This repo, `opus-r9-spsa` 73eb280a (`opus_r9/tuner/`) | Repo-internal code | Imported verbatim (blob ids recorded), then extended |
| SPSA method (simultaneous perturbation, gain sequences a_k, c_k) | J. C. Spall, 1992 and 1998 papers | Published method | Ideas only |
| Pair-counted schedule (c_end, r_end, A = 0.1·N) | Fishtest SPSA conventions, as already documented in the R9 IDEA_SOURCE | Ideas only | Same equations as R9; no Fishtest code |
| Pentanomial SPRT/LLR | Standard statistics, as used by Fishtest | Ideas only | Own implementation in `confirm/` |
| fastchess (live dry-run command lines only) | Installed binary `C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe` (sha256 c6d7e445…); licence text at `tools/match/FASTCHESS-LICENSE.txt` on `opus-r9-spsa` 73eb280a | MIT | Invoked as an external program; not copied |
| python-chess (opening partition tool only) | Installed in the grok-pc venv | GPL-3.0 | Imported as an unmodified external dependency (precedent: repo `tools/audit` and `opus_30h/a`); no code copied |
