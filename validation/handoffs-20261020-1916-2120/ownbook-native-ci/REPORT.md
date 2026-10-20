# Original OwnBook CI evidence retrieval

Public metadata is now independently confirmed; the original raw test evidence remains unavailable. No tests, engines, builds or Git writes were executed.

The unauthenticated public [run page](https://github.com/couns0538-sketch/dwqww/actions/runs/39446498263) returned HTTP 200 and identifies successful run `39446498263`, workflow commit `9a6598bc718bfc144b2499277b7affc89a152e10`, and successful job `118709700044` (`baseline-versus-fix`, 43 seconds). It lists one artifact:

| Field | Public-page value |
| --- | --- |
| ID | `12276067068` |
| Name | `forge-ownbook-native-baseline-vs-fix-20261020` |
| Displayed size | `7.01 KB` |
| Displayed digest | `sha256:def0d77d1e74627db750bde7fba02f3ba87ca6b66c9990d963a8a7c980bb99f9` |

That digest was read from GitHub's artifact row; it has **not** been checked against downloaded ZIP bytes. The page itself is preserved as `run-page.html`, SHA256 `a2ab3ea2b537e5df8426bc2bbc1c0cda9f26fb104081c6572138bb024ed8e380`.

The exact local Git object for that workflow is preserved as `workflow-pinned-source.yml` (SHA256 `f3b1bc72bb9cadccd273bb6ac430e7dbe00579b4f1d22f61ac47f29cc9b6ad59`). It pins baseline **`356e863dbd86d2ce24b8ee9486d7406f1d525480`** and corrected source/test **`5101c2529d386b7c3a04ba9156a69ee34df6bb43`**, whose parent is one-line source repair `af1941375111717f415a46d9ce0224c329034466`. It specifies Release, `FORGE_NATIVE=OFF`, both four-suite CTests, then the same native script against baseline `--expect-leak yes` and candidate `--expect-leak no`. The exact test source and UCI source diff are preserved here without execution. These source pins are verified workflow contents, not recovered runtime provenance.

Access stopped after four bounded, unauthenticated GETs:

- Run page: HTTP 200; public status/artifact metadata recovered.
- Artifacts API: `URLError: <urlopen error Tunnel connection failed: 403 Forbidden>` before an API response body; no conclusion about API permissions or artifact expiry follows.
- Job page: HTTP 200; explicitly **“Sign in to view logs.”** No CTest output, UCI transcript, decision text or executable hash is present in that captured page.
- Standard public artifact URL: redirected to `/couns0538-sketch/dwqww/suites/106894148254/artifacts/12276067068`, returning HTTP 404 with HTML, not ZIP bytes. This does not establish whether authenticated retrieval would succeed.

Each access has a JSON record and original response bytes where received. Current callable tool discovery exposed 18 tools; no GitHub workflow/artifact reader or generic tool-search method was available. The onboarding configuration tool is unrelated and was not invoked. No credentials, configuration changes, plugin installation or alternate write path were used.

`VERIFICATION.json` therefore records `PUBLIC_METADATA_VERIFIED_RAW_ARTIFACT_UNAVAILABLE`, with raw CTest/transcript/executable-hash verification all false. The remaining completion action is retrieval of this exact original artifact through already authorized authenticated GitHub access, followed by ZIP digest and raw provenance/transcript verification. There is no reason to repeat the completed test run merely to replace inaccessible evidence. Accepted-lineage integration remains separate from candidate 17, which already contains the repair.
