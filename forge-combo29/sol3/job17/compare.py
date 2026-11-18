import argparse
import csv


FIELDS = ('requested_depth', 'info_depth', 'bestmove', 'score_type', 'score', 'nodes')


def read_rows(path):
    with open(path, encoding='ascii', newline='') as table:
        rows = list(csv.DictReader(table, delimiter='\t'))
    if [int(row['requested_depth']) for row in rows] != list(range(1, 21)):
        raise ValueError(f'expected all 20 ordered requests in {path}')
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('reference')
    parser.add_argument('candidate')
    args = parser.parse_args()
    reference = read_rows(args.reference)
    candidate = read_rows(args.candidate)
    differences = [depth for depth, (a, b) in enumerate(zip(reference, candidate), 1)
                   if any(a[field] != b[field] for field in FIELDS)]
    print('comparison fields:', ', '.join(FIELDS))
    print('reference', args.reference)
    print('candidate', args.candidate)
    print(f'matching rows {20 - len(differences)}/20')
    if differences:
        first = differences[0]
        for name, row in [('reference', reference[first - 1]), ('candidate', candidate[first - 1])]:
            print(name, *(row[field] for field in FIELDS))
            print(row.get('last_info', row.get('info', '')))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
