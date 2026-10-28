# fable-review-S47

Base: opus-sol-S47 head. Correction (Fable review, mistake 3): the audit tests use fixture "exe" and lock files that are
small text files whose SHA256 is frozen in the fixture RUN_INFO/SOURCES lists as the LF bytes (e.g. forge_fx_new.exe ->
0bb06372...). On a Windows checkout with core.autocrlf=true the fixtures are checked out as CRLF, so three audit
tests fail on the PC. Fix: `.gitattributes` with `* -text` in the job folder. Verified: the test passes in a fresh
worktree of this branch. No tool logic changed.
