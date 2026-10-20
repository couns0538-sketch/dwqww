#!/usr/bin/env python3
"""Stream all hosted evidence into a verified ZIP or fixed-size raw ZIP parts.

Only output files are written. Concatenate parts in manifest order to recover the
original ZIP. Each input file is stored below ``files/`` and ``manifest.json``
inside the ZIP records its byte size and SHA256. The adjacent manifest also
records the complete ZIP and every physical output file's size and SHA256.
"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile


DEFAULT_SPLIT_SIZE = 64 * 1024 * 1024
COPY_SIZE = 1024 * 1024
MANIFEST_MEMBER = "manifest.json"


class _SplitWriter:
    """An unseekable ZIP sink that never creates an oversized physical file."""

    def __init__(self, directory, name, split_size):
        self.directory = directory
        self.name = name
        self.split_size = split_size
        self.size = 0
        self.digest = hashlib.sha256()
        self.parts = []
        self._open_part()

    def _open_part(self):
        self.part_size = 0
        self.part_digest = hashlib.sha256()
        self.part_name = f"{self.name}.zip.part{len(self.parts) + 1:04d}"
        self.stream = (self.directory / self.part_name).open("xb")

    def _close_part(self):
        self.stream.close()
        self.parts.append({"file": self.part_name, "size": self.part_size,
                           "sha256": self.part_digest.hexdigest()})

    def write(self, data):
        view = memoryview(data)
        length = len(view)
        while view:
            if self.part_size == self.split_size:
                self._close_part()
                self._open_part()
            block = view[:self.split_size - self.part_size]
            self.stream.write(block)
            self.digest.update(block)
            self.part_digest.update(block)
            self.size += len(block)
            self.part_size += len(block)
            view = view[len(block):]
        return length

    def tell(self):
        return self.size

    def seek(self, *args):
        raise io.UnsupportedOperation("streaming archive")

    def flush(self):
        self.stream.flush()

    def finish(self):
        self._close_part()
        if len(self.parts) == 1:
            name = f"{self.name}.zip"
            (self.directory / self.parts[0]["file"]).rename(self.directory / name)
            self.parts[0]["file"] = name

    def close(self):
        self.stream.close()


def _json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def _input_files(root):
    result = []
    for directory, directories, filenames in os.walk(root, followlinks=False):
        directories.sort()
        for name in directories:
            if (Path(directory) / name).is_symlink():
                raise ValueError(f"Symlinked input directory cannot be archived: {name}")
        for name in sorted(filenames):
            path = Path(directory) / name
            if not path.is_file():
                raise ValueError(f"Input is not a regular file: {path}")
            result.append((path.relative_to(root).as_posix(), path))
    return sorted(result)


def archive_results(input_dir, out_dir, name, split_size=DEFAULT_SPLIT_SIZE):
    """Return the external manifest path after archiving without modifying input."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise ValueError("Archive name must be a single safe filename component")
    if isinstance(split_size, bool) or not isinstance(split_size, int) or split_size < 1:
        raise ValueError("Split size must be a positive integer")
    root = Path(input_dir).resolve(strict=True)
    output = Path(out_dir).resolve()
    if not root.is_dir():
        raise ValueError("Input must be a directory")
    if output == root or root in output.parents:
        raise ValueError("Output must not be inside the input directory")
    inputs = _input_files(root)
    output.mkdir(parents=True, exist_ok=True)
    manifest_name = f"{name}.manifest.json"
    if ((output / manifest_name).exists() or (output / f"{name}.zip").exists()
            or any(output.glob(f"{name}.zip.part*"))):
        raise FileExistsError(f"Archive outputs already exist for {name}")
    with tempfile.TemporaryDirectory(prefix=f".{name}.", dir=output) as temporary:
        stage = Path(temporary)
        sink = _SplitWriter(stage, name, split_size)
        entries = []
        try:
            with zipfile.ZipFile(sink, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=6, allowZip64=True) as archive:
                for relative, path in inputs:
                    digest = hashlib.sha256()
                    size = 0
                    with path.open("rb") as source:
                        before = os.fstat(source.fileno())
                        with archive.open(f"files/{relative}", "w", force_zip64=True) as target:
                            while True:
                                block = source.read(COPY_SIZE)
                                if not block:
                                    break
                                target.write(block)
                                digest.update(block)
                                size += len(block)
                        after = os.fstat(source.fileno())
                    if ((before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                            != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                            or size != before.st_size):
                        raise ValueError(f"Input changed while being archived: {relative}")
                    entries.append({"path": relative, "size": size, "sha256": digest.hexdigest()})
                archive.writestr(MANIFEST_MEMBER, _json_bytes({"schema_version": 1, "files": entries}))
            sink.finish()
        finally:
            sink.close()
        manifest = {"schema_version": 1, "format": "raw-split-zip",
                    "archive": {"file": f"{name}.zip", "size": sink.size,
                                "sha256": sink.digest.hexdigest()},
                    "split_size": split_size, "parts": sink.parts,
                    "manifest_member": MANIFEST_MEMBER, "files": entries}
        (stage / manifest_name).write_bytes(_json_bytes(manifest))
        # Publish the manifest last: its presence means all parts are available.
        for record in sink.parts:
            (stage / record["file"]).rename(output / record["file"])
        (stage / manifest_name).rename(output / manifest_name)
    return output / manifest_name


def verify_archive(manifest_path):
    """Stream hashes, reassemble on disk, and verify every ZIP payload byte."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256()
    size = 0
    with tempfile.TemporaryFile() as combined:
        for record in manifest["parts"]:
            filename = record["file"]
            if Path(filename).name != filename or filename in (".", ".."):
                raise ValueError("Unsafe archive part filename")
            part_digest = hashlib.sha256()
            part_size = 0
            with (manifest_path.parent / filename).open("rb") as source:
                while True:
                    block = source.read(COPY_SIZE)
                    if not block:
                        break
                    combined.write(block)
                    part_digest.update(block)
                    digest.update(block)
                    part_size += len(block)
                    size += len(block)
            if part_size != record["size"] or part_digest.hexdigest() != record["sha256"]:
                raise ValueError(f"Archive part integrity failure: {filename}")
        if size != manifest["archive"]["size"] or digest.hexdigest() != manifest["archive"]["sha256"]:
            raise ValueError("Complete archive integrity failure")
        combined.seek(0)
        with zipfile.ZipFile(combined) as archive:
            internal = json.loads(archive.read(MANIFEST_MEMBER))
            if internal != {"schema_version": 1, "files": manifest["files"]}:
                raise ValueError("Internal and external file manifests disagree")
            expected = [MANIFEST_MEMBER] + [f"files/{row['path']}" for row in internal["files"]]
            if sorted(archive.namelist()) != sorted(expected) or len(set(expected)) != len(expected):
                raise ValueError("Unexpected or duplicate archive members")
            for row in internal["files"]:
                file_digest = hashlib.sha256()
                file_size = 0
                with archive.open(f"files/{row['path']}") as source:
                    while True:
                        block = source.read(COPY_SIZE)
                        if not block:
                            break
                        file_digest.update(block)
                        file_size += len(block)
                if file_size != row["size"] or file_digest.hexdigest() != row["sha256"]:
                    raise ValueError(f"Input file integrity failure: {row['path']}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--split-size", type=int, default=DEFAULT_SPLIT_SIZE,
                        help="raw ZIP part size in bytes (default: 64 MiB)")
    args = parser.parse_args()
    try:
        manifest = archive_results(args.input, args.out, args.name, args.split_size)
        verify_archive(manifest)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"archive_results: {error}\n")
    print(manifest)


if __name__ == "__main__":
    main()
