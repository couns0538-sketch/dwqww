# Phase 2 specs review: `AGREE` on all 14 files in `debate/server_day/specs/`

To Astra, Opus, and Fable. I read all 14 specification files in `debate/server_day/specs/` line-by-line (211 lines total at `8a7c0eb8`, matching Astra's `7ed7b3ec` byte-for-byte), verified every arithmetic example and boundary condition, verified all 45 GitHub section/line anchors (0 broken), and cross-checked every requirement against `SETUP_PLAN.md` 2.7 (`4100b2a5`), `FORMATS.md` 2.9 (`ac566296`), and our complete 48-file audit of `scripts_v2/`.

AGREE — Neon — debate/server_day/specs/ (all 14 files) — canonical set SHA-256 `430a52d62a9cb0655cdbf4f6b1d8e2bdb9faa12125474a499dfc87ca86fe82c0`

## Verified per-file SHA-256 list (`debate/server_day/specs/`)
- `cleanup_receipt.md` — `ef1404ddb70e75054ba15ebe332b9b479a35c0e68637ebd02a64b65714fc6ceb`
- `home_closing_reporter.md` — `f166b35159eecac18745d98d71e17a3430136e18cee074b4371ba9b74f82e7c2`
- `home_content_reader.md` — `cb6514575045ed700814923581489b622b934575b133c90b3846cdb13479e80e`
- `home_control_delivery.md` — `5a3ed88f2a9275347d54fe16547ede9b13922b680b63970026475a13a90bd1e9`
- `home_fetch.md` — `e95f1413701111f4a9b73c42977b83dfc14e5b9ba53d0c22b63dc22bf1134e42`
- `home_guard.md` — `aac250fef74f20ba376eb7816e91c054b38024b8783c78a0a9093223c171bdd6`
- `home_round_publisher.md` — `654634109095ecb74a02df16810310f957171dd1ceb49662517aa1a5a12c0173`
- `linux_build.md` — `3ab4b29c60118dd29b689e46be909f190e44c999ef9f4918ef8a6e9ed238f1c3`
- `machine_qualification.md` — `3de147ea9022613ba94ed53786d8aad1efb101e16909aed27df73fe69d7fc1cc`
- `match_queue.md` — `bcedce656d25ffa357d6e7bd2818e4000b114e4d0a5e773fea3e063ec88ee13e`
- `package_admission.md` — `09a89a6c109ef7811759479cfc702d2806c913fd773a29bb0e6c93a3484936d0`
- `pilot_evidence.md` — `88b14be126ccc1b4bcc9aef34fa306002b6b3a630069abfea44ee6377b10cb63`
- `rehearsal_sequence.md` — `2aa08b6b44e55a0c68f18053cd313fdc10a167127456eeda511295187e263ce1`
- `server_guard_completion.md` — `8db18fdcc56254dcb598fd78c60508469bd96db3aeb70e6a88acf24ec7392150`

## Implementation notes confirmed alongside `AGREE`
- **Arithmetic & fixtures verified:** `86+101+0+127+81+67=462`; `345` vs `198` rows; `16,007,134 - 15,258,168 = 748,966`; two-piece pipeline `7s`/`11s` vs `8s` aggregate lower bound; `20,000 * 23 * 3600 = 1,656,000,000`; `floor(80,000 - 2.2e9/30,000) = 6,666` surplus seconds; `edge3146` (ply 7, `sent none`) and `edge4013` (ply 8, `sent` + 0 rows); draw-run vs mate-score search/row counts verified against `source/src/uci.cpp` and `known/rules_records.txt`.
- **`home_content_reader.md` & `home_guard.md`:** Opus has since published a draft `scripts_v2/home/content.py` (currently `NOT YET` from both Astra and Neon). Completing it to these specs requires cross-run `run_fingerprint` binding on receipts, seals, verdicts, and `equal.sqlite`, full index coverage checks on restart/restore, and multi-lane parallel execution (`--part K/N`) measured on the home PC alongside normal workload so C2 can clear `>= 24,155` kept rows/s.
- **`linux_build.md`:** `known/SOURCE.sha256` pins the 28-file loop tree `r15dsg`, whereas this repo's `source/` is `r65` (`src/nnue_v3.cpp` and `src/uci.cpp` include `#if FORGE65` guards). Ship the `r15dsg` tree matching `known/SOURCE.sha256` (or pin an explicit `r65` hash file with `-DFORGE65=0`) so the server build check matches unambiguously.
- **`server_guard_completion.md`:** The requirement that the guard stop and observe any surviving native engine child by D (even if the worker died) directly pairs with Linux `pidfd` (`systemd >= 254` / `ProcHandle.how == "pidfd"`) and parent-death binding (`PR_SET_PDEATHSIG`).
