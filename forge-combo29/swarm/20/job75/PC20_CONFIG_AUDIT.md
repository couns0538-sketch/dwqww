# seat 20 — job 75: did MY PC20 configs have the same bug seat 30's did?

Seat 30's 30-F59 was retracted because its script passed `PC20EXTRA` **alone** — six extras over DEFAULT options,
never S14 + six. That is a construction error, and the obvious question is whether my own PC20 lists have it. This
audits every one of them.

## Result: none of mine has the bug
Each PC20 list is `S14 + the six extras`, where my S14 block already carries `Threads 1` and `Hash 16` — so the
construction is "S14 plus extras", not "extras alone".

| script | S14 carries Threads | S14 carries Hash | S14 option count | PC20 line starts with |
|---|---|---|---|---|
| `job44/band_hm_91_99.py` | yes | yes | 17 | `S14 + [("CuckooRep", "true"), ("HistRework", "2"), …` |
| `job45/band_go_nodes.py` | yes | yes | 17 | `S14 + …` |
| `job46/verify_pc_mate8.py` | yes | yes | 17 | `S14 + …` |
| `job47/softnodes_probe.py` | yes | yes | 17 | `S14 + …` |
| `job48/pc_path_limits.py` | yes | yes | 17 | `S14 + …` |
| `job49/pc_clock_path.py` | yes | yes | 17 | `S14 + …` |
| `job25/pc_honesty.py` | yes | yes | 16 + `Threads/Hash` prefix | `[("Threads",1),("Hash",16)] + S14 + PC20_EXTRA` |
| `job26/pc20_rerun.py` | yes | yes | 16 + prefix | `[("Threads",1),("Hash",16)] + S14 + […]` |

**17 options in my S14 block** = the 14 S14 settings + `Threads` + `Hash` + `OwnBook false`. So every PC20 run of mine
was S14-based, and no published number needs re-running for this reason.

## How I verified, and why not by reading alone
A `grep` for `PC20 =` can match a comment (it does, in `job25`), so I parsed the actual `S14 = [...]` list text and
counted its members, then checked the `PC20 =` line begins with `S14`. I also confirmed the honest-check numbers in
`job25` independently earlier (8/8 published values, S-F32), which could not have matched if that config were
extras-only.

## The general lesson, worth keeping
Seat 30's bug is **invisible in the output**: an extras-only arm still produces a plausible score and a legal move. It
was only catchable by asking for the ordered option list — which is exactly why METHOD now carries "ask for provenance
before refuting" and records that the *option list*, not the binary, was what resolved it.

**A config that is wrong-by-construction looks exactly like a config that is right.** The only defence is naming the
construction in the finding line, and here it is: mine are `S14 (17 options) + 6 extras`.
