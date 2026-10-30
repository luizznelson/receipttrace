"""Verify that the wheel contains every checksummed public demo asset."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def check(directory: Path) -> None:
    wheels = list(directory.glob("*.whl"))
    if len(wheels) != 1:
        raise ValueError("Expected exactly one wheel in the output directory")
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
        prefix = "receipttrace/webdata/"
        checksums = json.loads(archive.read(prefix + "checksums.json"))
        for name, expected in checksums.items():
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError("Invalid demo asset path")
            value = archive.read(prefix + name)
            if hashlib.sha256(value).hexdigest() != expected:
                raise ValueError("Wheel asset checksum mismatch")
        for name in (
            "app.js",
            "api.js",
            "i18n.js",
            "ui.js",
            "index.html",
            "styles.css",
            "upload.js",
            "upload-client.js",
        ):
            if "receipttrace/static/" + name not in names:
                raise ValueError("Frontend file missing from wheel")
        if prefix + "ATTRIBUTION.md" not in names:
            raise ValueError("Public data attribution missing from wheel")
        if any(name.endswith((".env", ".sqlite3")) for name in names):
            raise ValueError("Local credentials or review storage included in wheel")
    print(f"Wheel verified: {len(checksums)} demo assets and frontend files included.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    check(parser.parse_args().directory)
