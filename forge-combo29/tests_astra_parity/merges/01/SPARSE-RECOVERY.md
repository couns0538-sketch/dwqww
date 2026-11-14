# Sparse checkout recovery

All four git merge-file commands returned0. The later git diff --check returned128 because the shared repository lacks an excluded historical report blob. No engine conflict or source correction occurred. Root ran the following metadata-only command, observed exit0 with empty stdout/stderr, then status showed only the four intended source modifications plus the new report/tests directory. A repeated git diff --check exited0 without output. The captured recovery below checks every source file byte-for-byte against its original merge output before committing only those four paths.

```text
git sparse-checkout set --no-cone --stdin <<'EOF'
/forge-combo29/CMakeLists.txt
/forge-combo29/src/
/forge-combo29/include/
/forge-combo29/tests_astra_parity/
/forge-combo29/REPORT_astra_parity.md
EOF
```

This command/output description is transcribed from the root tool result; subsequent verification and commit commands have complete raw outputs in recovery-commands.txt.
