"""R7 J4: what would resign / draw adjudication have done to a finished fastchess gate? (offline, PGN read only)
usage: python -I -B adjudication_sim.py <games.pgn> [--rate GAMES_PER_HOUR]
For each rule set below, every game is replayed from its per-move comments ({+0.12/17 0.240s, tl=9.960s}: the
mover's score in pawns, '+M5'-style mates, the move's time) and stopped at the first ply where the rule fires:
  draw  movenumber=N movecount=M score=S : from full move N on, |score| <= S cp on 2*M consecutive plies
  resign movecount=M score=S twosided    : 2*M consecutive plies whose scores, turned to White's view, all say
                                           the same side is ahead by >= S cp (the loser agrees with the winner)
  resign one-sided                       : M consecutive own moves of one engine with score <= -S cp
The adjudicated game is shortened by the time of the plies after the stop (the move times in the comments).
Reported: share of games adjudicated, results changed vs the played result, mean game time before/after,
projected games/hour (measured rate x old mean / new mean), and the pentanomial Elo of the played vs the
adjudicated results (pairs = the two games of one Round with -repeat). Book plies ({book}) never count."""
import collections
import math
import re
import statistics
import sys

path = sys.argv[1]
rate = float(sys.argv[sys.argv.index("--rate") + 1]) if "--rate" in sys.argv else None
TAG = re.compile(r'^\[(\w+) "(.*)"\]')
COMMENT = re.compile(r"\{([^}]*)\}")
SCORE = re.compile(r"^([+-]?)(M?)(\d+(?:\.\d+)?)/\d+\s+(\d+(?:\.\d+)?)s")

games = []
with open(path, encoding="utf-8", errors="replace") as f:
    tags, moves = {}, []
    for line in f:
        m = TAG.match(line)
        if m:
            if m.group(1) == "Event" and tags:
                games.append((tags, " ".join(moves)))
                tags, moves = {}, []
            tags[m.group(1)] = m.group(2)
        elif line.strip():
            moves.append(line.strip())
    if tags:
        games.append((tags, " ".join(moves)))


def plies_of(movetext):
    out = []  # (score_cp from the mover's view or None for book, seconds)
    for c in COMMENT.findall(movetext):
        c = c.strip()
        if c.startswith("book"):
            out.append((None, 0.0))
            continue
        m = SCORE.match(c)
        if not m:
            out.append((None, 0.0))
            continue
        sign = -1 if m.group(1) == "-" else 1
        if m.group(2) == "M":
            cp = sign * 100000
        else:
            cp = sign * round(float(m.group(3)) * 100)
        out.append((cp, float(m.group(4))))
    return out


def dur(s):
    h, mi, se = (int(x) for x in s.split(":"))
    return 3600 * h + 60 * mi + se


RULES = {
    "A resign 3x600 twosided + draw 34/8/8": dict(resign=(3, 600, True), draw=(34, 8, 8)),
    "B resign 3x400 twosided + draw 34/8/20": dict(resign=(3, 400, True), draw=(34, 8, 20)),
    "C resign 3x600 twosided only": dict(resign=(3, 600, True), draw=None),
    "D draw 34/8/8 only": dict(resign=None, draw=(34, 8, 8)),
    "E resign 4x1000 twosided + draw 40/10/5 (conservative)": dict(resign=(4, 1000, True), draw=(40, 10, 5)),
}


def adjudicate(pl, rule):
    """first ply index (0-based, inclusive) where the rule fires and the adjudicated result, else None"""
    draw_run = 0
    lead_run, lead_side = 0, 0
    for i, (cp, _) in enumerate(pl):
        if cp is None:
            draw_run, lead_run = 0, 0
            continue
        mover_white = i % 2 == 0
        white_view = cp if mover_white else -cp
        if rule["draw"]:
            n, m, s = rule["draw"]
            fullmove = i // 2 + 1
            draw_run = draw_run + 1 if (abs(cp) <= s and fullmove >= n) else 0
            if draw_run >= 2 * m:
                return i, "1/2-1/2"
        if rule["resign"]:
            m, s, twosided = rule["resign"]
            side = 1 if white_view >= s else (-1 if white_view <= -s else 0)
            if side != 0 and side == lead_side:
                lead_run += 1
            else:
                lead_run, lead_side = (1, side) if side != 0 else (0, 0)
            if lead_run >= 2 * m:
                return i, "1-0" if lead_side > 0 else "0-1"
    return None


def score_of(result, white_is_cand):
    w = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}[result]
    return w if white_is_cand else 1.0 - w


def penta_elo(pairs):
    """pentanomial Elo +- 95% from per-pair candidate points (0, .5, 1, 1.5, 2)"""
    counts = collections.Counter(pairs)
    n = len(pairs)
    a = sum(p / 2 for p in pairs) / n
    var = sum(c * (p / 2 - a) ** 2 for p, c in counts.items()) / n
    elo = lambda x: -400 * math.log10(1 / x - 1) if 0 < x < 1 else float("nan")  # noqa: E731
    hw = 1.96 * math.sqrt(var / n)
    return elo(a), (elo(min(a + hw, 0.9999)) - elo(max(a - hw, 0.0001))) / 2, [counts.get(k, 0) for k in (0, .5, 1, 1.5, 2)]


cand = None
rows = []
for tags, mt in games:
    if "GameDuration" not in tags or tags.get("Result") not in ("1-0", "0-1", "1/2-1/2"):
        continue
    if cand is None:
        cand = tags["White"]
    rows.append((tags, plies_of(mt)))
print(f"{len(rows)} games read from {path}; candidate = {cand}")
base_durs = [dur(t["GameDuration"]) for t, _ in rows]
print(f"played: mean game {statistics.mean(base_durs):.2f} s")


def pairs_from(results):
    by_round = collections.defaultdict(list)
    for (tags, _), res in zip(rows, results):
        by_round[tags.get("Round")].append(score_of(res, tags["White"] == cand))
    return [sum(v) for v in by_round.values() if len(v) == 2]


played = [t["Result"] for t, _ in rows]
e0, h0, p0 = penta_elo(pairs_from(played))
print(f"played results: Elo {e0:+.2f} +- {h0:.2f}, ptnml {p0}")
for name, rule in RULES.items():
    results, durs, adjud, changed = [], [], 0, 0
    for (tags, pl), d in zip(rows, base_durs):
        a = adjudicate(pl, rule)
        if a is None:
            results.append(tags["Result"])
            durs.append(d)
            continue
        i, res = a
        adjud += 1
        changed += res != tags["Result"]
        cut = sum(t for _, t in pl[i + 1:])
        durs.append(max(d - cut, 0.0))
        results.append(res)
    e, h, p = penta_elo(pairs_from(results))
    m_old, m_new = statistics.mean(base_durs), statistics.mean(durs)
    proj = f", projected {rate * m_old / m_new:.0f} games/h (from {rate:.0f})" if rate else ""
    print(f"{name}: adjudicated {100 * adjud / len(rows):.1f}%, result changed {changed} ({100 * changed / len(rows):.2f}%), "
          f"mean game {m_new:.2f} s ({100 * (m_new / m_old - 1):+.1f}%), throughput x{m_old / m_new:.3f}{proj}; "
          f"Elo {e:+.2f} +- {h:.2f} (played {e0:+.2f}), ptnml {p}")
