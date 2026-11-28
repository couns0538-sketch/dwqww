"""Rewrites the automatic rounds section of REPORT.md from the state file, between two marker lines per engine profile.
When a profile's marker lines are damaged (one missing or doubled, END before BEGIN, or its table there without markers),
REPORT.md keeps its text and gets one notice line at its top, the table goes to the side file REPORT.AUTO-ROUNDS-<name>.md,
and one WARNING is logged when the damage first shows or changes. update() never raises: a failure is logged once."""
from __future__ import annotations

from pathlib import Path

from .common import atomic_write_text, log, now, free_gb


def _f(x, nd=5):
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _n(x):
    return "-" if x is None else f"{int(x):,}"


def build(cfg: dict, state: dict) -> str:
    name = cfg["engine"]["name"]
    lines = [f"### Rounds for engine profile `{name}` (written by the pipeline, {now()})", ""]
    best = state.get("best")
    if best:
        lines.append(f"Current best net: `{best.get('net')}` (from round {best.get('round')}, {best.get('label', '')}).")
    else:
        lines.append("No best net yet.")
    lines.append(f"Free disk now: {free_gb(cfg['paths']['root']):.0f} GB.")
    lines.append("")
    lines.append("| Round | Data source | Positions made | Kept by filter | Draws | Train: epochs x size | "
                 "Train loss first -> last | Val loss last | SPRT games | W-L-D | Elo +/- | LLR | SPRT result | Decision |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    times = ["", "| Round | Datagen | Filter | Train | SPRT | Positions/s made | Trainer positions/s | State |",
             "|---|---|---|---|---|---|---|---|"]
    for key in sorted(state.get("rounds", {}), key=int):
        rd = state["rounds"][key]
        st = rd.get("stages", {})

        def out(stage):
            return (st.get(stage) or {}).get("out") or {}

        def secs(stage):
            s = (st.get(stage) or {}).get("seconds")
            return "-" if s is None else f"{s / 60:.1f} min"

        dg, qc, tr, sp = out("datagen"), out("filter"), out("train"), out("sprt")
        epochs = "-"
        if tr:
            epochs = f"{tr.get('epochs_run')} x {_n(cfg['train'].get('epoch_size')) if tr.get('samples') else '-'}"
        wld = f"{sp.get('wins')}-{sp.get('losses')}-{sp.get('draws')}" if sp else "-"
        elo = "-"
        if sp:
            e = str(sp.get("elo"))
            if e in ("None", "inf", "-inf", "nan", "-nan"):
                # fastchess prints "inf" for a 100% or 0% score
                elo = ("all games won" if not sp.get("losses") and not sp.get("draws") else
                       "all games lost" if not sp.get("wins") and not sp.get("draws") else "not finite")
            else:
                elo = f"{e} +/- {sp.get('elo_err')}"
        verdict = {"H1": "H1 accepted (better)", "H0": "H0 accepted (not better)",
                   "none": "no verdict at game limit"}.get(sp.get("verdict"), "-") if sp else "-"
        decision = rd.get("decision", "-")
        lines.append(
            f"| {key} | {dg.get('backend', '-')} | {_n(dg.get('positions'))} | "
            f"{_n(qc.get('kept'))} ({qc.get('kept_pct', '-')}%) | {qc.get('draw_pct', '-')}% | {epochs} | "
            f"{_f(tr.get('train_loss_first'))} -> {_f(tr.get('train_loss_last'))} | {_f(tr.get('val_loss_last'))} | "
            f"{_n(sp.get('games'))} | {wld} | {elo} | {_f(sp.get('llr'), 2)} | {verdict} | {decision} |")
        state_txt = "finished" if rd.get("finished") else "in progress: " + ", ".join(
            f"{k}={v.get('status')}" for k, v in st.items() if v.get("status") != "done") or "in progress"
        times.append(f"| {key} | {secs('datagen')} | {secs('filter')} | {secs('train')} | {secs('sprt')} | "
                     f"{_f(dg.get('pos_per_s'), 0) if dg else '-'} | {_f(tr.get('pos_per_s'), 0) if tr else '-'} | {state_txt} |")
        tl = sp.get("time_losses") if sp else None
        if tl:
            times.append(f"|  | note: {tl} time-loss/timeout lines in the SPRT log of round {key} |  |  |  |  |  |  |")
    lines.extend(times)
    notes = state.get("history", [])[-12:]
    if notes:
        lines.append("")
        lines.append("Recent events:")
        lines.extend(f"- {n}" for n in notes)
    return "\n".join(lines) + "\n"


_said: set = set()   # warnings this process (one round) has logged: each is said once


def update(cfg: dict, state: dict) -> None:
    # target 62 (23 Nov): a report that cannot be written must never fail a round (run.py calls this 6 times a round)
    try:
        _update(cfg, state)
    except Exception as e:  # noqa: BLE001
        msg = f"WARNING: the rounds table could not be written: {e!r}"
        if msg not in _said:
            _said.add(msg)
            log(msg)


def _update(cfg: dict, state: dict) -> None:
    path = Path(cfg["paths"]["report"])
    name = cfg["engine"]["name"]
    begin, end = f"<!-- AUTO-ROUNDS-{name}-BEGIN -->", f"<!-- AUTO-ROUNDS-{name}-END -->"
    side = path.with_name(f"{path.stem}.AUTO-ROUNDS-{name}.md")
    notice = (f"> NOTE written by the loop: the rounds table of profile `{name}` is not updated in this file while its "
              f"marker lines are damaged; until they are repaired by hand it is written to {side.name}.")
    damaged_head = f"<!-- written by the loop while the marker lines of profile `{name}` in {path.name} are damaged: "
    body = build(cfg, state)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = "# REPORT\n"
    block = f"{begin}\n{body}{end}"
    lines = text.split("\n")
    ib = [k for k, ln in enumerate(lines) if ln.strip() == begin]   # whole marker lines only: a quoted marker is text
    ie = [k for k, ln in enumerate(lines) if ln.strip() == end]
    stray = any(ln.startswith(f"### Rounds for engine profile `{name}`") for ln in lines)
    if len(ib) == 1 and len(ie) == 1 and ib[0] < ie[0]:
        lines[ib[0]:ie[0] + 1] = block.split("\n")
        text = "\n".join(lines)
    elif not ib and not ie and not stray:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    else:
        # Damaged: a rewrite around damaged markers can eat hand-written text (after an orphan BEGIN) or repeat it
        # (after an orphan END). So REPORT.md keeps its text (one notice line at its top says where the table is), the
        # table goes to the side file, and the warning is logged when the damage first shows or changes.
        what = ("no marker lines, but a rounds table of this profile is in the text (markers deleted by hand?)"
                if not ib and not ie else "the END line comes before the BEGIN line" if len(ib) == len(ie) == 1
                else f"{len(ib)} BEGIN and {len(ie)} END marker lines (one of each, BEGIN first, is needed)")
        head = damaged_head + what + " -->"
        try:
            known = side.read_text(encoding="utf-8").split("\n", 1)[0] == head
        except FileNotFoundError:
            known = False
        if not known:
            log(f"WARNING: {path}: {what}; it keeps its text, and the rounds table of profile {name} is written to "
                f"{side} until the marker lines are repaired by hand")
        atomic_write_text(side, head + "\n" + block + "\n")
        if notice not in lines:
            atomic_write_text(path, notice + "\n\n" + text)
        return
    if notice in lines:   # repaired: the notice goes, and the side file says it is no longer updated
        text = text[len(notice) + 2:] if text.startswith(notice + "\n\n") else "\n".join(
            ln for ln in text.split("\n") if ln != notice)
    atomic_write_text(path, text)
    try:
        first, rest = side.read_text(encoding="utf-8").split("\n", 1)
    except (FileNotFoundError, ValueError):
        return
    if first.startswith(damaged_head):
        atomic_write_text(side, f"<!-- NO LONGER UPDATED since {now()}: the marker lines of profile `{name}` in "
                                f"{path.name} are repaired and the table is written there again -->\n" + rest)
        log(f"the marker lines of profile {name} in {path} are repaired: the rounds table is written there again; "
            f"{side} is marked as no longer updated")
