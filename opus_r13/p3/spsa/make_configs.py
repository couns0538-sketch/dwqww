"""R13 P3: write the two SPSA configs (budget fixed up front: 160 pairs per bit at 5+0.05, concurrency <= 2)."""
import json

common = {
    "engine": r"C:\o13\handoff\p3_sf26\forge_ltopgo_sfs.exe",
    "fastchess": r"C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe",
    "book": r"C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn",
    "book_format": "pgn", "book_openings": 34700, "tc": "5+0.05", "hash": 16,
    "pairs_planned": 160, "pairs_per_batch": 2, "alpha": 0.602, "gamma": 0.101, "A_ratio": 0.1,
    "governor": {"cap_percent": 105, "pause_percent": 120, "pause_after": 60, "max_concurrency": 2, "min_free_gb": 6,
                 "sample_seconds": 3, "wait_seconds": 60, "cpus_per_game": 1.0},
}
runs = {
    2: (["option.Sf26NmpPrior=1"], [
        {"name": "Sf26NmpPriorBonus", "start": 16, "lock_default": 16, "min": 0, "max": 100, "c_end": 4, "r_end": 0.06},
        {"name": "Sf26NmpPriorCap", "start": 3, "lock_default": 3, "min": 1, "max": 8, "c_end": 1, "r_end": 0.06}]),
    4: (["option.Sf26LmrGap=1"], [
        {"name": "Sf26LmrAlphaGap", "start": 260, "lock_default": 260, "min": 50, "max": 1000, "c_end": 40, "r_end": 0.06}]),
}
for bit, (fixed, params) in runs.items():
    cfg = dict(common)
    cfg["name"] = f"R13 P3 SPSA, Sf26 bit {bit} (switch on in both engines); fixed budget 160 pairs at 5+0.05, conc <= 2"
    cfg["seed"] = 13000 + bit
    cfg["fixed_options"] = fixed
    cfg["params"] = params
    with open(f"C:/o13/p3/spsa/sf26_bit{bit}.json", "w", newline="\n") as fh:
        json.dump(cfg, fh, indent=1)
    print(bit, cfg["seed"], fixed, [p["name"] for p in params])
