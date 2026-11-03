"""Render the measured QC result without changing any data or qualification."""
import argparse
import json
from pathlib import Path
from run_policy import Inputs, free_guard, safe_path

def render(source):
    inputs=Inputs()
    report=inputs.json(source)
    profiles=report['profiles']
    new,old=profiles['r14b'],profiles['old440k']
    lines=['# P5 relabel QC — R13','',
           f"QC integrity: **{report['status']}**. Authentic game separation: **UNVERIFIED**.",
           'No strength, training-readiness or improved-label-quality claim.','',
           '| Measure | R14-B jobA | Old R13 baseline |','|---|---:|---:|']
    for label,a,b in [('Rows',new['rows'],old['rows']),('Mate-range rows',new['mate_rows'],old['mate_rows']),
                       ('Mate-range percentage',100*new['mate_rows']/new['rows'],100*old['mate_rows']/old['rows']),
                       ('Mean STM score',new['score_stm']['mean'],old['score_stm']['mean']),
                       ('Mean White score',new['score_white']['mean'],old['score_white']['mean']),
                       ('Exact-FEN duplicate rows',report['duplicates']['r14b']['duplicate_rows'],report['duplicates']['old440k']['duplicate_rows']),
                       ('Exact-FEN duplicate rate',report['duplicates']['r14b']['duplicate_rate'],report['duplicates']['old440k']['duplicate_rate'])]:
        lines.append(f'| {label} | {a} | {b} |')
    if 'r14b:non_mate' in profiles and 'old440k:non_mate' in profiles:
        a,b=profiles['r14b:non_mate'],profiles['old440k:non_mate']
        for label,left,right in [('Non-mate rows',a['rows'],b['rows']),('Non-mate mean STM score',a['score_stm']['mean'],b['score_stm']['mean']),
                                 ('Non-mate paired mean absolute label delta',a['paired_old_score']['mean_absolute_delta'],b['paired_old_score']['mean_absolute_delta'])]:
            lines.append(f'| {label} | {left} | {right} |')
    lines+=['','## Score distribution','', 'Buckets are STM centipawns, lower-inclusive and upper-exclusive. Mate flagging is separately inclusive at abs(score) >= 30000.','',
            '| Bucket | R14-B rows | R14-B % | Old rows | Old % |','|---|---:|---:|---:|---:|']
    for key in sorted(set(new['score_stm']['histogram'])|set(old['score_stm']['histogram']),key=lambda k:float(k[1:].split(',')[0])):
        a,b=new['score_stm']['histogram'].get(key,0),old['score_stm']['histogram'].get(key,0)
        lines.append(f"| {key} | {a} | {100*a/new['rows']:.4f} | {b} | {100*b/old['rows']:.4f} |")
    for title,field in [('WDL, White perspective','wdl_white'),('WDL, side-to-move perspective','wdl_stm'),('Side to move','side_to_move'),('Piece count, including kings','piece_count'),('Material-phase proxy','phase_group')]:
        lines+=['',f'## {title}','','| Value | R14-B rows | R14-B % | Old rows | Old % |','|---|---:|---:|---:|---:|']
        for key in sorted(set(new[field])|set(old[field]),key=lambda k:(int(k) if str(k).isdecimal() else 0,str(k))):
            a,b=new[field].get(key,0),old[field].get(key,0)
            lines.append(f"| {key} | {a} | {100*a/new['rows']:.4f} | {b} | {100*b/old['rows']:.4f} |")
    lines+=['','## Interpretation and limits','',
            '- The cohorts are different populations. Cross-cohort differences are descriptive, not paired label changes.',
            '- R14-B paired old-score statistics compare each row only to its own original self-play score.',
            '- Old labels were searched with castling/EP removed and clocks reset. Their duplicate-FEN rate uses that lossy representation and is not directly comparable as original-state diversity.',
            '- The 440k baseline is the complete sealed prefix listed in its shards.tsv; its larger original relabel job is incomplete.',
            '- A separate corrected 1k P5 proof exists at D:/o14a/p5/job_fix1k. It is not pooled into either cohort, nor used to repair old labels.',
            '- R14-B IDs are inferred groups, not authentic original-game identifiers. No production game-separation PASS is claimed.',
            '- JobB is used only for final-label content-hash reproducibility, not counted as extra data.',
            '- Mate rows are flagged into a separate original-preserving file. No source score is clamped or rewritten.',
            '- Full per-split distributions, duplicate counts and paired-score deltas are in statistics.json.',
            '- Primary label/sidecar manifests are checked; historical probe logs and retained intermediate files are not reopened.',
            '', 'Material phase: '+report['phase_definition']+'.', '',
            '## Reproduction','',
            'Run `p5qc/reproduce.ps1 -RunName NEW_NAME` from the contained checkout. Existing run destinations are refused.',
            'Tests: full inherited datafilter suite plus `tests/`, via `tools/run_tests.py` and the reviewed launcher.',
            '',f"Measured audit duration: {report['seconds']:.3f} seconds.",
            f"Input result: `{source}`. Complete consumed-input SHA256/MD5 receipts: adjacent `INPUTS.json`.",
            'Final artifact checksums are in SHA256SUMS and MD5SUMS.']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--statistics',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    args=parser.parse_args()
    output=safe_path(args.output,write=True)
    text=render(args.statistics)
    free_guard(len(text.encode('utf-8'))+1024*1024)
    with output.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(text)
