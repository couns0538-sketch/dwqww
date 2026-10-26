"""Original stdlib-only descriptive PGN outcome miner, not a legality proof.

Pairing is explicit: ``same-round`` groups identical Round values (Forge runner
contract); ``adjacent-rounds`` groups decimal rounds (2n-1, 2n);
``round-prefix`` groups N.1/N.2. No pairing policy is inferred. Settings are
partitioned before pairing. Scores use candidate half-point units 0/1/2.
All games, including malformed or unfinished records, remain in ``games``.
Missing FEN/OpeningFEN means unknown opening; missing Termination means unknown
fault status. ``aggregate_eligible`` is a data-quality screen, never match
acceptance, a legality claim, or an SPRT decision.

Opening FEN validation checks syntax only (four or six fields); no board
legality or move legality is implied. The bounded supported identity tags are
listed in ``supported_identity_tags`` in each report. They cover explicit run
identities and common fastchess option/configuration labels. Arbitrary unknown
tags are preserved, not authenticated as settings. Date is deliberately not
an identity tag: an overnight match can span dates without changing settings.
"""
import re
from collections import Counter, defaultdict


_RESULTS = {"1-0", "0-1", "1/2-1/2", "*"}
_META = ("Event", "Site", "TimeControl", "Threads", "Hash", "Concurrency", "Seed", "Gate",
         "Match", "Run", "Attempt", "Srand", "Variant", "Options", "EngineOptions",
         "WhiteOptions", "BlackOptions", "WhiteEngineOptions", "BlackEngineOptions",
         "WhiteOption", "BlackOption", "WhiteConfig", "BlackConfig", "CandidateOptions", "BaselineOptions",
         "Ponder", "OwnBook", "Book", "BookFile", "BookFormat", "BookOrder", "BookDepth", "BookPlies",
         "OpeningFile", "OpeningSuite", "OpeningSeed", "OpeningPly", "UCI_Chess960", "UCI_LimitStrength",
         "UCI_Elo", "SkillLevel", "SyzygyPath", "SyzygyProbeDepth", "SyzygyProbeLimit", "MoveOverhead",
         "Adjudication", "Resign", "Draw", "Tablebase", "TbPieces", "Timemargin", "TimeMargin",
         "Restart", "Protocol")
_BINS = ("WW", "WD", "WL", "DD", "LD", "LL")
_TAG = re.compile(r'\[([A-Za-z0-9_]+)\s+"((?:\\["\\]|[^"\\])*)"\s*\]\Z')
_FAULTS = {
    "time_loss": re.compile(r"\b(?:time forfeit|time loss|los(?:es|t) on time|time limit|timeout|timed out)\b", re.I),
    "crash": re.compile(r"\b(?:crash(?:ed)?|disconnect(?:ed|ion)?|connection stall)\b", re.I),
    "illegal": re.compile(r"\billegal(?: move)?\b", re.I),
}


def _tokens(text):
    """Scan PGN syntax without mistaking comments/RAVs for mainline results."""
    i, length = 0, len(text)
    while i < length:
        ch = text[i]
        if ch.isspace() or ch == "\ufeff":
            i += 1
        elif ch == "%" and (i == 0 or text[i - 1] in "\r\n"):
            end = text.find("\n", i)
            i = length if end < 0 else end + 1
        elif ch == "{":
            end = text.find("}", i + 1)
            if end < 0:
                yield "comment", text[i + 1:]
                yield "error", "unclosed_comment"
                return
            yield "comment", text[i + 1:end]
            i = end + 1
        elif ch == ";":
            end = text.find("\n", i + 1)
            if end < 0:
                end = length
            yield "comment", text[i + 1:end]
            i = end
        elif ch in "()":
            yield ch, ch
            i += 1
        elif ch == "[":
            j, quoted, escaped = i + 1, False, False
            while j < length:
                c = text[j]
                if c in "\r\n":
                    break
                if escaped:
                    escaped = False
                elif c == "\\" and quoted:
                    escaped = True
                elif c == '"':
                    quoted = not quoted
                elif c == "]" and not quoted:
                    j += 1
                    break
                j += 1
            raw = text[i:j]
            match = _TAG.fullmatch(raw)
            if match:
                value = re.sub(r'\\(["\\])', r'\1', match.group(2))
                yield "tag", (match.group(1), value)
            else:
                yield "bad_tag", raw
            i = j if j > i else i + 1
        else:
            j = i
            while j < length and not text[j].isspace() and text[j] not in "{}();[]":
                j += 1
            if j == i:
                yield "error", "unexpected_delimiter"
                i += 1
            else:
                yield "word", text[i:j]
                i = j


def _parse(text):
    records = []
    tags, issues, results, comments = {}, [], [], []
    body, depth = False, 0

    def finish():
        if tags or issues or body or comments:
            final_issues = list(issues)
            if depth:
                final_issues.append("unclosed_variation")
            records.append({"tags": dict(tags), "issues": final_issues,
                            "results": list(results), "comments": list(comments)})

    for kind, value in _tokens(text):
        if kind in ("tag", "bad_tag"):
            if body:
                finish()
                tags, issues, results, comments = {}, [], [], []
                body, depth = False, 0
            if kind == "bad_tag":
                issues.append("malformed_tag")
            else:
                name, tag_value = value
                if name in tags:
                    issues.append("duplicate_tag:" + name)
                else:
                    tags[name] = tag_value
        elif kind == "comment":
            comments.append({"text": value, "variation_depth": depth})
        elif kind == "error":
            issues.append(value)
        elif kind == "(":
            body = True
            depth += 1
        elif kind == ")":
            body = True
            if depth:
                depth -= 1
            else:
                issues.append("unmatched_variation_close")
        else:
            body = True
            if not depth:
                if value in _RESULTS:
                    results.append(value)
                elif results:
                    issues.append("movetext_after_result")
    finish()
    return records


def _fen_syntax(fields):
    """Validate FEN field spelling and rank widths, without legality checks."""
    if len(fields) not in (4, 6):
        return False
    ranks = fields[0].split("/")
    if len(ranks) != 8:
        return False
    for rank in ranks:
        width = 0
        for char in rank:
            if char in "pnbrqkPNBRQK":
                width += 1
            elif char in "12345678":
                width += int(char)
            else:
                return False
        if width != 8:
            return False
    if fields[1] not in ("w", "b"):
        return False
    castling = fields[2]
    if castling != "-" and (not re.fullmatch(r"[KQkq]+", castling) or len(set(castling)) != len(castling)):
        return False
    if not re.fullmatch(r"(?:-|[a-h][36])", fields[3]):
        return False
    if len(fields) == 6:
        if not re.fullmatch(r"[0-9]+", fields[4]) or not re.fullmatch(r"[0-9]+", fields[5]):
            return False
        if int(fields[5]) < 1:
            return False
    return True


def _opening(tags, issues):
    keys = []
    for name in ("FEN", "OpeningFEN"):
        if name in tags:
            fields = tags[name].split()
            if not _fen_syntax(fields):
                issues.append("invalid_opening_fen")
                return None
            keys.append(" ".join(fields[:4]))
    if len(set(keys)) > 1:
        issues.append("conflicting_opening_fen")
        return None
    return keys[0] if keys else None


def _attribute(text, candidate, baseline, color, result):
    mentions = []
    for identity, name in (("candidate", candidate), ("baseline", baseline)):
        if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text, re.I):
            mentions.append(identity)
    for side in ("white", "black"):
        if re.search(r"\b" + side + r"\b", text, re.I) and color:
            mentions.append("candidate" if side == color else "baseline")
    if len(set(mentions)) == 1:
        return mentions[0], "explicit"
    if mentions:
        return "unknown", "ambiguous"
    if result in ("1-0", "0-1") and color:
        loser = "black" if result == "1-0" else "white"
        return ("candidate" if loser == color else "baseline"), "result_loser"
    return "unknown", "unknown"


def _game(record, index, candidate, baseline, phase_tag):
    tags, issues = record["tags"], list(record["issues"])
    header = tags.get("Result")
    results = record["results"]
    mainline = results[-1] if results else None
    result_trusted = True
    if header not in _RESULTS:
        issues.append("missing_or_invalid_header_result")
        result_trusted = False
    if not results:
        issues.append("missing_mainline_result")
        result_trusted = False
    if len(results) > 1:
        issues.append("multiple_mainline_results")
        result_trusted = False
    if header in _RESULTS and mainline is not None and header != mainline:
        issues.append("result_mismatch")
        result_trusted = False
    white, black = tags.get("White"), tags.get("Black")
    color = None
    if white == candidate and black == baseline:
        color = "white"
    elif black == candidate and white == baseline:
        color = "black"
    else:
        issues.append("engine_names_mismatch")
    score = None
    if result_trusted and color and mainline != "*":
        score = 1 if mainline == "1/2-1/2" else (2 if (mainline == "1-0") == (color == "white") else 0)
    outcome = {0: "L", 1: "D", 2: "W"}.get(score, "unknown")
    opening_key = _opening(tags, issues)
    termination = tags.get("Termination")
    if termination is not None and (not termination.strip() or termination.strip() in ("?", "*", "unknown")):
        termination = None
    sources = []
    if termination:
        sources.append(("Termination", termination))
    sources.extend(("comment", comment["text"]) for comment in record["comments"] if comment["variation_depth"] == 0)
    faults = []
    # A game/kind is counted once even if the runner repeats its explanation.
    for kind, pattern in _FAULTS.items():
        evidence = []
        for source, source_text in sources:
            for clause in re.split(r"[;\n]", source_text):
                match = pattern.search(clause)
                if match:
                    attribution, basis = _attribute(clause, candidate, baseline, color,
                                                    mainline if result_trusted else None)
                    evidence.append({"kind": kind, "attribution": attribution,
                                     "attribution_basis": basis, "source": source,
                                     "text": clause.strip()})
        if evidence:
            explicit = [fault for fault in evidence if fault["attribution_basis"] == "explicit"]
            identities = {fault["attribution"] for fault in explicit}
            fault = dict((explicit or evidence)[0])
            if len(identities) > 1:
                fault["attribution"], fault["attribution_basis"] = "unknown", "ambiguous"
            faults.append(fault)
    phase = tags.get(phase_tag)
    termination_status = ("unknown" if termination is None else "reported_fault" if faults else
                          "normal" if termination and termination.strip().casefold() == "normal" else "unknown")
    return {"index": index, "tags": tags, "header_result": header,
            "mainline_result": mainline, "result": mainline if result_trusted else None,
            "score": score, "outcome": outcome, "candidate_color": color,
            "phase": phase if phase and phase not in ("?", "*") else "unknown",
            "opening_key": opening_key, "termination": termination, "termination_status": termination_status,
            "faults": faults, "comment_observations": record["comments"],
            "issues": list(dict.fromkeys(issues))}


def _raw(games):
    outcomes = Counter(game["outcome"] for game in games)
    faults = {key: 0 for key in ("total", "time_loss", "crash", "illegal", "candidate", "baseline", "unknown")}
    for game in games:
        for fault in game["faults"]:
            faults["total"] += 1
            faults[fault["kind"]] += 1
            faults[fault["attribution"]] += 1
    unknown = sum(game["termination_status"] == "unknown" for game in games)
    return {"games": len(games), **{key: outcomes[key] for key in ("W", "D", "L", "unknown")},
            "terminations": dict(Counter(game["termination"] or "unknown" for game in games)),
            "termination_unknown": unknown, "faults": faults,
            "fault_status": "observed_faults" if faults["total"] else ("unknown" if unknown else "no_reported_faults")}


def _round_key(game, pairing):
    value = game["tags"].get("Round")
    if not value or value in ("?", "*"):
        return "missing:%d" % game["index"], "missing_round"
    if pairing == "same-round":
        return value, None
    if pairing == "adjacent-rounds":
        if not re.fullmatch(r"[1-9][0-9]*", value):
            return "invalid:%d" % game["index"], "invalid_adjacent_round"
        return str((int(value) + 1) // 2), None
    match = re.fullmatch(r"([1-9][0-9]*)\.([12])", value)
    if not match:
        return "invalid:%d" % game["index"], "invalid_round_prefix"
    return match.group(1), None


def _pair(key, games, pairing, round_issues):
    issues = list(round_issues)
    if len(games) != 2:
        issues.append("pair_game_count")
    if any(game["issues"] for game in games):
        issues.append("game_record_issues")
    if any(game["score"] is None for game in games):
        issues.append("unknown_score")
    opening_keys = {game["opening_key"] for game in games}
    if None in opening_keys:
        issues.append("opening_unknown")
    if len(opening_keys) > 1:
        issues.append("opening_mismatch")
    if len(games) == 2:
        if {game["candidate_color"] for game in games} != {"white", "black"}:
            issues.append("colors_not_swapped")
        rounds = [game["tags"].get("Round") for game in games]
        if pairing == "adjacent-rounds" and len(set(rounds)) != 2:
            issues.append("duplicate_round")
        if pairing == "round-prefix" and {value.rsplit(".", 1)[-1] for value in rounds if value} != {"1", "2"}:
            issues.append("round_prefix_members")
    phases = {game["phase"] for game in games}
    phase = next(iter(phases)) if len(phases) == 1 else None
    fault_count = sum(len(game["faults"]) for game in games)
    valid = not issues
    score_sum = sum(game["score"] for game in games) if valid else None
    outcomes = sorted((game["outcome"] for game in games), key=lambda outcome: {"W": 0, "D": 1, "L": 2, "unknown": 3}[outcome])
    # Requested spelling LD denotes one loss and one draw.
    six_bin = ("LD" if outcomes == ["D", "L"] else "".join(outcomes)) if valid else None
    normal_termination = all(game["termination_status"] == "normal" for game in games)
    eligible = valid and not fault_count and normal_termination
    return {"key": key, "games": [game["index"] for game in games], "valid": valid,
            "eligible": eligible, "opening_known": None not in opening_keys,
            "opening_key": next(iter(opening_keys)) if len(opening_keys) == 1 else None,
            "phase": phase, "phase_status": "same" if phase is not None else "mixed",
            "score_sum": score_sum, "bin": six_bin, "pentabin": score_sum,
            "fault_count": fault_count, "issues": list(dict.fromkeys(issues)),
            "eligibility_issues": (["reported_faults"] if fault_count else []) +
                                  (["unknown_or_abnormal_termination"] if not normal_termination else [])}


def _paired(pairs, *, allow_aggregate=True):
    bins, pentabins = dict.fromkeys(_BINS, 0), [0] * 5
    for pair in pairs:
        if pair["valid"]:
            bins[pair["bin"]] += 1
            pentabins[pair["pentabin"]] += 1
    eligible = sum(pair["eligible"] for pair in pairs)
    return {"valid_pairs": sum(pair["valid"] for pair in pairs), "eligible_pairs": eligible,
            "invalid_pairs": sum(not pair["valid"] for pair in pairs),
            "six_bins": bins if allow_aggregate else None,
            "pentabins": pentabins if allow_aggregate else None,
            "fault_count": sum(pair["fault_count"] for pair in pairs),
            "aggregate_eligible": bool(pairs) and allow_aggregate and eligible == len(pairs)}


def _breakdown(games, pairs, field, allow_aggregate):
    buckets = {}
    for game in games:
        key = game[field] if game[field] is not None else "unknown"
        buckets.setdefault(key, {"games_list": [], "pairs_list": []})["games_list"].append(game)
    for pair in pairs:
        key = pair[field]
        # Mixed-phase outcomes cannot be assigned to any component phase.
        if key is not None:
            buckets.setdefault(key, {"games_list": [], "pairs_list": []})["pairs_list"].append(pair)
    return {key: {**_raw(value["games_list"]), "paired": _paired(value["pairs_list"], allow_aggregate=allow_aggregate)}
            for key, value in buckets.items()}


def mine_pgn(text, candidate, baseline, *, pairing="same-round", phase_tag="Phase"):
    """Return JSON-safe descriptive game/pair records; invalid arguments raise ValueError.

    ``raw`` never discards games. Untrusted/missing/conflicting results have
    unknown score. Structurally valid faulted pairs contribute descriptive bins
    but never eligibility. Repeated opening pairs are flagged and ineligible.
    Multiple metadata pools expose no global penta/six-bin aggregate.
    """
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if any(not isinstance(name, str) or not name or name != name.strip() for name in (candidate, baseline)) or candidate == baseline:
        raise ValueError("candidate and baseline must be distinct nonempty exact engine names")
    if pairing not in ("same-round", "adjacent-rounds", "round-prefix"):
        raise ValueError("unknown explicit pairing policy")
    if not isinstance(phase_tag, str) or not re.fullmatch(r"[A-Za-z0-9_]+", phase_tag):
        raise ValueError("phase_tag must be an explicit PGN tag name")
    games = [_game(record, index, candidate, baseline, phase_tag)
             for index, record in enumerate(_parse(text), 1)]
    pool_groups = {}
    for game in games:
        identity = tuple(game["tags"].get(name) for name in _META)
        pool_groups.setdefault(identity, []).append(game)
    issues, pools, all_pairs = [], [], []
    if len(pool_groups) > 1:
        varied = [name for index, name in enumerate(_META) if len({identity[index] for identity in pool_groups}) > 1]
        issues.append({"code": "metadata_variation", "fields": varied,
                       "message": "Settings identities are separate pools; global paired bins are blocked."})
    for pool_index, (identity, pool_games) in enumerate(pool_groups.items(), 1):
        pool_id = "pool-%d" % pool_index
        groups, group_issues = defaultdict(list), defaultdict(list)
        for game in pool_games:
            game["pool_id"] = pool_id
            key, round_issue = _round_key(game, pairing)
            groups[key].append(game)
            if round_issue:
                group_issues[key].append(round_issue)
        pairs = [_pair(key, grouped, pairing, group_issues[key]) for key, grouped in groups.items()]
        repeated = defaultdict(list)
        for pair in pairs:
            pair["pool_id"] = pool_id
            if pair["valid"] and pair["opening_key"] is not None:
                repeated[pair["opening_key"]].append(pair)
        for opening, opening_pairs in repeated.items():
            if len(opening_pairs) > 1:
                issues.append({"code": "repeated_opening_pairs", "pool_id": pool_id,
                               "opening_key": opening, "pair_keys": [pair["key"] for pair in opening_pairs]})
                for pair in opening_pairs:
                    pair["issues"].append("repeated_opening_pairs")
                    pair["eligible"] = False
        pools.append({"id": pool_id, "metadata": dict(zip(_META, identity)),
                      "games": [game["index"] for game in pool_games], "raw": _raw(pool_games),
                      "pairs": pairs, "paired": _paired(pairs),
                      "per_opening": _breakdown(pool_games, pairs, "opening_key", True),
                      "per_phase": _breakdown(pool_games, pairs, "phase", True)})
        all_pairs.extend(pairs)
    for game in games:
        for issue in game["issues"]:
            issues.append({"code": issue, "game": game["index"]})
    for pair in all_pairs:
        for issue in pair["issues"]:
            if issue != "repeated_opening_pairs":
                issues.append({"code": issue, "pool_id": pair["pool_id"], "pair_key": pair["key"]})
    aggregate = len(pools) <= 1
    return {"schema": "forge-sol-s06-pgn-v1", "candidate": candidate, "baseline": baseline,
            "pairing": pairing, "phase_tag": phase_tag, "supported_identity_tags": list(_META),
            "games": games, "raw": _raw(games),
            "pairs": all_pairs, "paired": _paired(all_pairs, allow_aggregate=aggregate),
            "pools": pools, "per_opening": _breakdown(games, all_pairs, "opening_key", aggregate),
            "per_phase": _breakdown(games, all_pairs, "phase", aggregate), "issues": issues,
            "limitations": ["Descriptive PGN parsing only; no move legality proof.",
                            "FEN syntax checks do not establish board legality.",
                            "Identity partitioning uses only supported_identity_tags; arbitrary unknown tags are not authenticated settings.",
                            "Not a final acceptance decision or an SPRT result.",
                            "Missing Termination is unknown fault status; zero observed faults is not a guarantee."]}
