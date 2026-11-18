"""Run the job 1 known answers against one freshly built Forge executable."""
import argparse
import hashlib
import re
import subprocess
from pathlib import Path

CONTROLS = [("Threads", 1), ("Hash", 16)]
S14 = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205),
    ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
    ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
    ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
    ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
    ("HistoryBonusMax", 2212), ("SingularDepth", 6),
    ("IirDepth", 2), ("NonPawnCorrection", "true"),
]
PC20 = S14 + [
    ("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]
PROFILES = {"no-setoption": [], "S14": CONTROLS + S14, "PC20": CONTROLS + PC20}
CASES = {
    "no-setoption": [("bench 11", 312866), ("bench 13", 862329), ("go perft 5", 4865609)],
    "S14": [("bench 11", 242796), ("bench 13", 656517)],
    "PC20": [("bench 11", 278024), ("bench 13", 587276)],
}
BUILDS = {
    "lock": ["no-setoption"],
    "pc": ["no-setoption", "S14", "PC20"],
    "pca": ["no-setoption", "PC20"],
}
EXTRA_RANGES = {"FailHighBlend": 7, "RfpNoTtPv": 1, "RfpTtGuard": 1, "RfpCorrMul": 64}


def fresh(exe, commands, log):
    """Run synchronous UCI commands in a fresh process and log both sides."""
    commands = [*commands, "quit"]
    log.write("INPUT\n" + "\n".join(commands) + "\nOUTPUT\n")
    log.flush()
    result = subprocess.run(
        [str(exe)], input="\n".join(commands) + "\n", text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120,
    )
    log.write(result.stdout)
    log.flush()
    result.check_returncode()
    for line in result.stdout.splitlines():
        if re.search(r"unknown option|invalid value|error", line, re.IGNORECASE):
            raise ValueError(f"engine diagnostic: {line}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", choices=BUILDS)
    parser.add_argument("exe", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    exe = args.exe.resolve(strict=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / f"{args.build}-uci.txt").open("x") as uci:
        uci.write(f"build {args.build}\nexe {exe}\nsha256 {hashlib.sha256(exe.read_bytes()).hexdigest()}\n")
        listing = fresh(exe, ["uci"], uci)
    if "uciok" not in listing.splitlines():
        raise ValueError("engine did not send uciok")
    names = set(re.findall(r"^option name (.+?) type ", listing, re.M))
    needed = set(name for name, _ in CONTROLS)
    for profile in BUILDS[args.build]:
        needed.update(name for name, _ in PROFILES[profile])
    if missing := needed - names:
        raise ValueError(f"options absent from UCI listing: {sorted(missing)}")
    if args.build == "pca":
        for name, maximum in EXTRA_RANGES.items():
            required = f"option name {name} type spin default 0 min 0 max {maximum}"
            if required not in listing.splitlines():
                raise ValueError(f"expected UCI line absent: {required}")
            print(required, flush=True)
    for profile in BUILDS[args.build]:
        options = [f"setoption name {name} value {value}" for name, value in PROFILES[profile]]
        for command, expected in CASES[profile]:
            filename = f"{args.build}-{profile}-{command.replace(' ', '-')}.txt"
            with (args.output_dir / filename).open("x") as raw:
                raw.write(f"build {args.build}\nprofile {profile}\n")
                output = fresh(exe, [*options, "isready", command], raw)
            if "readyok" not in output.splitlines():
                raise ValueError("engine did not send readyok")
            if command == "go perft 5":
                pattern = r"^nodes (\d+)$"
            else:
                depth = command.split()[1]
                pattern = rf"^info string bench depth {depth} nodes (\d+) .*"
            values = re.findall(pattern, output, re.M)
            print(f"{args.build} {profile} {command}: expected {expected}, observed {values}", flush=True)
            if values != [str(expected)]:
                raise ValueError(f"STOP: {filename}")


if __name__ == "__main__":
    main()
