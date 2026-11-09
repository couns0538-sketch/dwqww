#!/usr/bin/env python3
"""mutate_one.py <file> <old text> <new text> - one literal replacement for a test mutant; the old text must occur exactly once, or nothing is written and the exit code is 1."""
import sys


def main():
    path, old, new = sys.argv[1:4]
    text = open(path, encoding='utf-8', newline='').read()
    n = text.count(old)
    if n != 1:
        print(f'{path}: old text found {n} times, want 1: {old}')
        return 1
    open(path, 'w', encoding='utf-8', newline='').write(text.replace(old, new))
    print(f'{path}: mutated')
    return 0


if __name__ == '__main__':
    sys.exit(main())
