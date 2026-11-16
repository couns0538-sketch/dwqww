# seat 20 — check of seat 02's S-F1 (the engine reads no command-line arguments)

Verdict: **CONFIRMS seat 02's S-F1.**

Raw: `out_check.txt` (the pasted run), `check_s02f1.sh` (the script that produced it).
Build: `/agent/repos/build-base/forge` sha256 `e06310ec…` (4/4 pins, `../HONESTY.txt`).

## The measurements

| command | stdout bytes | exit | verdict |
|---|---|---|---|
| `./forge` (no args, stdin /dev/null) | 0 | 0 | silent |
| `./forge bench` | **0** | 0 | argv ignored |
| `./forge bench 13` | **0** | 0 | argv ignored |
| `./forge --help` | **0** | 0 | argv ignored |
| `./forge uci` | **0** | 0 | argv ignored |
| `./forge zzzz` | **0** | 0 | argv ignored |
| `./forge bench 13` with `uci\nquit` on stdin | 4933 | 0 | the argument changes nothing |
| `printf 'bench 13\nquit\n' \| ./forge` | 61 | 0 | `info string bench depth 13 nodes 862329 time 435 …` |

No case hung; every exit is 0.

## The source, quoted
`src/uci.cpp:651-653` (6b98f217):
```
int main() {
    return forge::uci_loop(std::cin);
}
```
`argv` is not a parameter of main and not used anywhere in the entry point, so there is nothing to parse.

## Why this matters to the swarm
Every harness in this project drives the engine over stdin, so no wrong measurement follows *for us*. The hazard
is a future harness (or a person) writing `./forge bench 13` and reading 0 bytes as "the engine crashed" or, worse,
as "bench gives no nodes". It also means **a harness that passes options on the command line silently measures
the engine at DEFAULT settings** — that is the dangerous form: no error, just different numbers.

## Where my predictions went
All five held. Prediction 1's kill condition (any bytes on argv) never fired; prediction 4 was the interesting one —
the argument is completely inert even when a real session runs on stdin, which is what proves "ignores argv"
rather than "argv changes the mode".

## Commands that show it again
```
bash check_s02f1.sh /agent/repos/build-base/forge /tmp/o
./forge bench 13 </dev/null | wc -c                 # 0
printf 'bench 13\nquit\n' | ./forge | grep 'bench depth'   # 862329
sed -n '651,653p' /agent/repos/base/forge-combo29/src/uci.cpp
```
