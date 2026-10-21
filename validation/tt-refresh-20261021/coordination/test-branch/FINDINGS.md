# Public tester-branch observation

One unauthenticated GET to https://github.com/couns0538-sketch/dwqww/tree/forge/test-20261021-0330 completed HTTP200; final URL is identical. Redirects and retries were disabled; per-operation timeout20s, aggregate deadline35s.

The exact saved response entity body is341,508bytes, SHA-256 `b149e62850d1d34c0e15ace351f1c958fa0d47ef993825f987bd0fdbd03b9080`. Original ordered response header fields, library header serialization, status, command/script hash and closed fetch receipt are retained. Header serialization is not a TCP wire capture.

Both branch refInfo records in the original embedded JSON report `forge/test-20261021-0330` at **5101c2529d386b7c3a04ba9156a69ee34df6bb43**. This agrees with root's existing accepted5101 observation; the branch name is not evidence of a new test run. The root listing shows directory names only. No checkpoint contents, test outcomes, PR page or other branch were fetched.

No second network request, API/auth troubleshooting, Git mutation, engine/build/test or external message was performed. Exact extracted JSON paths and original ref objects are in EXTRACTED-IDENTITY.json.
