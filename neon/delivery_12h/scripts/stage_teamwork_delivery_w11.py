"""Stage verified Wave 11 curated text-only deliverables into C:\\nnue-lab\\teamwork\\.

SAFETY CONTRACT:
  - Uses external manifest DELIVERY_MANIFEST_W11.json (overridable via --manifest).
  - Defaults unconditionally to --dry-run (read-only; NEVER touches C:\\nnue-lab\\teamwork\\).
  - Mutually exclusive --dry-run / --verify-manifest / --check-freeze / --live modes.
  - NO --allow-unfrozen escape hatch.
  - Refuses --live (RC=2, creating zero dirs and copying zero files) unless ALL hold:
      (a) --confirm-quest-complete YES_COPY_TO_TEAMWORK, AND
      (b) freeze check passes (zero [PENDING/[IN PROGRESS/[QUEUED/[TESTING/[TRAINING markers
          in HANDOFF_12H_DATA_QUALITY.md, zero banned words in HANDOFF_12H_DATA_QUALITY.md,
          AND every pending_until_freeze JSON exists as a valid non-empty JSON dict), AND
      (c) schema_errors==0, dup_dest_rel==0, dup_source==0, missing==0, pending_sibling==0,
          pending_freeze==0, immutable_mismatch==0, forbidden_ext==0, forbidden_path==0,
          forbidden_words==0, json_invalid==0, and total_staged_bytes <= 4_194_304 (4.0 MiB).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

sys.dont_write_bytecode = True

LAB = Path(r"C:\nnue-lab")
DEFAULT_DEST = LAB / "teamwork" / "neon_12h_quest_delivery"
MAX_BUNDLE_BYTES = 4_194_304  # 4.0 MiB
HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "DELIVERY_MANIFEST_W11.json"
CONFIRM_TOKEN = "YES_COPY_TO_TEAMWORK"

VALID_CATEGORIES = {"docs", "packets", "patches", "scripts", "tests", "audits"}
VALID_WAVE_ORIGINS = {
    "W6",
    "W7",
    "post-W6",
    "W8",
    "W9",
    "post-W8",
    "W10",
    "post-W10",
    "W11",
    "freeze-pending",
}
VALID_STATUSES = {"frozen", "living", "pending_freeze"}
REQUIRED_TOP_KEYS = {
    "schema_version",
    "wave",
    "generated_utc",
    "default_dest",
    "max_bundle_bytes",
    "handoff_source",
    "forbidden_suffixes",
    "forbidden_dir_names",
    "forbidden_dir_prefixes",
    "files",
}
REQUIRED_ENTRY_KEYS = {
    "category",
    "source",
    "dest_rel",
    "sha256",
    "status",
    "freeze_mutable",
    "wave11_sibling",
    "pending_until_freeze",
    "wave_origin",
}

FORBIDDEN_SUFFIXES = {
    ".binpack",
    ".dll",
    ".epd",
    ".exe",
    ".fnn3",
    ".fqs",
    ".lib",
    ".log",
    ".npz",
    ".o",
    ".obj",
    ".out",
    ".part",
    ".pgn",
    ".plain",
    ".pt",
    ".pyc",
    ".z",
}
FORBIDDEN_DIR_NAMES = {"__pycache__", ".pytest_cache", "_tmp_cache", "_pytest_tmp"}
FORBIDDEN_DIR_PREFIXES = ("_work_",)

SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
FREEZE_MARKER_RE = re.compile(
    r"\[(?:PENDING|IN PROGRESS|QUEUED|TESTING|TRAINING)[^\]]*(?:\]|$)",
    re.IGNORECASE,
)

# Dynamically constructed stem so this script itself contains zero literal banned terms.
_BANNED_STEM = "".join(["c", "u", "r", "e"])
BANNED_WORD_RE = re.compile(r"\b" + _BANNED_STEM + r"d?\b", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def has_forbidden_suffix(
    path_obj: Path, forbidden_suffixes: set[str]
) -> list[str]:
    return [suf for suf in path_obj.suffixes if suf.lower() in forbidden_suffixes]


def has_forbidden_path(
    path_obj: Path,
    forbidden_dir_names: set[str],
    forbidden_dir_prefixes: tuple[str, ...],
) -> bool:
    lower_names = {d.lower() for d in forbidden_dir_names}
    lower_prefixes = tuple(p.lower() for p in forbidden_dir_prefixes)
    for part in path_obj.parts:
        pl = part.lower()
        if pl in lower_names or any(pl.startswith(pref) for pref in lower_prefixes):
            return True
    return False


def is_safe_dest_rel(dest_str: str) -> bool:
    if not isinstance(dest_str, str) or not dest_str or dest_str.strip() != dest_str:
        return False
    if "\x00" in dest_str or ":" in dest_str:
        return False
    if dest_str.startswith(("/", "\\")) or dest_str.endswith(("/", "\\")):
        return False
    raw_segments = re.split(r"[\\/]", dest_str)
    if any(seg in ("", ".", "..") for seg in raw_segments):
        return False
    dp = Path(dest_str)
    dp_win = PureWindowsPath(dest_str)
    dp_pos = PurePosixPath(dest_str)
    for p in (dp, dp_win, dp_pos):
        if p.is_absolute() or bool(p.drive) or bool(p.root) or p.anchor != "" or ".." in p.parts:
            return False
    return True


def normalize_dest_rel_key(dest_str: str) -> str:
    return PurePosixPath(dest_str.replace("\\", "/")).as_posix().lower()


def normalize_source_key(src_str: str) -> str:
    return os.path.normcase(os.path.normpath(src_str))


def validate_manifest_schema(
    manifest: Any,
) -> tuple[list[str], int, int, list[str], list[str]]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["Manifest root must be a JSON object."], 0, 0, [], []

    missing_top = sorted(REQUIRED_TOP_KEYS - set(manifest.keys()))
    if missing_top:
        errors.append(f"Missing top-level manifest keys: {missing_top}")

    if manifest.get("schema_version") != "w11.1":
        errors.append(
            f"Unsupported schema_version: {manifest.get('schema_version')!r} (expected 'w11.1')"
        )
    if manifest.get("wave") != 11 or isinstance(manifest.get("wave"), bool):
        errors.append(f"Invalid wave: {manifest.get('wave')!r} (expected 11)")

    max_bytes = manifest.get("max_bundle_bytes")
    if (
        isinstance(max_bytes, bool)
        or not isinstance(max_bytes, int)
        or max_bytes <= 0
        or max_bytes > MAX_BUNDLE_BYTES
    ):
        errors.append(
            f"Invalid max_bundle_bytes: {max_bytes!r} (must be int 1..{MAX_BUNDLE_BYTES})"
        )

    handoff_src = manifest.get("handoff_source")
    if not isinstance(handoff_src, str) or not handoff_src.strip():
        errors.append("handoff_source must be a non-empty string.")

    for list_key in ("forbidden_suffixes", "forbidden_dir_names", "forbidden_dir_prefixes"):
        val = manifest.get(list_key)
        if not isinstance(val, list) or not all(isinstance(x, str) and x for x in val):
            errors.append(f"{list_key} must be a list of non-empty strings.")

    files = manifest.get("files")
    if not isinstance(files, list) or len(files) == 0:
        errors.append("files must be a non-empty list.")
        return errors, 0, 0, [], []

    dest_seen: dict[str, int] = {}
    src_seen: dict[str, int] = {}
    dup_dest_msgs: list[str] = []
    dup_src_msgs: list[str] = []

    for idx, entry in enumerate(files):
        if not isinstance(entry, dict):
            errors.append(f"Entry #{idx} is not an object.")
            continue
        missing_keys = sorted(REQUIRED_ENTRY_KEYS - set(entry.keys()))
        if missing_keys:
            errors.append(f"Entry #{idx} missing keys: {missing_keys}")
            continue

        cat = entry["category"]
        if cat not in VALID_CATEGORIES:
            errors.append(f"Entry #{idx} invalid category {cat!r}")

        origin = entry["wave_origin"]
        if origin not in VALID_WAVE_ORIGINS:
            errors.append(f"Entry #{idx} invalid wave_origin {origin!r}")

        status_val = entry["status"]
        if status_val not in VALID_STATUSES:
            errors.append(f"Entry #{idx} invalid status {status_val!r}")

        bools_ok = True
        for bkey in ("freeze_mutable", "wave11_sibling", "pending_until_freeze"):
            if not isinstance(entry[bkey], bool):
                errors.append(f"Entry #{idx} {bkey} must be boolean.")
                bools_ok = False

        src_str = entry["source"]
        dest_str = entry["dest_rel"]
        if not isinstance(src_str, str) or not src_str.strip():
            errors.append(f"Entry #{idx} source must be a non-empty string.")
        else:
            sk = normalize_source_key(src_str)
            if sk in src_seen:
                dup_src_msgs.append(f"Duplicate source #{idx} (first at #{src_seen[sk]}): {src_str}")
            else:
                src_seen[sk] = idx

        if not isinstance(dest_str, str) or not dest_str.strip():
            errors.append(f"Entry #{idx} dest_rel must be a non-empty string.")
        else:
            if not is_safe_dest_rel(dest_str):
                errors.append(f"Entry #{idx} invalid relative dest_rel: {dest_str!r}")
            dk = normalize_dest_rel_key(dest_str)
            if dk in dest_seen:
                dup_dest_msgs.append(
                    f"Duplicate dest_rel #{idx} (first at #{dest_seen[dk]}): {dest_str}"
                )
            else:
                dest_seen[dk] = idx

        sha = entry["sha256"]
        sha_valid_hex = isinstance(sha, str) and bool(SHA256_HEX_RE.match(sha))
        if sha is None:
            if bools_ok and not entry["freeze_mutable"]:
                errors.append(f"Entry #{idx} ({dest_str}) has sha256=null with freeze_mutable=false.")
        elif not sha_valid_hex:
            errors.append(f"Entry #{idx} ({dest_str}) has invalid sha256: {sha!r}")

        if bools_ok and status_val in VALID_STATUSES:
            fm = entry["freeze_mutable"]
            w11 = entry["wave11_sibling"]
            puf = entry["pending_until_freeze"]

            if status_val == "pending_freeze":
                if not (puf and fm and sha is None):
                    errors.append(
                        f"Entry #{idx} ({dest_str}) status='pending_freeze' requires "
                        "pending_until_freeze=true, freeze_mutable=true, and sha256=null."
                    )
            elif status_val == "living":
                if not (fm and not puf):
                    errors.append(
                        f"Entry #{idx} ({dest_str}) status='living' requires "
                        "freeze_mutable=true and pending_until_freeze=false."
                    )
            elif status_val == "frozen":
                if fm or puf or w11 or not sha_valid_hex:
                    errors.append(
                        f"Entry #{idx} ({dest_str}) status='frozen' requires "
                        "freeze_mutable=false, pending_until_freeze=false, wave11_sibling=false, "
                        "and a valid 64-hex sha256."
                    )

            if puf and fm and sha is None and status_val != "pending_freeze":
                errors.append(
                    f"Entry #{idx} ({dest_str}) with pending_until_freeze=true, freeze_mutable=true, "
                    f"sha256=null must have status='pending_freeze' (got {status_val!r})."
                )
            if fm and not puf and status_val != "living":
                errors.append(
                    f"Entry #{idx} ({dest_str}) with freeze_mutable=true and pending_until_freeze=false "
                    f"must have status='living' (got {status_val!r})."
                )
            if not fm and not puf and not w11 and sha_valid_hex and status_val != "frozen":
                errors.append(
                    f"Entry #{idx} ({dest_str}) with immutable 64-hex sha256 must have "
                    f"status='frozen' (got {status_val!r})."
                )

    return errors, len(dup_dest_msgs), len(dup_src_msgs), dup_dest_msgs, dup_src_msgs


def check_freeze_state(
    handoff_path: Path, pending_entries: list[dict[str, Any]]
) -> dict[str, Any]:
    handoff_missing = not handoff_path.exists() or not handoff_path.is_file()
    marker_hits: list[dict[str, Any]] = []
    handoff_banned_hits: list[dict[str, Any]] = []
    if not handoff_missing:
        text = handoff_path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in FREEZE_MARKER_RE.findall(line):
                marker_hits.append(
                    {
                        "line": lineno,
                        "marker": m,
                        "line_preview": line.strip()[:160],
                    }
                )
            for bw in BANNED_WORD_RE.findall(line):
                handoff_banned_hits.append(
                    {
                        "line": lineno,
                        "word": bw,
                        "line_preview": line.strip()[:160],
                    }
                )

    pending_freeze_issues: list[str] = []
    pending_freeze_details: list[dict[str, Any]] = []
    for item in pending_entries:
        src_val = item.get("source")
        if not isinstance(src_val, str) or not src_val.strip():
            msg = f"INVALID source for pending_until_freeze target: {src_val!r}"
            pending_freeze_issues.append(msg)
            pending_freeze_details.append({"source": repr(src_val), "status": "INVALID_SOURCE"})
            continue
        src = Path(src_val)
        if not src.exists() or not src.is_file():
            status = "MISSING" if not src.exists() else "NOT_A_FILE"
            msg = f"{status} pending_until_freeze target: {src}"
            pending_freeze_issues.append(msg)
            pending_freeze_details.append({"source": str(src), "status": status})
            continue
        try:
            parsed = json.loads(src.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            msg = f"INVALID JSON for pending_until_freeze target {src}: {exc}"
            pending_freeze_issues.append(msg)
            pending_freeze_details.append({"source": str(src), "status": "INVALID_JSON"})
            continue
        if not isinstance(parsed, dict) or len(parsed) == 0:
            msg = f"EMPTY_OR_NON_DICT JSON for pending_until_freeze target {src}"
            pending_freeze_issues.append(msg)
            pending_freeze_details.append({"source": str(src), "status": "EMPTY_OR_NON_DICT"})
            continue
        pending_freeze_details.append(
            {"source": str(src), "status": "VALID_NONEMPTY_DICT", "keys": len(parsed)}
        )

    freeze_ok = (
        not handoff_missing
        and len(marker_hits) == 0
        and len(handoff_banned_hits) == 0
        and len(pending_freeze_issues) == 0
    )
    return {
        "handoff_path": str(handoff_path),
        "handoff_missing": handoff_missing,
        "marker_hits": marker_hits,
        "handoff_banned_hits": handoff_banned_hits,
        "pending_freeze_issues": pending_freeze_issues,
        "pending_freeze_details": pending_freeze_details,
        "freeze_ok": freeze_ok,
    }


def inspect_bundle(
    manifest: dict[str, Any],
    dest_root: Path,
    verbose_files: bool = True,
) -> dict[str, Any]:
    schema_errors, dup_dest_rel, dup_source, dup_dest_msgs, dup_src_msgs = (
        validate_manifest_schema(manifest)
    )
    if dup_dest_msgs:
        for msg in dup_dest_msgs:
            print(f"[DUP_DEST_REL] {msg}", file=sys.stderr)
    if dup_src_msgs:
        for msg in dup_src_msgs:
            print(f"[DUP_SOURCE] {msg}", file=sys.stderr)

    manifest_dict = manifest if isinstance(manifest, dict) else {}
    combined_suffixes = set(FORBIDDEN_SUFFIXES) | {
        s.lower() for s in manifest_dict.get("forbidden_suffixes", []) if isinstance(s, str)
    }
    combined_dir_names = set(FORBIDDEN_DIR_NAMES) | {
        d for d in manifest_dict.get("forbidden_dir_names", []) if isinstance(d, str)
    }
    combined_dir_prefixes = tuple(
        sorted(
            set(FORBIDDEN_DIR_PREFIXES)
            | {p for p in manifest_dict.get("forbidden_dir_prefixes", []) if isinstance(p, str)}
        )
    )
    raw_max_bytes = manifest_dict.get("max_bundle_bytes", MAX_BUNDLE_BYTES)
    if (
        isinstance(raw_max_bytes, int)
        and not isinstance(raw_max_bytes, bool)
        and 1 <= raw_max_bytes <= MAX_BUNDLE_BYTES
    ):
        max_bundle_bytes = raw_max_bytes
    else:
        max_bundle_bytes = MAX_BUNDLE_BYTES
    files = manifest_dict.get("files", []) if isinstance(manifest_dict.get("files"), list) else []
    resolved_dest_root = dest_root.resolve()

    missing = 0
    pending_sibling = 0
    pending_freeze = 0
    changed = 0
    immutable_mismatch = 0
    forbidden_ext = 0
    forbidden_path = 0
    forbidden_words = 0
    json_invalid = 0
    matched = 0
    total_bytes = 0

    cat_counts: Counter[str] = Counter()
    cat_bytes: Counter[str] = Counter()
    origin_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    copy_sources: list[tuple[Path, str]] = []
    compact_files: list[dict[str, Any]] = []
    pending_entries: list[dict[str, Any]] = []
    file_lines: list[str] = []

    for item in files:
        if not isinstance(item, dict) or not REQUIRED_ENTRY_KEYS.issubset(item.keys()):
            continue
        if (
            not isinstance(item["source"], str)
            or not isinstance(item["dest_rel"], str)
            or not isinstance(item["category"], str)
            or not isinstance(item["wave_origin"], str)
            or not isinstance(item["status"], str)
        ):
            continue
        src = Path(item["source"])
        dest_rel_str = item["dest_rel"]
        dest_rel_path = Path(dest_rel_str)
        cat = item["category"]
        origin_counts[item["wave_origin"]] += 1
        status_counts[item["status"]] += 1

        if item.get("pending_until_freeze"):
            pending_entries.append(item)

        bad_src_sufs = has_forbidden_suffix(src, combined_suffixes)
        bad_dst_sufs = has_forbidden_suffix(dest_rel_path, combined_suffixes)
        if bad_src_sufs or bad_dst_sufs:
            forbidden_ext += 1
            file_lines.append(
                f"[FORBIDDEN_EXT] {src} -> {dest_rel_str} (src={bad_src_sufs}, dst={bad_dst_sufs})"
            )

        if has_forbidden_path(src, combined_dir_names, combined_dir_prefixes) or has_forbidden_path(
            dest_rel_path, combined_dir_names, combined_dir_prefixes
        ):
            forbidden_path += 1
            file_lines.append(f"[FORBIDDEN_PATH] {src} -> {dest_rel_str}")

        if not is_safe_dest_rel(dest_rel_str):
            file_lines.append(f"[UNSAFE_DEST_REL] {src} -> {dest_rel_str!r}")
            continue

        dst = dest_root / dest_rel_path
        try:
            in_dest = dst.resolve().is_relative_to(resolved_dest_root)
        except (OSError, ValueError):
            in_dest = False
        if not in_dest:
            schema_errors.append(
                f"dest_rel escapes dest_root after resolution: {dest_rel_str!r} -> {dst}"
            )
            file_lines.append(f"[ESCAPE_DEST_REL] {src} -> {dst}")
            continue

        if not src.exists():
            if item.get("pending_until_freeze"):
                pending_freeze += 1
                file_lines.append(f"[PENDING_UNTIL_FREEZE] {src} -> {dst}")
            elif item.get("wave11_sibling"):
                pending_sibling += 1
                file_lines.append(f"[PENDING_W11_SIBLING] {src} -> {dst}")
            else:
                missing += 1
                file_lines.append(f"[MISSING] {src} -> {dst}")
            continue

        if not src.is_file():
            missing += 1
            file_lines.append(f"[NOT_A_FILE] {src} -> {dst}")
            continue

        size = src.stat().st_size
        total_bytes += size
        cat_counts[cat] += 1
        cat_bytes[cat] += size
        actual_sha = sha256_file(src)

        if src.suffix.lower() == ".json" and (
            item.get("freeze_mutable") or item.get("pending_until_freeze")
        ):
            try:
                parsed = json.loads(src.read_text(encoding="utf-8"))
                if item.get("pending_until_freeze") and (
                    not isinstance(parsed, dict) or len(parsed) == 0
                ):
                    json_invalid += 1
                    file_lines.append(f"[JSON_INVALID_EMPTY] {dest_rel_str} | src={src}")
            except (OSError, json.JSONDecodeError) as exc:
                json_invalid += 1
                file_lines.append(f"[JSON_INVALID] {dest_rel_str} | err={exc} | src={src}")

        if (
            item.get("wave11_sibling")
            or item.get("wave_origin") in ("W11", "post-W10")
            or normalize_dest_rel_key(dest_rel_str) == "docs/handoff_12h_data_quality.md"
        ):
            txt = src.read_text(encoding="utf-8", errors="replace")
            hits = BANNED_WORD_RE.findall(txt)
            if hits:
                forbidden_words += len(hits)
                file_lines.append(
                    f"[FORBIDDEN_WORD] {dest_rel_str} | hits={hits[:5]} | src={src}"
                )

        expected_sha = item.get("sha256")
        if expected_sha is not None and actual_sha == expected_sha:
            state = "MATCH"
            matched += 1
        elif item.get("freeze_mutable"):
            state = "CHANGED_MUTABLE" if expected_sha is not None else "MUTABLE_SELF"
            changed += 1
        else:
            state = "SHA_MISMATCH"
            changed += 1
            immutable_mismatch += 1

        if verbose_files:
            file_lines.append(
                f"[{state}] {dest_rel_str} | {size} B | sha256={actual_sha[:16]} | src={src}"
            )
        copy_sources.append((src, dest_rel_str))
        compact_files.append(
            {
                "dest_rel": dest_rel_str,
                "bytes": size,
                "sha256": actual_sha,
                "category": cat,
                "status": item["status"],
                "freeze_mutable": bool(item.get("freeze_mutable")),
            }
        )

    manifest_payload = {
        "dest_root": str(dest_root),
        "total_files": len(compact_files),
        "total_files_bytes": total_bytes,
        "max_bundle_bytes": max_bundle_bytes,
        "files": compact_files,
    }
    manifest_json_bytes_data = json.dumps(
        manifest_payload, separators=(",", ":")
    ).encode("utf-8")
    manifest_json_bytes = len(manifest_json_bytes_data)
    total_staged_bytes = total_bytes + manifest_json_bytes
    over_budget = total_staged_bytes > max_bundle_bytes

    raw_handoff = manifest_dict.get("handoff_source")
    handoff_path = (
        Path(raw_handoff)
        if isinstance(raw_handoff, str) and raw_handoff.strip()
        else (LAB / "neon" / "filter_quest" / "HANDOFF_12H_DATA_QUALITY.md")
    )
    freeze_info = check_freeze_state(handoff_path, pending_entries)

    return {
        "schema_errors": schema_errors,
        "schema_error_count": len(schema_errors),
        "dup_dest_rel": dup_dest_rel,
        "dup_source": dup_source,
        "total_manifest": len(files),
        "present_files": len(copy_sources),
        "matched": matched,
        "changed": changed,
        "immutable_mismatch": immutable_mismatch,
        "missing": missing,
        "pending_sibling": pending_sibling,
        "pending_freeze": pending_freeze,
        "forbidden_ext": forbidden_ext,
        "forbidden_path": forbidden_path,
        "forbidden_words": forbidden_words,
        "json_invalid": json_invalid,
        "total_bytes": total_bytes,
        "manifest_json_bytes": manifest_json_bytes,
        "manifest_json_bytes_data": manifest_json_bytes_data,
        "total_staged_bytes": total_staged_bytes,
        "max_bundle_bytes": max_bundle_bytes,
        "over_budget": over_budget,
        "cat_counts": dict(sorted(cat_counts.items())),
        "cat_bytes": dict(sorted(cat_bytes.items())),
        "origin_counts": dict(sorted(origin_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "copy_sources": copy_sources,
        "freeze_info": freeze_info,
        "file_lines": file_lines,
    }


def print_freeze_summary(freeze_info: dict[str, Any]) -> None:
    if freeze_info["freeze_ok"]:
        print("FREEZE_CHECK: FROZEN (0 open markers, 0 banned words in HANDOFF, pending_until_freeze valid)")
        return
    hits = freeze_info["marker_hits"]
    bhits = freeze_info["handoff_banned_hits"]
    issues = freeze_info["pending_freeze_issues"]
    print(
        f"FREEZE_CHECK: UNFROZEN (handoff_missing={freeze_info['handoff_missing']}, "
        f"marker_hits={len(hits)}, handoff_banned_hits={len(bhits)}, pending_freeze_issues={len(issues)})"
    )
    for hit in hits:
        print(f"  - HANDOFF line {hit['line']}: {hit['marker']} | {hit['line_preview']}")
    for bhit in bhits:
        print(f"  - HANDOFF banned word line {bhit['line']}: {bhit['word']} | {bhit['line_preview']}")
    for iss in issues:
        print(f"  - {iss}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Stage verified Wave 11 curated text-only deliverables into "
            "C:\\nnue-lab\\teamwork\\ (defaults to --dry-run)."
        )
    )
    mode_grp = ap.add_mutually_exclusive_group()
    mode_grp.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview staging without touching C:\\nnue-lab\\teamwork\\ (default).",
    )
    mode_grp.add_argument(
        "--verify-manifest",
        action="store_true",
        help="Verify manifest schema, uniqueness, SHA-256s, forbidden rules, living JSONs, and 4.0 MiB budget.",
    )
    mode_grp.add_argument(
        "--check-freeze",
        action="store_true",
        help="Check whether HANDOFF_12H_DATA_QUALITY.md and pending_freeze targets are frozen for --live.",
    )
    mode_grp.add_argument(
        "--live",
        action="store_true",
        help=(
            "Enable live copy ONLY when BOTH --confirm-quest-complete YES_COPY_TO_TEAMWORK "
            "AND --check-freeze passes with 0 missing/pending/errors."
        ),
    )
    ap.add_argument(
        "--confirm-quest-complete",
        type=str,
        default="",
        help=f"Required exact confirmation token for --live: {CONFIRM_TOKEN}",
    )
    ap.add_argument(
        "--require-siblings",
        action="store_true",
        help="Fail --dry-run / --verify-manifest if any Wave 11 sibling deliverable is absent.",
    )
    ap.add_argument(
        "--dest",
        type=str,
        default=str(DEFAULT_DEST),
        help="Destination staging directory inside C:\\nnue-lab\\teamwork\\.",
    )
    ap.add_argument(
        "--manifest",
        type=str,
        default=str(DEFAULT_MANIFEST),
        help="Path to DELIVERY_MANIFEST_W11.json.",
    )
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: Manifest file not found: {manifest_path}", file=sys.stderr)
        return 2 if args.live else 1

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Failed to parse manifest JSON {manifest_path}: {exc}", file=sys.stderr)
        return 2 if args.live else 1

    raw_dest = args.dest.strip() if isinstance(args.dest, str) else ""
    if not raw_dest:
        manifest_dest = manifest.get("default_dest") if isinstance(manifest, dict) else None
        raw_dest = (
            manifest_dest.strip()
            if isinstance(manifest_dest, str) and manifest_dest.strip()
            else str(DEFAULT_DEST)
        )
    dest_root = Path(raw_dest)

    if args.live and args.confirm_quest_complete != CONFIRM_TOKEN:
        print(
            f"REFUSED: --live requires exact --confirm-quest-complete {CONFIRM_TOKEN}. "
            "Zero directories created; zero files touched.",
            file=sys.stderr,
        )
        return 2

    verbose_files = not (args.verify_manifest or args.check_freeze)
    res = inspect_bundle(manifest, dest_root, verbose_files=verbose_files)
    freeze_info = res["freeze_info"]

    if args.live:
        if res["schema_error_count"] > 0:
            print(
                f"REFUSED: Manifest schema errors ({res['schema_error_count']}): "
                f"{res['schema_errors']}. Zero directories created; zero files touched.",
                file=sys.stderr,
            )
            return 2
        if not freeze_info["freeze_ok"]:
            print(
                f"REFUSED: Quest is not frozen yet "
                f"(handoff_missing={freeze_info['handoff_missing']}, "
                f"marker_hits={len(freeze_info['marker_hits'])}, "
                f"handoff_banned_hits={len(freeze_info['handoff_banned_hits'])}, "
                f"pending_freeze_issues={len(freeze_info['pending_freeze_issues'])}). "
                "Zero directories created; zero files touched.",
                file=sys.stderr,
            )
            print_freeze_summary(freeze_info)
            return 2
        if (
            res["dup_dest_rel"] > 0
            or res["dup_source"] > 0
            or res["missing"] > 0
            or res["pending_sibling"] > 0
            or res["pending_freeze"] > 0
            or res["immutable_mismatch"] > 0
            or res["forbidden_ext"] > 0
            or res["forbidden_path"] > 0
            or res["forbidden_words"] > 0
            or res["json_invalid"] > 0
            or res["over_budget"]
        ):
            print(
                f"REFUSED: missing={res['missing']}, pending_sibling={res['pending_sibling']}, "
                f"pending_freeze={res['pending_freeze']}, immutable_mismatch={res['immutable_mismatch']}, "
                f"dup_dest_rel={res['dup_dest_rel']}, dup_source={res['dup_source']}, "
                f"forbidden_ext={res['forbidden_ext']}, forbidden_path={res['forbidden_path']}, "
                f"forbidden_words={res['forbidden_words']}, json_invalid={res['json_invalid']}, "
                f"total_bytes={res['total_bytes']}+{res['manifest_json_bytes']}={res['total_staged_bytes']} "
                f"(cap={res['max_bundle_bytes']}). Zero directories created; zero files touched.",
                file=sys.stderr,
            )
            return 2

        resolved_dest_root = dest_root.resolve()
        resolved_copy_plan: list[tuple[Path, Path]] = []
        for src_p, dest_rel in res["copy_sources"]:
            if not is_safe_dest_rel(dest_rel):
                print(
                    f"REFUSED: Unsafe dest_rel {dest_rel!r}. "
                    "Zero directories created; zero files touched.",
                    file=sys.stderr,
                )
                return 2
            dst = dest_root / dest_rel
            try:
                in_dest = dst.resolve().is_relative_to(resolved_dest_root)
            except (OSError, ValueError):
                in_dest = False
            if not in_dest:
                print(
                    f"REFUSED: dest_rel {dest_rel!r} resolves outside {resolved_dest_root}. "
                    "Zero directories created; zero files touched.",
                    file=sys.stderr,
                )
                return 2
            resolved_copy_plan.append((src_p, dst))

        dest_root.mkdir(parents=True, exist_ok=True)
        for src_p, dst in resolved_copy_plan:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_p, dst)
        (dest_root / "MANIFEST_SHA256.json").write_bytes(res["manifest_json_bytes_data"])
        print(
            f"LIVE_COPY_COMPLETE: copied {len(res['copy_sources'])} files + MANIFEST_SHA256.json "
            f"({res['total_bytes']}+{res['manifest_json_bytes']}={res['total_staged_bytes']} B) into {dest_root}"
        )
        return 0

    if args.check_freeze:
        print("STAGE_MODE: CHECK_FREEZE (read-only)")
        print(f"MANIFEST  : {manifest_path}")
        print(f"DEST_ROOT : {dest_root}")
        print_freeze_summary(freeze_info)
        for ln in res["file_lines"]:
            print(ln)
        freeze_pass = (
            freeze_info["freeze_ok"]
            and res["schema_error_count"] == 0
            and res["dup_dest_rel"] == 0
            and res["dup_source"] == 0
            and res["missing"] == 0
            and res["pending_sibling"] == 0
            and res["pending_freeze"] == 0
            and res["immutable_mismatch"] == 0
            and res["forbidden_ext"] == 0
            and res["forbidden_path"] == 0
            and res["forbidden_words"] == 0
            and res["json_invalid"] == 0
            and not res["over_budget"]
        )
        print(
            f"CHECK_FREEZE_SUMMARY: freeze_ok={freeze_info['freeze_ok']} | "
            f"marker_hits={len(freeze_info['marker_hits'])} | "
            f"handoff_banned_hits={len(freeze_info['handoff_banned_hits'])} | "
            f"pending_freeze={res['pending_freeze']} | pending_sibling={res['pending_sibling']} | "
            f"missing={res['missing']} | immutable_mismatch={res['immutable_mismatch']} | "
            f"forbidden_ext={res['forbidden_ext']} | forbidden_path={res['forbidden_path']} | "
            f"forbidden_words={res['forbidden_words']} | json_invalid={res['json_invalid']} | "
            f"total_bytes={res['total_bytes']}+{res['manifest_json_bytes']}={res['total_staged_bytes']}/{res['max_bundle_bytes']} | "
            f"status={'PASS' if freeze_pass else 'BLOCKED'}"
        )
        return 0 if freeze_pass else 1

    if args.verify_manifest:
        print("STAGE_MODE: VERIFY_MANIFEST (read-only)")
        print(f"MANIFEST  : {manifest_path}")
        schema_ver = manifest.get("schema_version") if isinstance(manifest, dict) else None
        wave_val = manifest.get("wave") if isinstance(manifest, dict) else None
        print(f"SCHEMA    : version={schema_ver} | wave={wave_val} | errors={res['schema_error_count']}")
        for err in res["schema_errors"]:
            print(f"  [SCHEMA_ERROR] {err}", file=sys.stderr)
        print(
            f"UNIQUENESS: total_entries={res['total_manifest']} | dup_dest_rel={res['dup_dest_rel']} | dup_source={res['dup_source']}"
        )
        print(f"ORIGINS   : {res['origin_counts']}")
        print(f"STATUSES  : {res['status_counts']}")
        print("CATEGORIES:")
        for cat in sorted(res["cat_counts"].keys()):
            print(f"  - {cat}: {res['cat_counts'][cat]} files, {res['cat_bytes'][cat]} B")
        print_freeze_summary(freeze_info)
        for ln in res["file_lines"]:
            print(ln)
        ok = (
            res["schema_error_count"] == 0
            and res["dup_dest_rel"] == 0
            and res["dup_source"] == 0
            and res["missing"] == 0
            and res["immutable_mismatch"] == 0
            and res["forbidden_ext"] == 0
            and res["forbidden_path"] == 0
            and res["forbidden_words"] == 0
            and res["json_invalid"] == 0
            and not res["over_budget"]
            and (not args.require_siblings or res["pending_sibling"] == 0)
        )
        print(
            f"VERIFY_MANIFEST_SUMMARY: total={res['total_manifest']} | present={res['present_files']} | "
            f"matched={res['matched']} | changed={res['changed']} | immutable_mismatch={res['immutable_mismatch']} | "
            f"missing={res['missing']} | pending_sibling={res['pending_sibling']} | pending_freeze={res['pending_freeze']} | "
            f"forbidden_ext={res['forbidden_ext']} | forbidden_path={res['forbidden_path']} | "
            f"forbidden_words={res['forbidden_words']} | json_invalid={res['json_invalid']} | "
            f"total_bytes={res['total_bytes']}+{res['manifest_json_bytes']}={res['total_staged_bytes']}/{res['max_bundle_bytes']} | "
            f"status={'PASS' if ok else 'FAIL'}"
        )
        return 0 if ok else 1

    # Default: --dry-run
    print("STAGE_MODE: DRY_RUN (read-only, C:\\nnue-lab\\teamwork\\ untouched)")
    print(f"MANIFEST  : {manifest_path}")
    print(f"DEST_ROOT : {dest_root}")
    print_freeze_summary(freeze_info)
    for err in res["schema_errors"]:
        print(f"[SCHEMA_ERROR] {err}", file=sys.stderr)
    for ln in res["file_lines"]:
        print(ln)
    ok = (
        res["schema_error_count"] == 0
        and res["dup_dest_rel"] == 0
        and res["dup_source"] == 0
        and res["missing"] == 0
        and res["immutable_mismatch"] == 0
        and res["forbidden_ext"] == 0
        and res["forbidden_path"] == 0
        and res["forbidden_words"] == 0
        and res["json_invalid"] == 0
        and not res["over_budget"]
        and (not args.require_siblings or res["pending_sibling"] == 0)
    )
    print(
        f"\nDRY_RUN_SUMMARY: total={res['total_manifest']} | present={res['present_files']} | "
        f"matched={res['matched']} | changed={res['changed']} | immutable_mismatch={res['immutable_mismatch']} | "
        f"missing={res['missing']} | pending_sibling={res['pending_sibling']} | pending_freeze={res['pending_freeze']} | "
        f"schema_errors={res['schema_error_count']} | dup_dest_rel={res['dup_dest_rel']} | dup_source={res['dup_source']} | "
        f"forbidden_ext={res['forbidden_ext']} | forbidden_path={res['forbidden_path']} | "
        f"forbidden_words={res['forbidden_words']} | json_invalid={res['json_invalid']} | "
        f"total_bytes={res['total_bytes']}+{res['manifest_json_bytes']}={res['total_staged_bytes']}/{res['max_bundle_bytes']}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
