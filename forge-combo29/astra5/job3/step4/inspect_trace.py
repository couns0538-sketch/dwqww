"""Summarize actual call returns and candidate-move decisions at one root iteration."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path

def load(source):
    visits = {}
    for line in source.read_text().splitlines():
        if not line.startswith("AS3TRACE "):
            raise ValueError(line)
        fields = dict(item.split("=", 1) for item in line.split()[1:])
        ident = int(fields["id"])
        event = fields.pop("event")
        if event == "enter":
            if ident in visits:
                raise ValueError(f"duplicate entry: {ident}")
            visits[ident] = {"entry": fields, "events": []}
        elif event == "return":
            if "return" in visits[ident]:
                raise ValueError(f"duplicate return: {ident}")
            visits[ident]["return"] = fields
        else:
            visits[ident]["events"].append((event, fields))
    if not visits or any("return" not in v for v in visits.values()):
        raise ValueError(f"{source}: missing call or unmatched enter/return")
    return visits

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("iteration", type=int)
    args = p.parse_args()
    visits = load(args.source)
    local = [(i, v) for i, v in visits.items() if int(v["entry"]["iteration"]) == args.iteration]
    print(f"{args.source.name}: {len(visits)} balanced calls in all iterations; "
          f"{len(local)} from iteration {args.iteration}")
    counts = defaultdict(Counter)
    for i, v in local:
        e, ret = v['entry'], v['return']
        counts[e['path'],e['kind']][ret['reason']] += 1
        events = " ".join(f"{event}({data.get('move', '-')},{data.get('value','-')})"
                          for event, data in v['events'] if event != "tt")
        print(f"#{i} {e['path']} {e['kind']} depth={e['depth']} w=[{e['alpha']},{e['beta']}] "
              f"static={ret['search_static']} raw={e['raw_static']} -> {ret['reason']}={ret['score']}; {events}")
    print("return-reason totals by path and kind")
    for (path, kind), reasons in sorted(counts.items()):
        print(path, kind, " ".join(f"{r}={c}" for r,c in sorted(reasons.items())))

if __name__ == "__main__":
    main()
