"""Declared SPRT [0, 5] for LmrDeeperShallower (Opus 22:19 PC recommendation: zero C++ change,
cheapest single search candidate).

Writes pre-match declaration BEFORE game 1, runs fastchess with normalized SPRT [0, 5],
alpha=0.05, beta=0.05, parses pentanomial & SPRT LLR verdict cleanly, and supports either
fixed-nodes (50k) or equal-time (6+0.06 with CLOCK_MATCH_RUNNING lockfile).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
FASTCHESS = LAB / "tools/fastchess/fastchess-windows-x86-64/fastchess.exe"
BOOK = LAB / "tools/book/UHO_Lichess_4852_v1.epd"
LIVE_PGO_EXE = LAB / "runs/forge/engines/v3-r15dsg-sp-clang/forge.exe"
BASE_EXE = FIX / "builds/base_r15dsg.exe"
R0067 = LAB / "runs/forge/r0067/train/cand.fnn3"
LOCK = LAB / "neon/CLOCK_MATCH_RUNNING"

# Full 45 live Big Tune v3_uci_options (copied read-only from live Forge config)
BIG_TUNE_OPTS = [
    ("Hash", "16"), ("Threads", "1"), ("NNUEArch", "true"),
    ("NmpBase", "3"), ("NmpDiv", "4"), ("NmpEvalDiv", "235"), ("NmpMaxEvalRed", "3"),
    ("RfpMargin", "85"), ("RfpMaxDepth", "9"), ("RfpImprovingMargin", "65"),
    ("FpBase", "125"), ("FpSlope", "110"), ("FpMaxDepth", "7"),
    ("RazorMargin", "280"), ("RazorMaxDepth", "2"),
    ("LmrBase", "75"), ("LmrDiv", "225"), ("LmrPvReduce", "1"), ("LmrNotImproving", "1"),
    ("LmrCutNode", "1"), ("LmrQuietHistDiv", "5000"), ("LmrCapHistDiv", "6000"),
    ("LmpBase", "3"), ("LmpMult", "1"), ("LmpMaxDepth", "8"),
    ("SeeQuietMargin", "-65"), ("SeeCaptureMargin", "-100"), ("SeeMaxDepth", "8"),
    ("HistPruneMargin", "-2000"), ("HistPruneMaxDepth", "4"),
    ("SingMinDepth", "8"), ("SingMarginMult", "2"), ("SingDoubleExtMargin", "20"),
    ("ProbCutMargin", "200"), ("ProbCutMinDepth", "5"),
    ("IirMinDepth", "4"), ("AspDelta", "15"),
    ("PawnCorrWeight", "100"), ("NonPawnCorrWeight", "100"), ("ContCorrWeight", "80"),
    ("CaptureFutilityBase", "150"), ("FailLowContinuationBonus", "20"),
    ("EvalSwingMult", "100"),
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_live_uci_options() -> list[tuple[str, str]]:
    """Read exact live v3_uci_options from pipeline/forge.toml if present."""
    for cand in [LAB / "pipeline/config.forge.toml", LAB / "pipeline/forge.toml"]:
        if cand.exists():
            import tomllib
            cfg = tomllib.loads(cand.read_text(encoding="utf-8"))
            opts = cfg.get("engine", {}).get("v3_uci_options") or cfg.get("engine", {}).get("uci_options")
            if isinstance(opts, dict) and opts:
                out = []
                for k, v in opts.items():
                    if k == "NNUEArchFile":
                        continue
                    out.append((str(k), "true" if v is True else "false" if v is False else str(v)))
                if not any(k == "NNUEArch" for k, _ in out):
                    out.append(("NNUEArch", "true"))
                return out
    return list(BIG_TUNE_OPTS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="SPRT_LmrDeeperShallower_0_5_50k")
    ap.add_argument("--exe", default=str(BASE_EXE))
    ap.add_argument("--net", default=str(R0067))
    ap.add_argument("--nodes", type=int, default=50000)
    ap.add_argument("--tc", default="", help="If set (e.g. 6+0.06), runs equal-time SPRT with CLOCK_MATCH_RUNNING")
    ap.add_argument("--max-rounds", type=int, default=2000, help="Game pairs (2000 pairs = 4000 games max)")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--seed", type=int, default=202611601)
    ap.add_argument("--elo0", type=float, default=0.0)
    ap.add_argument("--elo1", type=float, default=5.0)
    args = ap.parse_args()

    is_clock = bool(args.tc)
    out_dir = FIX / "matches" / args.name
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "summary.json"
    if summary_path.exists():
        print(f"SKIP {args.name}: summary already exists")
        return 0

    exe = Path(args.exe)
    net = Path(args.net)
    assert exe.exists(), f"Missing exe: {exe}"
    assert net.exists(), f"Missing net: {net}"

    base_opts = load_live_uci_options()
    base_opts = [(k, v) for k, v in base_opts if k != "LmrDeeperShallower"]
    decl = {
        "match_name": args.name,
        "declared_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S PC"),
        "rule": (
            f"Opus-recommended declared normalized SPRT [{args.elo0}, {args.elo1}] "
            f"(alpha=0.05, beta=0.05, max_games={args.max_rounds * 2}) for UCI option "
            f"LmrDeeperShallower=true vs false (zero C++ changes; never pooled with prior runs)."
        ),
        "mode": f"clock {args.tc}" if is_clock else f"fixed_nodes {args.nodes}",
        "exe": str(exe),
        "exe_sha256": sha256_file(exe),
        "net": str(net),
        "net_sha256": sha256_file(net),
        "book": str(BOOK),
        "seed": args.seed,
        "concurrency": args.concurrency,
        "sprt": {"elo0": args.elo0, "elo1": args.elo1, "alpha": 0.05, "beta": 0.05, "model": "normalized"},
        "max_games": args.max_rounds * 2,
        "cand_diff": {"LmrDeeperShallower": "true"},
        "base_diff": {"LmrDeeperShallower": "false"},
        "shared_uci_opt_count": len(base_opts),
    }
    (out_dir / f"declaration_{args.name}.json").write_text(json.dumps(decl, indent=2), encoding="utf-8")

    def eng_args(name: str, lmr_val: str) -> list[str]:
        a = ["-engine", f"cmd={exe}", f"name={name}"]
        if is_clock:
            a.append(f"tc={args.tc}")
        else:
            a.append(f"nodes={args.nodes}")
            a.append("tc=inf")
        a.append(f"option.NNUEArchFile={net}")
        for k, v in base_opts:
            a.append(f"option.{k}={v}")
        a.append(f"option.LmrDeeperShallower={lmr_val}")
        return a

    pgn_path = out_dir / "games.pgn"
    log_path = out_dir / "fastchess.log"
    cmd = [
        str(FASTCHESS),
        *eng_args("cand_LmrDeeper", "true"),
        *eng_args("base_r15dsg", "false"),
        "-openings", f"file={BOOK}", "format=epd", "order=random",
        "-srand", str(args.seed),
        "-rounds", str(args.max_rounds), "-games", "2", "-repeat",
        "-concurrency", str(args.concurrency),
        "-sprt", f"elo0={args.elo0}", f"elo1={args.elo1}", "alpha=0.05", "beta=0.05", "model=normalized",
        "-ratinginterval", "20",
        "-recover",
        "-resign", "movecount=3", "score=600", "twosided=true",
        "-draw", "movenumber=34", "movecount=8", "score=10",
        "-maxmoves", "300",
        "-pgnout", f"file={pgn_path}", "min=true",
    ]
    if is_clock:
        cmd += ["-each", "timemargin=100"]

    t0 = time.time()
    if is_clock:
        LOCK.write_text(f"{args.name} started {datetime.now().isoformat()}\n", encoding="utf-8")
    try:
        with log_path.open("w", encoding="utf-8") as lf:
            proc = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
    finally:
        if is_clock and LOCK.exists():
            LOCK.unlink()

    elapsed = time.time() - t0
    txt = log_path.read_text(encoding="utf-8", errors="replace")
    m_score = list(re.finditer(r"Score of cand_LmrDeeper vs base_r15dsg:\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)", txt))
    m_ptnml = list(re.finditer(r"Ptnml\(0-2\):\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)", txt))
    m_llr = list(re.finditer(r"LLR:\s*([+-]?\d+\.\d+)\s*\(([+-]?\d+\.\d+),\s*([+-]?\d+\.\d+)\)\s*\[([^\]]+)\]", txt))
    verdict = "INCONCLUSIVE"
    if "H1 was accepted" in txt:
        verdict = "H1_ACCEPTED"
    elif "H0 was accepted" in txt:
        verdict = "H0_ACCEPTED"
    w = l = d = 0
    if m_score:
        w, l, d = map(int, m_score[-1].groups())
    ptnml = list(map(int, m_ptnml[-1].groups())) if m_ptnml else []
    llr = float(m_llr[-1].group(1)) if m_llr else None
    n = w + l + d
    elo = 0.0
    if n > 0 and 0 < (w + 0.5 * d) < n:
        s = (w + 0.5 * d) / n
        elo = -400.0 * math.log10(1.0 / s - 1.0)
    tl = len(re.findall(r"loses on time", txt, re.I))
    il = len(re.findall(r"illegal move", txt, re.I))
    res = {
        "match_name": args.name,
        "rc": proc.returncode,
        "verdict": verdict,
        "games": n,
        "wins": w,
        "losses": l,
        "draws": d,
        "elo": round(elo, 2),
        "ptnml": ptnml,
        "llr": llr,
        "time_losses": tl,
        "illegal_moves": il,
        "elapsed_sec": round(elapsed, 1),
    }
    summary_path.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"SPRT {args.name}: {verdict} games={n} W-L-D={w}-{l}-{d} elo={elo:+.2f} llr={llr} ptnml={ptnml} tl={tl} il={il} sec={elapsed:.1f}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
