# S18 source/data checkpoint preservation — 2026-10-26

This preserves an unfinished offline job, with no change to the delivered count. All168 original files are retained in the lossless data/source checkpoint archive; the167-entry original manifest passed. Python member-byte verification and independent Python/GNU gzip decoding passed, with original files unchanged. No filtering, SQLite query, trainer import, training or native engine run occurred during encoding.

t200 repeats kept132421 and t400 repeats175673 with byte-identical11-file outputs. t500first kept187141; the original repeat failed its120-second deadline, remains unsealed, and all partial POS/HCE/database/WAL/SHM bytes are preserved. Its cause is unresolved. An outer traceback existed only in the original tool output and has not been reconstructed as a supposed raw log. Histogram13/trainer14 dry checks pass; full histograms, actual training, all50000-row postscore and real013/014 checks remain UNVERIFIED. New bounded diagnostic code is being prepared without execution and cannot relabel the original failure.

No engine/network/accepted source changes. Never run the trainer or resume filtering from an unsealed partial output. Resume from the frozen protocol and a separately authorized NEW diagnostic/output directory after S10 timing-sensitive windows close.
