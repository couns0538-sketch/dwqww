"""Check Job 29 report fields and every local Markdown link against report evidence."""
from csv import DictReader
from hashlib import sha256
from pathlib import Path
import argparse,json,re
from urllib.parse import unquote,urlsplit

def check_report(doc,forge,job,footer_path):
    seen=doc.read_text().split('```')[::2];content='\n'.join(seen)
    links=re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)',content)
    require=lambda test,detail: None if test else (_ for _ in ()).throw(ValueError(detail))
    require(links,'expected evidence links')
    if doc.name=='REPORT_astra5_job29.md':
        inventory_marker='$ git status --short && ls -R forge-combo29/astra5/job29'
        require(inventory_marker in doc.read_text(),'missing closing working tree/inventory command')
        tail=doc.read_text().split(inventory_marker,1)[1]
        for name in ('forge-combo29/astra5/job29:', 'forge-combo29/astra5/job29/audit/final:',
                     'forge-combo29/astra5/job29/part1/8000:', 'forge-combo29/astra5/job29/thresholds:'):
            require(name in tail,('missing inventory directory',name))
    for link in links:
        u=urlsplit(link)
        if u.scheme:raise ValueError(f'expected local evidence: {link}')
        if not u.path:continue
        p=(forge/unquote(u.path)).resolve()
        require(p.is_relative_to(forge.resolve()) and p.is_file(),f'missing/outside evidence: {link}')
    whole=json.loads((job/'audit/final/independent.json').read_text())
    verdict=whole['E_line']
    require('**'+verdict+'**' in content,'E verdict')
    fields=[l.strip('|').split('|') for l in content.splitlines() if l.startswith('|') and l.endswith('|')]
    vals=[tuple(x.strip() for x in row) for row in fields]
    arms=[(k,v) for k,v in whole['arms'].items() if v['pairs']]
    for arm,v in arms:
        elo,lo,hi=v['elo_lower_upper'];a,b=v['players']['A'],v['players']['B']
        scores=[r for r in vals if r[0]==arm and len(r)>10]
        require(len(scores)==1,('match row',arm))
        s=scores[0]
        require(s[2]==str(v['pairs']) and tuple(map(int,s[3].split('–')))==tuple(v['A_WLD']) and
                tuple(map(int,s[4].split('/')))==tuple(v['penta']) and f"{a['mean_n']:,.2f}" in s[5] and
                s[6]==f"{b['mean_n']:,.2f}" and s[7]==f"{v['nodes_ratio']:.4f}" and s[8]==f'{elo:+.2f}' and
                s[9]==f'[{lo:+.2f}, {hi:+.2f}]' and s[10]==v['reading'],(arm,s))
        for side in 'AB':
            p=v['players'][side];r=next(x for x in vals if x[:2]==(arm,side))
            cap='—' if arm=='E' and side=='A' else f"{p['hardcap']:,} ({p['hardcap_share']:.2%})"
            require(r[2:]==(p['go'],f"{p['searches']:,}",f"{p['mean_n']:,.2f}",f"{p['mean_depth']:.3f}",cap,f"{p['no_score']:,}"),(arm,side,r))
        want=(arm,f"{v['mean_plies']:.2f}",*[str(v['endings'].get(end,0)) for end in ('checkmate','stalemate','insufficient','threefold','fifty','cap')])
        require(want in vals,('ending table',arm))
    with (job/'thresholds/summary.tsv').open() as f:
        threshold_rows=list(DictReader(f,delimiter='\t'))
    for q in threshold_rows:
        mean=q['mean_plies_remaining']
        row=(f"{int(q['threshold_cp']):,}",q['match'],q['side'],q['games_reached'],q['won'],q['drew'],q['lost'],f'{float(mean):.2f}' if mean else '—')
        require(row in vals,('threshold',row))
    bands={'all':'All','1-40':'1–40','41-80':'41–80','81+':'81 and later'}
    for k,v in whole['pooled_2000'].items():
        require((bands[k],f"{v['searches']:,}",f"{v['n_total']:,}",f"{v['mean_n']:,.2f}") in vals,('pooled',k))
    with footer_path.open() as f:
        fixed=next(DictReader(f,delimiter='\t'))
    require(f"{float(fixed['footer_mean']):,.2f}" in content and f"{int(fixed['footer_under_4000']):,}" in content and
            f"{int(fixed['footer_eq_4000']):,}" in content, 'fixed footer actual')
    with (job/'part1/table.tsv').open() as f:
        for q in DictReader(f,delimiter='\t'):
            require(q['row_sha16'] in content,('Part 1 signature',q['limit']))
    for gate in ('K29','C29'):
        data=(job/'controls'/gate/'comparison.tsv').read_text()
        for digest in set(re.findall(r'\b[0-9a-f]{16}\b',data)):require(digest in content,('control',digest))
    for section in ('## 1.', '## 2.', '## 3.', '## 4.', '## 5.', '## Facts','## Suspicions','## What I did not do','## What I am not sure about'):
        require(section in content,section)
    return (f"Verified all {len(links)} Markdown links ({len(set(links))} distinct paths), including all score/spend/threshold inputs.\n"
            f"Verified {len(arms)} reporting rows, {len(arms)*2} side rows, {len(arms)} endings rows, "
            f"{len(threshold_rows)} thresholds, all 4 pooled softnodes-2000 rows, "
            f"five Part 1 signatures, all K29 and C29 known-answer signatures, E's named reading and its actual footer mean.\n"
            f"Source SHA256 {sha256(doc.read_bytes()).hexdigest()}.\n")

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('report','forge_tree','job29_evidence','plain_footer','output'):p.add_argument(key,type=Path)
    a=p.parse_args();summary=check_report(a.report,a.forge_tree,a.job29_evidence,a.plain_footer)
    a.output.write_text(summary);print(summary,end='')
