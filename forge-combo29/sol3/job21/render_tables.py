import argparse
import json
from pathlib import Path


def numbers(value):
    return f'{value:,}'


def ratio(value):
    return '—' if value is None else f'{value:.2f}%'


def seconds(nanoseconds):
    return f'{nanoseconds / 1e9:.3f}'


def histogram(values):
    return ', '.join(f'D{depth} × {count}' for depth,count in values.items()) or '—'


def format_a(data):
    print('| Searches | Count | Final nodes | Last-info nodes | Nodes after last info | Share of final nodes | Wall seconds | Estimated tail seconds | Share of wall |')
    print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
    for key,label,metric in [('all','All','all'),('cap','Cap only','capped')]:
        row=data[key]
        print(f"| {label} | {numbers(row['searches'])} | {numbers(row['final_nodes'])} | "
              f"{numbers(row['last_info_nodes'])} | {numbers(row['excess_nodes'])} | "
              f"{ratio(data['excess_share_' + metric + '_nodes_pct'])} | {seconds(row['wall_ns'])} | "
              f"{seconds(data['wall_minus_last_info_on_cap_ns'])} | {ratio(data['estimated_tail_share_' + metric + '_wall_pct'])} |")


def format_b(data, label):
    print(f'| {label} | Searches all / cap | Final nodes all / cap | Tail nodes (% of group) | Go-to-bestmove seconds all / cap | Estimated tail seconds (% of group) |')
    print('| --- | ---: | ---: | ---: | ---: | ---: |')
    for name,row in data.items():
        all_rows,cap_rows=row['all'],row['cap']
        print(f"| {name} | {numbers(all_rows['searches'])} / {numbers(cap_rows['searches'])} | "
              f"{numbers(all_rows['final_nodes'])} / {numbers(cap_rows['final_nodes'])} | "
              f"{numbers(cap_rows['excess_nodes'])} ({ratio(row['excess_share_all_nodes_pct'])}) | "
              f"{seconds(all_rows['wall_ns'])} / {seconds(cap_rows['wall_ns'])} | "
              f"{seconds(row['wall_minus_last_info_on_cap_ns'])} ({ratio(row['estimated_tail_share_all_wall_pct'])}) |")


def format_c(data):
    print('| k | Capped tails skipped | Nodes saved, upper bound (% of all) | Completed iterations skipped | Depths lost | Skips with last completed nodes below 2,000 |')
    print('| ---: | ---: | ---: | ---: | --- | ---: |')
    for k,row in data['rows'].items():
        print(f"| {k} | {numbers(row['capped_searches_stopped'])} | {numbers(row['tail_nodes_upper_bound'])} "
              f"({ratio(row['share_all_nodes_upper_bound_pct'])}) | {numbers(row['false_stop_searches'])} | "
              f"{histogram(row['completed_depths_lost'])} | {numbers(row['false_stop_searches_literal_last_below_target'])} |")


def main():
    parser=argparse.ArgumentParser(description='Render Job 21 G1 tables from the offline analysis.')
    parser.add_argument('analysis',type=Path)
    parser.add_argument('table',choices=('A','B-pieces','B-depth','C'))
    args=parser.parse_args()
    data=json.loads(args.analysis.read_text())
    if args.table=='A':
        format_a(data['table_A'])
    elif args.table=='B-pieces':
        format_b(data['table_B_by_piece_count'],'Pieces on board')
    elif args.table=='B-depth':
        format_b(data['table_B_by_last_completed_depth'],'Last completed depth')
    else:
        format_c(data['table_C'])


if __name__=='__main__':
    main()
