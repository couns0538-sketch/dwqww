# Item2 — platform-consistent stat identity

Non-POSIX identity excludes ctime only; device, inode, size and mtime remain
checked. POSIX retains ctime mutation detection. Three regressions cover the
cross-call Windows condition and retained safeguards; red then green preserved.
Platform behavior was simulated around real file hashing on Linux, not executed
on Windows. No PC access. IDEA_SOURCE: QA Python3.12 Windows stat/fstat report.
