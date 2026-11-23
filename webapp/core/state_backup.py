"""R2 snapshot/restore for SQLite files on the ephemeral Container filesystem.

The snapshot is a single gzip tar object. It includes Django's SQLite database and
workspace-isolated OpenOutFind databases. Upload happens after mutating HTTP requests;
startup restores the last complete object before migrations run.
"""
from __future__ import annotations

import io
import os
import sqlite3
import tarfile
import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from django.conf import settings


def _data_dir() -> Path:
    path = Path(settings.ACQUISITION_DATA_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _client():
    required = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        return None
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def _object_key() -> str:
    return os.environ.get("R2_STATE_OBJECT_KEY", "acquisition-agent/state.tar.gz")


def _sqlite_files() -> list[Path]:
    root = _data_dir()
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.suffix in {".sqlite3", ".sqlite", ".db"}
    )


def restore() -> bool:
    """Restore latest archive if configured. Returns False when no snapshot exists."""
    client = _client()
    if client is None:
        print("R2 snapshot storage is not configured; using container-local SQLite.")
        return False

    try:
        response = client.get_object(Bucket=os.environ["R2_BUCKET_NAME"], Key=_object_key())
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in {"NoSuchKey", "404", "NotFound"}:
            print("No prior SQLite snapshot found in R2; starting with an empty data directory.")
            return False
        raise

    root = _data_dir().resolve()
    body = response["Body"]
    try:
        with tarfile.open(fileobj=body, mode="r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                destination = (root / member.name).resolve()
                if root not in destination.parents:
                    raise ValueError("Unsafe path in R2 SQLite snapshot.")
                destination.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    continue
                with destination.open("wb") as output:
                    output.write(source.read())
    finally:
        body.close()
    print("Restored SQLite snapshot from R2.")
    return True


def backup() -> bool:
    """Checkpoint SQLite WAL files and atomically replace the R2 snapshot object."""
    client = _client()
    if client is None:
        print("R2 snapshot storage is not configured; SQLite changes remain container-local.")
        return False

    root = _data_dir()
    files = _sqlite_files()
    for path in files:
        connection = sqlite3.connect(str(path), timeout=30)
        try:
            result = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            if result and result[0] != 0:
                raise RuntimeError(f"SQLite WAL checkpoint is busy: {path}")
        finally:
            connection.close()

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for path in files:
            archive.add(path, arcname=path.relative_to(root).as_posix())
    buffer.seek(0)
    client.put_object(
        Bucket=os.environ["R2_BUCKET_NAME"],
        Key=_object_key(),
        Body=buffer.getvalue(),
        ContentType="application/gzip",
        Metadata={"sqlite-file-count": str(len(files))},
    )
    print(f"Saved {len(files)} SQLite database file(s) to R2.")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("restore", "backup"))
    action = parser.parse_args().action
    if action == "restore":
        restore()
    else:
        backup()
