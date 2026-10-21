# Public Forge 6.4.20 archive readback

An unauthenticated HTTPS readback at exact repository commit
`7aed6c969135c5761f8b7c89db2220668b871db0` completed once with exit 0 and empty
stderr. All four top-level GET responses returned HTTP 200, and each recorded
final URL equals its requested commit-pinned URL.

Both large parts were streamed directly into independent per-part and ordered
combined SHA-256 hashers. Their 113,855,291 combined bytes match
`ee1bdd21707175cd57107a3a4a1c1daacd106975974b53d40338f0b9f1a22f7e`.
The small public response bodies are retained exactly; large part bodies were
streamed rather than saved again. Original local archive parts remain retained.

| Public object | Received bytes | SHA-256 |
| --- | ---: | --- |
| Manifest | 449,588 | `9f12841fbdba3a9575d53c36bae5e6ae105d3f5c78a42c44b358c696fb789478` |
| Final verification receipt | 16,353 | `8504ea11ff5e64de48972289450b5ffc0248979d669bc205028928d74fc9f892` |
| Part 0001 | 67,108,864 | `44de1a6ff175ecf9ae74b93e31663d312393b1b380ca8bef92a7d52cefad01d9` |
| Part 0002 | 46,746,427 | `f7e7e3bddd083e01ac9bd051f47774195c78e26f3d87bc7c5634f18df0d42398` |

Verified public URLs:

- [Manifest](https://raw.githubusercontent.com/couns0538-sketch/dwqww/7aed6c969135c5761f8b7c89db2220668b871db0/validation/pawn-span-fill-20261020/archive-complete/forge-pawn-span-fc23918-20261020-complete.manifest.json)
- [Final verification receipt](https://raw.githubusercontent.com/couns0538-sketch/dwqww/7aed6c969135c5761f8b7c89db2220668b871db0/validation/pawn-span-fill-20261020/archive-complete/FINAL-VERIFICATION.json)
- [Part 0001](https://raw.githubusercontent.com/couns0538-sketch/dwqww/7aed6c969135c5761f8b7c89db2220668b871db0/validation/pawn-span-fill-20261020/archive-complete/forge-pawn-span-fc23918-20261020-complete.zip.part0001)
- [Part 0002](https://raw.githubusercontent.com/couns0538-sketch/dwqww/7aed6c969135c5761f8b7c89db2220668b871db0/validation/pawn-span-fill-20261020/archive-complete/forge-pawn-span-fc23918-20261020-complete.zip.part0002)

[RESULT.json](RESULT.json) records original HTTP status, request/response headers,
URLs, timestamps, sizes and streamed hashes. Individual `*.http.json` and
`*.headers.txt` files retain the request results and original response header
serializations. [COMMAND.json](COMMAND.json), [LAUNCH.json](LAUNCH.json),
[EXIT.json](EXIT.json), `transport.stdout` and `transport.stderr` preserve exact
execution provenance. [TRANSPORT-REVIEW.json](TRANSPORT-REVIEW.json) records the
independent local review without duplicating the public downloads.

This proves public byte identity at the named commit. The public archive contains
frozen candidate source `fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`; publication
commit and source candidate are distinct identities. No engine, compiler, Git,
benchmark, game, archive mutation or source mutation ran in this readback task.
No new Elo or speed result is claimed. These transport sidecars are intentionally
outside the immutable archive directory.
