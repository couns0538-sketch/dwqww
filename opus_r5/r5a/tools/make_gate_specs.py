#!/usr/bin/env python3
"""R5A M4: write opus_r5/r5a/gate_specs.json and GATE_SPECS.md from one table (so both always agree).

Smoke verdicts are read from opus_r5/r5a/smoke/<name>/summary.json when present ("pending" otherwise).
usage: make_gate_specs.py <r5a dir>
"""
import json
import os
import sys

R5A = sys.argv[1]
EXE_SRC = r"F:\opus_scratch\r5\r5a\exe\forge_r5a_m2_0a01ec53.exe"
EXE_SHA = "fda298e6df180a067c323d0bf68434e365cd2eef55617e671c57b4dea700738a"
EXE_INSTALL = "forge_r5a_singles.exe"
COMMIT = "e22d3649 (M2 push; search identical to forge-bundle-int b7c17722)"
OFF_PINS = [312866, 862329, 3024920, 12389307, 34048354]
BOOK = r"C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn"
SPRT = {"elo0": 0, "elo1": 10, "alpha": 0.05, "beta": 0.05, "model": "normalized"}

# rank, id, name, options, primary TC, smoke dir, ON pins d11/d13/d16, conflicts with B1-B4, reason, evidence
GATES = [
    (1, "R5A-1", "CorrHistPlus=4", ["CorrHistPlus=4"], "10+0.1", "corrhistplus4", [340927, 734347, 2794671],
     "B1/B3 use CorrHistPlus=1: combinable as the bitmask 5 (1|4). B2/B4 use CorrHistV2: exclusive (the UCI refuses "
     "the pair in both orders, M2 tests), so a pass transfers to B1/B3 only.",
     "Best prior of the set: the related NonPawnCorr+PawnHist pack ended with a positive LLR in all 4 of its PC gates "
     "(0.63-2.48 at [0,10], all capped; R3-3 R3-03); non-pawn correction history is public practice in strong engines. "
     "Cheap at 10+0.1, smallest conflict surface.",
     "C2 (opus_round1), R3-3 R3-03"),
    (2, "R5A-2", "CorrExt=1", ["CorrExt=1"], "40+0.4", "corrext1", [312961, 838790, 2891507],
     "None: no preset touches singular extensions (FB2 SingularV2, which overlaps it, is not on this branch and in no "
     "preset); CorrExt runs in its own search instance and combines with CuckooRep (all presets) via search_ce_cu.",
     "Independent of every bundle, so its result transfers. Weak at short TC by design (extensions compound with "
     "depth; equal to OFF at go depth 10 on all four M1 positions; O8: 'lost at STC'), hence 40+0.4 primary as the "
     "job and the test plan say; about 4x the wall time of a 10+0.1 gate.",
     "O8, R3-3 R3-14"),
    (3, "R5A-3", "CorrMargins=1", ["CorrMargins=1"], "40+0.4", "corrmargins1", [343365, 858019, 2522546],
     "Entangled with every preset: TtPruneV2 (B1-B4) adds its improving/worsening terms to the same RFP and futility "
     "margins inside the CorrMargins instance (M2 prints a warning for the pair). A standalone result does not "
     "transfer to a bundle; a pass needs a combined re-gate.",
     "Plausible idea (correction-size-aware pruning/LMR is public practice); O5 notes correction terms gain more at "
     "longer TC, hence 40+0.4 primary. Ranked after CorrExt because of the TtPruneV2 entanglement.",
     "O5, R3-3 R3-09"),
    (4, "R5A-4", "CorrHistPlus=2", ["CorrHistPlus=2"], "10+0.1", "corrhistplus2", [296553, 824640, 2914749],
     "As CorrHistPlus=4: combinable with B1/B3 (bitmask 3), exclusive with B2/B4 (CorrHistV2).",
     "Weaker prior than bit 4 (no related positive gate); its deep trees grow (R3-3: d20 +12.6%, d22 +18.9%), the "
     "crew flag for a longer-TC confirm after an H1.",
     "C2, R3-3 R3-05"),
    (5, "R5A-5", "CorrHistPlus=6", ["CorrHistPlus=6"], "10+0.1", "corrhistplus6", [357478, 747883, 2544596],
     "As CorrHistPlus=4 (bitmask 7 with B1/B3; exclusive with B2/B4).",
     "The 2+4 combination: gate only after R5A-1 and R5A-4 (if bit 4 passes and bit 2 is flat, skip it). New pins "
     "here (no earlier record).",
     "C2"),
    (6, "R5A-6", "NetScale=99", ["NetScale=99"], "10+0.1", "netscale99", [308948, 917342, 2601047],
     "Moves every eval margin, so it interacts with TtPruneV2 (all presets) and CorrMargins; no table or option "
     "conflict.",
     "The only defensible value from M1: S41 measured the lock net s198 +1.2% wider than h256_e12 (the scale the "
     "margins were tuned on), 99 maps it back; 97/101/103 have no measurement behind them. Expected effect about "
     "zero (R3-3 R3-11), so it goes after the option gates.",
     "S41 EVALSCALE_20261027.md, R3-3 R3-11"),
    (7, "R5A-7", "HistRework=3", ["HistRework=3"], "10+0.1", "histrework3", [336192, 869621, 3052885],
     "B1/B4 use HistRework=2: levels are alternative values of one option, never combined.",
     "Conditional: only if HistRework=2 (B1/B4 or R3-3 R3-08) ends H1 or capped with Elo > 0 (A1 plan).",
     "A1, R3-3 R3-15"),
    (8, "R5A-8", "HistRework=1", ["HistRework=1"], "10+0.1", "histrework1", [373261, 1043893, 3399770],
     "As HistRework=3.",
     "Last or skip: fails the crew node screen (d13 +21.1%, d16 +12.4% vs OFF, M1 = R3 pins).",
     "A1, R3-3 R3-19"),
]


def smoke_verdict(name):
    path = os.path.join(R5A, "smoke", name, "summary.json")
    if not os.path.exists(path):
        return {"verdict": "pending", "summary": None}
    s = json.load(open(path))
    stress = s.get("stop_stress") or {}
    return {"verdict": s["verdict"], "summary": f"opus_r5/r5a/smoke/{name}/summary.json",
            "games": f"{s['games_played']}/{s['games_planned']}", "failures": s["failure_counts"],
            "stop_stress": f"{stress.get('completed', 0)}/{stress.get('iterations', 0)} problems "
                           f"{len(stress.get('problems', []))}" if stress else "skipped"}


def main():
    entries = []
    for rank, gid, name, opts, tc, smoke, pins, conflicts, reason, evidence in GATES:
        entries.append({
            "rank": rank, "id": gid, "name": name,
            "tag_suggestion": f"gate{gid.replace('-', '_')}_{name.replace('=', '').lower()}_vs_r5aoff",
            "cand": {"exe_install_name": EXE_INSTALL, "exe_source": EXE_SRC, "sha256": EXE_SHA,
                     "options": [f"option.{o}" for o in opts]},
            "opponent": {"name": "base_r5a_off", "exe_install_name": EXE_INSTALL, "sha256": EXE_SHA, "options": []},
            "both_sides": ["option.Threads=1", "option.Hash=16", "option.OwnBook=false"],
            "tc_primary": tc, "tc_secondary": "10+0.1" if tc == "40+0.4" else None,
            "sprt": SPRT, "cap_games": 3000,
            "srand": "", "openings_start": "",
            "book": {"file": BOOK, "format": "pgn", "order": "random"},
            "prebench_depths": [11, 13, 16],
            "prebench": {"cand_off": OFF_PINS[:3], "cand_on": pins},
            "off_identity": {"bench_d11_d13_d16_d20_d22": OFF_PINS, "perft5_startpos": 4865609,
                             "perft5_kiwipete": 193690690, "fma": 0},
            "expected_echo": f"info string active: {' '.join(opts)}",
            "smoke": smoke_verdict(smoke),
            "conflicts_b1_b4": conflicts, "reason": reason, "evidence": evidence,
            "status": "UNPROVEN, no Elo claim; gate-ready candidate (owner installs the exe, adds srand/openings start)",
        })
    doc = {"job": "Forge Opus round 5A (opus-r5a-singles)", "commit": COMMIT,
           "rule": "one option set per gate, candidate vs the same exe all-OFF; SPRT [0,10] normalized; cap 3000; "
                   "srand and openings start left blank for the queue owner",
           "exe": {"source": EXE_SRC, "sha256": EXE_SHA, "install_name": EXE_INSTALL,
                   "build": "opus_r5/r5a/tools/build_r5a.sh (g++ 15.2 -O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 "
                            "-fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256, static)"},
           "gates": entries}
    with open(os.path.join(R5A, "gate_specs.json"), "w", newline="\n", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")

    md = []
    md.append("# R5A gate pack: one option per gate vs the same exe all-OFF (UNPROVEN, no Elo claims)\n")
    md.append(f"Generated by `tools/make_gate_specs.py` together with `gate_specs.json` (same data). Branch "
              f"`opus-r5a-singles`, {COMMIT}.\n")
    md.append("Common to every entry:")
    md.append(f"- Exe (candidate and opponent are the same binary): `{EXE_SRC}`, sha256 `{EXE_SHA}`; suggested install "
              f"name `{EXE_INSTALL}` (the owner installs it; this job never touches forge_push\\bin or the manifest).")
    md.append("  Default build: every option OFF; OFF identity bench d11/13/16/20/22 = 312866 / 862329 / 3024920 / "
              "12389307 / 34048354, perft 5 = 4865609, kiwipete 193690690, FMA 0 (REPORT.md M2).")
    md.append("- Both sides: `Threads=1 Hash=16 OwnBook=false`; the candidate adds only its `option.<Name>=<value>`.")
    md.append("- SPRT `elo0=0 elo1=10 alpha=0.05 beta=0.05 model=normalized`; `cap_games` 3000 (int); "
              "**srand: blank; openings start: blank** (queue owner fills both).")
    md.append(f"- Book `{BOOK}` (pgn, order random).")
    md.append("- Pins: `prebench.cand_on` are the M1 ON benches d11/d13/d16 (Threads 1, Hash 16); "
              "`cand_off` the lock pins. The candidate prints `info string active: <Name>=<value>` at every go "
              "(M2), so the gate log shows the option really applied; the opponent prints nothing new.")
    md.append("- Smoke (M3): 200 games ON vs OFF at 5+0.05 + 50x go/stop stress per option; verdict below "
              "(crash/legality/clock screen, not strength).\n")
    md.append("## Ranked order\n")
    md.append("| rank | id | candidate option | primary TC | ON d11 / d13 / d16 | smoke | conflict with B1-B4 (short) |")
    md.append("|---|---|---|---|---|---|---|")
    short = {
        "R5A-1": "B1/B3 ok (mask 5); B2/B4 exclusive", "R5A-2": "none (independent)",
        "R5A-3": "TtPruneV2 in all four: same margins", "R5A-4": "B1/B3 ok (mask 3); B2/B4 exclusive",
        "R5A-5": "B1/B3 ok (mask 7); B2/B4 exclusive", "R5A-6": "moves all margins (TtPruneV2, CorrMargins)",
        "R5A-7": "alternative to HistRework=2 (B1/B4)", "R5A-8": "alternative to HistRework=2 (B1/B4)",
    }
    for e in entries:
        p = e["prebench"]["cand_on"]
        sm = e["smoke"]
        sm_text = sm["verdict"] if sm["verdict"] == "pending" else f"{sm['verdict']} ({sm['games']}, stress {sm['stop_stress']})"
        md.append(f"| {e['rank']} | {e['id']} | `{e['name']}` | {e['tc_primary']} | {p[0]} / {p[1]} / {p[2]} | "
                  f"{sm_text} | {short[e['id']]} |")
    md.append("")
    md.append("## Entries\n")
    for e in entries:
        md.append(f"### {e['rank']}. {e['id']} · {e['name']}\n")
        md.append("| field | value |")
        md.append("|---|---|")
        md.append(f"| candidate options | `{' '.join(e['cand']['options'])}` (plus the common Threads/Hash/OwnBook) |")
        md.append(f"| opponent | `base_r5a_off`: same exe, no options |")
        md.append(f"| TC | primary **{e['tc_primary']}**" + (f"; {e['tc_secondary']} informational only" if e['tc_secondary'] else "") + " |")
        md.append(f"| SPRT / cap | [0,10] normalized, a=b=0.05; cap_games 3000 |")
        md.append(f"| srand / openings start | blank / blank |")
        md.append(f"| prebench cand_on (d11/d13/d16) | {' / '.join(str(x) for x in e['prebench']['cand_on'])} |")
        md.append(f"| prebench cand_off | 312866 / 862329 / 3024920 |")
        md.append(f"| expected echo | `{e['expected_echo']}` |")
        sm = e["smoke"]
        md.append(f"| smoke | {sm['verdict']}" + (f": {sm['games']} games, failures {sm['failures']}, stop stress {sm['stop_stress']} (`{sm['summary']}`)" if sm['verdict'] != 'pending' else "") + " |")
        md.append(f"| conflicts with B1-B4 | {e['conflicts_b1_b4']} |")
        md.append(f"| why this rank | {e['reason']} |")
        md.append(f"| sources | {e['evidence']} |")
        md.append("")
    md.append("## fastchess template (as the R3 queue builds it; fill SRAND and START, set concurrency per queue policy)\n")
    md.append("```")
    md.append(r"fastchess.exe -engine name=cand_<id> cmd=<bin>\forge_r5a_singles.exe option.Threads=1 option.Hash=16 "
              r"option.OwnBook=false option.<Name>=<value> -engine name=base_r5a_off cmd=<bin>\forge_r5a_singles.exe "
              r"option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=<TC> timemargin=1000 proto=uci "
              r"-openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random "
              r"start=<START> -srand <SRAND> -games 2 -repeat -rounds 1500 -concurrency <N> -sprt elo0=0 elo1=10 "
              r"alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover")
    md.append("```")
    md.append("`-rounds 1500 -games 2` = the 3000-game cap. At the cap with no decision nothing is claimed.\n")
    with open(os.path.join(R5A, "GATE_SPECS.md"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"wrote {len(entries)} entries")


main()
