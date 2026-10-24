#!/usr/bin/env python3
"""Bounded original-stream cmp with independent hashes and lossless retention.

New output directories are mandatory. Equal gzip archives are hardlinked only
after both original raw streams and both independently compressed streams pass
cmp, SHA256 and length checks. Historical evidence is never opened for writing.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import threading
import time


HEADER_BYTES = 64
TRAILER_BYTES = 256
HIDDEN = 256
FLOATS = 2 * HIDDEN
PREFIX_BYTES = 104
RECORD_BYTES = PREFIX_BYTES + 2 * (FLOATS * 4 + 8)
RESERVE_BYTES = 512 * 1024 * 1024


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for data in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def cmp_files(left, right, log):
    with log.open("wb") as output:
        return subprocess.run(["cmp", "--", str(left), str(right)],
                              stdout=output, stderr=subprocess.STDOUT).returncode


def read_exact(process, output, count, digest, side, total_bytes):
    remaining = count
    while remaining:
        data = process.stdout.read(min(remaining, 1024 * 1024))
        if not data:
            raise RuntimeError(f"{side} truncated stream: missing {remaining} of {count} bytes")
        output.write(data)
        digest.update(data)
        total_bytes[side] += len(data)
        remaining -= len(data)


def validate_header(data, positions):
    header = struct.unpack("<16I", data)
    count = header[4] | (header[5] << 32)
    if (header[:4] != (0x314F4D4E, 1, HIDDEN, RECORD_BYTES) or count != positions or
            header[6:8] != (0x85A308D3, 0x243F6A88) or
            header[9:13] != (0, 192, 10, 2) or any(header[13:])):
        raise RuntimeError("invalid corpus header, H256 architecture or requested position count")
    return {"magic": "NMO1", "hidden": header[2], "record_bytes": header[3],
            "positions": count, "seed": "243f6a8885a308d3", "mxcsr": header[8],
            "rounding": header[9], "walk_max_plies": header[10]}


def validate_trailer(data, positions):
    trailer = struct.unpack("<64I", data)
    counts = [trailer[i] | (trailer[i + 1] << 32) for i in range(2, 16, 2)]
    records, fresh, updates, parent, inplace, games, starts = counts
    if (trailer[:2] != (0x544F4D4E, 1) or records != positions or fresh != positions or
            updates + starts != positions or parent != updates or inplace != updates or
            games != starts or sum(trailer[16:18]) != updates or
            any(value == 0 for value in trailer[16:42]) or any(trailer[42:])):
        raise RuntimeError("invalid trailer: incomplete real-position/API/special-move coverage")
    return {"records": records, "refresh": fresh, "updates": updates,
            "parent_checks": parent, "inplace_checks": inplace, "games": games,
            "starts": starts, "moves": list(trailer[16:18]),
            "captures": list(trailer[18:20]), "en_passant": list(trailer[20:22]),
            "castles_white_KQ_black_KQ": list(trailer[22:26]),
            "quiet_promotions_white_NBRQ_black_NBRQ": list(trailer[26:34]),
            "capture_promotions_white_NBRQ_black_NBRQ": list(trailer[34:42])}


def compress_original(raw, compressed, level):
    with raw.open("rb") as source, compressed.open("xb") as target:
        with gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0,
                           compresslevel=level) as archive:
            shutil.copyfileobj(source, archive, length=1024 * 1024)
    restored = hashlib.sha256()
    restored_bytes = 0
    with gzip.open(compressed, "rb") as archive:
        for data in iter(lambda: archive.read(1024 * 1024), b""):
            restored.update(data)
            restored_bytes += len(data)
    if restored.hexdigest() != sha256_file(raw) or restored_bytes != raw.stat().st_size:
        raise RuntimeError("gzip round-trip changed the original output bytes")
    return {"gzip": compressed.name, "gzip_bytes": compressed.stat().st_size,
            "gzip_sha256": sha256_file(compressed), "gzip_roundtrip_bytes": restored_bytes,
            "gzip_roundtrip_sha256": restored.hexdigest()}


def negative_controls(output, raw, header_bytes):
    controls = []
    with raw.open("rb") as source:
        source.seek(header_bytes)
        original = source.read(RECORD_BYTES)
    if len(original) != RECORD_BYTES:
        raise RuntimeError("negative control has no complete real record")
    source_path = output / "negative-control-original-record.bin"
    source_path.write_bytes(original)
    for name, offset in (("float-bit", PREFIX_BYTES),
                         ("eval-int-bit", PREFIX_BYTES + FLOATS * 4)):
        mutated = bytearray(original)
        mutated[offset] ^= 1
        target = output / f"negative-control-{name}.bin"
        target.write_bytes(mutated)
        code = cmp_files(source_path, target, output / f"negative-control-{name}.cmp.log")
        controls.append({"kind": name, "record_byte_offset": offset, "cmp_exit": code,
                         "original_sha256": sha256_file(source_path),
                         "mutated_sha256": sha256_file(target), "retained": target.name})
        if code != 1:
            raise RuntimeError(f"{name} negative control failed to detect one changed bit")
    return controls


def load_reference(path, args):
    path = path.resolve()
    manifest_bytes = path.read_bytes()
    reference = json.loads(manifest_bytes)
    for key, value in (("status", "PASS"), ("records", args.positions),
                       ("requested_records", args.positions),
                       ("chunk_records", args.chunk_records), ("gzip_level", args.gzip_level),
                       ("record_bytes", RECORD_BYTES)):
        if reference.get(key) != value:
            raise RuntimeError(f"incompatible canonical corpus/chunk metadata: {key}")
    expected_chunks = (args.positions + args.chunk_records - 1) // args.chunk_records
    if len(reference.get("chunks", [])) != expected_chunks:
        raise RuntimeError("incompatible canonical chunk count")
    info = {"path": str(path), "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "runner_source_sha256": reference.get("runner_source_sha256"),
            "off_binary_sha256": reference["off"]["binary_sha256"],
            "on_binary_sha256": reference["on"]["binary_sha256"]}
    return reference, path.parent, info


def reference_dedup(output, chunk, canonical, canonical_root):
    for key in ("index", "records", "first_record", "header_bytes", "trailer_bytes", "expected_bytes"):
        if chunk[key] != canonical.get(key):
            raise RuntimeError(f"incompatible canonical chunk metadata: {key}")
    for side in ("off", "on"):
        for key in ("raw_bytes", "raw_sha256", "gzip_bytes", "gzip_sha256"):
            if chunk[side][key] != canonical[side].get(key):
                raise RuntimeError(f"canonical original output differs: {side}/{key}")
    name = canonical["off"]["gzip"]
    if Path(name).name != name:
        raise RuntimeError("canonical gzip must be a local archive filename")
    archive = canonical_root / name
    if archive.stat().st_mode & 0o222:
        raise RuntimeError("canonical archive is writable; immutable evidence required")
    before = sha256_file(archive)
    if before != canonical["off"]["gzip_sha256"] or archive.stat().st_size != canonical["off"]["gzip_bytes"]:
        raise RuntimeError("canonical archive checksum/size is corrupt")
    proof = {"canonical_path": str(archive.resolve()), "canonical_sha256_before": before,
             "canonical_bytes": archive.stat().st_size, "cmp_exit": {}}
    for side in ("off", "on"):
        current = output / chunk[side]["gzip"]
        code = cmp_files(current, archive,
                         output / f"chunk-{chunk['index']:06d}.{side}.canonical.cmp.log")
        proof["cmp_exit"][side] = code
        if code != 0:
            raise RuntimeError("canonical archive byte comparison failed")
    # Only these freshly generated paths are unlinked. The canonical inode and
    # all pre-existing paths remain read-only throughout this operation.
    for side in ("off", "on"):
        current = output / chunk[side]["gzip"]
        current.unlink()
        os.link(archive, current)
    proof["canonical_sha256_after"] = sha256_file(archive)
    if proof["canonical_sha256_after"] != before:
        raise RuntimeError("canonical archive changed during hardlink deduplication")
    proof["hardlinked_after_all_fresh_stream_proofs"] = True
    return proof


def run(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "RUNNING", "requested_records": args.positions, "records": 0,
              "chunk_records": args.chunk_records, "gzip_level": args.gzip_level,
              "record_bytes": RECORD_BYTES, "chunks": [], "negative_controls": [],
              "runner_source_sha256": sha256_file(Path(__file__)),
              "minimum_free_reserve_bytes": RESERVE_BYTES,
              "timeout_seconds": args.timeout_seconds,
              "dedup_policy": "Only newly generated equal immutable gzip archives; raw cmp, raw SHA256/size, compressed cmp and compressed SHA256/size all required.",
              "started_unix": time.time()}
    processes = {}
    logs = {}
    digests = {side: hashlib.sha256() for side in ("off", "on")}
    total_bytes = {side: 0 for side in ("off", "on")}
    timed_out = threading.Event()
    watchdog = None

    def stop_hung_producers():
        timed_out.set()
        for process in processes.values():
            if process.poll() is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass

    def save():
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")

    save()
    try:
        reference = None
        canonical_root = None
        if args.dedup_reference_result is not None:
            reference, canonical_root, info = load_reference(args.dedup_reference_result, args)
            report["dedup_reference_result"] = info
        for side in ("off", "on"):
            binary = getattr(args, side).resolve()
            command = [str(binary), "--positions", str(args.positions)]
            report[side] = {"command": command, "binary_sha256": sha256_file(binary)}
            logs[side] = (output / f"{side}.stderr.log").open("wb")
            processes[side] = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=logs[side])
        watchdog = threading.Timer(args.timeout_seconds, stop_hung_producers)
        watchdog.daemon = True
        watchdog.start()
        first = True
        remaining = args.positions
        index = 0
        while remaining:
            records = min(remaining, args.chunk_records)
            header_bytes = HEADER_BYTES if first else 0
            trailer_bytes = TRAILER_BYTES if records == remaining else 0
            expected = header_bytes + records * RECORD_BYTES + trailer_bytes
            # Four chunk sizes cover two raw files and two worst-case gzip files;
            # abort before ENOSPC while retaining all earlier original archives.
            available = shutil.disk_usage(output).free
            if available < 4 * expected + RESERVE_BYTES:
                raise RuntimeError(f"disk reserve: {available} free, need {4 * expected + RESERVE_BYTES}")
            chunk = {"index": index, "records": records, "first_record": report["records"],
                     "header_bytes": header_bytes, "trailer_bytes": trailer_bytes,
                     "expected_bytes": expected}
            report["chunks"].append(chunk)
            raws = {}
            for side in ("off", "on"):
                raw = output / f"chunk-{index:06d}.{side}.raw"
                raws[side] = raw
                with raw.open("xb") as target:
                    read_exact(processes[side], target, expected, digests[side], side, total_bytes)
                chunk[side] = {"raw_bytes": raw.stat().st_size, "raw_sha256": sha256_file(raw)}
                with raw.open("rb") as source:
                    if first:
                        report[side]["header"] = validate_header(source.read(HEADER_BYTES), args.positions)
                    if trailer_bytes:
                        source.seek(-TRAILER_BYTES, os.SEEK_END)
                        report[side]["coverage"] = validate_trailer(source.read(TRAILER_BYTES), args.positions)
            chunk["raw_cmp_exit"] = cmp_files(raws["off"], raws["on"],
                                              output / f"chunk-{index:06d}.raw.cmp.log")
            if (chunk["raw_cmp_exit"] != 0 or
                    chunk["off"]["raw_sha256"] != chunk["on"]["raw_sha256"] or
                    chunk["off"]["raw_bytes"] != chunk["on"]["raw_bytes"]):
                raise RuntimeError(f"original accumulator/eval stream mismatch in chunk {index}")
            if first:
                report["negative_controls"] = negative_controls(output, raws["off"], header_bytes)
            for side in ("off", "on"):
                archive = output / f"chunk-{index:06d}.{side}.bin.gz"
                chunk[side].update(compress_original(raws[side], archive, args.gzip_level))
            chunk["gzip_cmp_exit"] = cmp_files(output / chunk["off"]["gzip"],
                                               output / chunk["on"]["gzip"],
                                               output / f"chunk-{index:06d}.gzip.cmp.log")
            if (chunk["gzip_cmp_exit"] != 0 or
                    chunk["off"]["gzip_sha256"] != chunk["on"]["gzip_sha256"] or
                    chunk["off"]["gzip_bytes"] != chunk["on"]["gzip_bytes"]):
                raise RuntimeError("independent deterministic gzip archives differ; raw evidence retained")
            left, right = (output / chunk[side]["gzip"] for side in ("off", "on"))
            right.unlink()
            os.link(left, right)
            left.chmod(0o444)
            chunk["gzip_hardlink_deduplicated_after_proof"] = True
            chunk["retained_physical_gzip_bytes"] = left.stat().st_size
            if reference is not None:
                chunk["reference_dedup"] = reference_dedup(output, chunk,
                                                         reference["chunks"][index], canonical_root)
                chunk["retained_additional_physical_gzip_bytes"] = 0
            else:
                chunk["retained_additional_physical_gzip_bytes"] = left.stat().st_size
            # Remove only these new raw chunks after preserving both complete
            # original byte sequences in proven lossless, immutable archives.
            for raw in raws.values():
                raw.unlink()
            report["records"] += records
            remaining -= records
            index += 1
            first = False
            save()
            print(f"records={report['records']} gzip_unique_bytes="
                  f"{sum(c.get('retained_physical_gzip_bytes', 0) for c in report['chunks'])}",
                  file=sys.stderr, flush=True)
        for side in ("off", "on"):
            extra = processes[side].stdout.read(1)
            if extra:
                (output / f"{side}.unexpected-extra-byte.bin").write_bytes(extra)
                raise RuntimeError(f"{side} has extra bytes after exact corpus trailer")
            code = processes[side].wait(timeout=30)
            report[side]["exit_code"] = code
            if code != 0:
                raise RuntimeError(f"{side} producer exited {code} after its output")
        expected_total = HEADER_BYTES + args.positions * RECORD_BYTES + TRAILER_BYTES
        if timed_out.is_set():
            raise RuntimeError(f"producer timeout after {args.timeout_seconds} seconds")
        if any(count != expected_total for count in total_bytes.values()):
            raise RuntimeError("independent full-stream byte count mismatch")
        report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = (f"producer timeout after {args.timeout_seconds} seconds: {error}"
                           if timed_out.is_set() else str(error))
        print(f"nnue_million_oracle: {error}", file=sys.stderr)
    finally:
        if watchdog is not None:
            watchdog.cancel()
        for side, process in processes.items():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            report[side]["exit_code"] = process.returncode
            report[side]["sha256"] = digests[side].hexdigest()
            report[side]["bytes"] = total_bytes[side]
            process.stdout.close()
        for log in logs.values():
            log.close()
        report["finished_unix"] = time.time()
        save()
    return 0 if report["status"] == "PASS" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--off", type=Path, required=True)
    parser.add_argument("--on", type=Path, required=True)
    parser.add_argument("--positions", type=int, default=1000000)
    parser.add_argument("--chunk-records", type=int, default=10000)
    parser.add_argument("--gzip-level", type=int, default=6, choices=range(1, 10))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=3600,
                        help="Kill stalled producers at this total run limit and retain actual exit codes")
    parser.add_argument("--dedup-reference-result", type=Path,
                        help="Reuse prior immutable gzip inodes only after fresh execution/cmp/hash proofs")
    args = parser.parse_args()
    if args.positions < 1 or args.chunk_records < 1 or args.timeout_seconds <= 0:
        parser.error("position/chunk counts and timeout must be positive")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
