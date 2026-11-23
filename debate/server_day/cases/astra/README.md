# Nine reproducible cases for the first server-day package

These fixtures use commit `a5c74106bb9174b3bb1d305550b838484b11f459`. Each starts from a private temporary directory and creates its own inputs. Run the commands from the repository root. For cases 8 and 9 replace `path/to/qualified/forge` with a native executable that passes this package's startup known answers. Cases 11 and 14–16 use python-chess in the invoking interpreter. Cases 8 and 9 use the actual published workload and net. Cases 10 and 12 isolate the UCI wait and converter return field. Case 16 has two small test-only adapters for the missing PC configuration and row formatter. Its two-row clean control must pass before the interruption.

Both runners accept `--work-dir PATH`. Each case creates and removes a unique child directory inside that parent. Existing files in the parent are preserved, and child processes inherit the case directory for temporary files. Choose an authorized local folder on the PC. Without this option, the system temporary folder is used.

Exit 0 means the acceptance condition held, 1 means the case exposed the stated failure, and 2 means the fixture could not run. The first package returned 1 in every case. These are rehearsal fixtures for Fable's regression tests. Each revised script and test still requires review at its own new digest. If the command-line or storage format changes, carry the same input events and acceptance conditions through the new public entry point.

| Case | Input and expected result | Observed on the first package |
|---|---|---|
| 8 | Finish oldrun game 1, then restart the same spool under newrun and another seed. Refuse before changing the old journal. | Exit 0, newrun game 2 appended. |
| 9 | Invoke the worker with its production cutoff a minute in the past. No startup search or game may run. | The depth-18 startup search completed and was journalled. No game completed. |
| 10 | A search has a 200 ms deadline. One stream has lines spaced 20 ms apart; the control uses 300 ms. Both must time out. | The 20 ms stream returned a bestmove at 800 ms. The 300 ms control timed out. This queue honors its timeout. Astra's earlier 300 ms progress example used a mock that ignored it. |
| 11 | The receiver sees a legal eight-ply opening, a no-moves end and zero rows. Reject the empty verdict if legal moves remain. | One reported empty and zero refused, despite 27 legal moves. |
| 12 | During the real packer's conversion proof, change only the returned result field from +1 to −1. Require an exact fallback. | The packer offered binpack. |
| 13 | Stop after the second offer is renamed and before its inventory entry is appended, then run the packer twice. Both seals must be discoverable once. | Two physical seals, only the first listed after both restarts. |
| 14 | After a successful receive, remove the retained working file and its ACK. Redeliver the original offer. Restore verified custody or request recovery before giving another ACK. | Another ACK, zero matching retained bytes, no recovery request. |
| 15 | A restored sender offers a different valid finished object at an already-sealed slot/index. Preserve the first accepted object and digest; record conflict and zero additional credit. | The ACK and retained object changed, two games were credited under one piece index. |
| 16 | Remove the second of two credited raw inputs during round publication, then restore it and retry at the same destination. Leave the public destination absent on failure and publish both rows after retry. | First exit 3 with 110 public bytes visible; retry exit 2 and no complete report. |

```sh
python debate/server_day/cases/astra/player_cases.py --scripts debate/server_day/scripts --forge path/to/qualified/forge --net loop/forge65_r0067.fnn3 8
python debate/server_day/cases/astra/player_cases.py --scripts debate/server_day/scripts --forge path/to/qualified/forge --net loop/forge65_r0067.fnn3 9
python debate/server_day/cases/astra/player_cases.py --scripts debate/server_day/scripts 10
python debate/server_day/cases/astra/player_cases.py --scripts debate/server_day/scripts 11
python debate/server_day/cases/astra/player_cases.py --scripts debate/server_day/scripts 12
python debate/server_day/cases/astra/transport_cases.py --scripts debate/server_day/scripts 13
python debate/server_day/cases/astra/transport_cases.py --scripts debate/server_day/scripts 14
python debate/server_day/cases/astra/transport_cases.py --scripts debate/server_day/scripts 15
python debate/server_day/cases/astra/transport_cases.py --scripts debate/server_day/scripts 16
```
