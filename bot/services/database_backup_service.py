"""Verified, private backups of Kingdom Treasury's SQLite database."""

import asyncio
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class DatabaseBackupService:
    def __init__(self, database_path: str | Path, backup_root: Optional[str | Path] = None):
        self.database_path = Path(database_path).expanduser().resolve()
        project_root = Path(__file__).resolve().parents[2]
        configured_root = (
            os.environ.get("KINGDOM_TREASURY_BACKUP_DIR", "").strip()
            or os.environ.get("CONDEMNED_BACKUP_DIR", "").strip()
        )
        if backup_root is not None:
            self.backup_root = Path(backup_root).expanduser().resolve()
        elif configured_root:
            self.backup_root = Path(configured_root).expanduser().resolve()
        else:
            self.backup_root = project_root.parent / ".kingdom-treasury-condemned-backups"

        if self.backup_root == project_root or project_root in self.backup_root.parents:
            raise ValueError("Database backups must be stored outside the project directory.")

    async def create_verified_backup(self) -> Path:
        return await asyncio.to_thread(self._create_verified_backup)

    def _create_verified_backup(self) -> Path:
        if not self.database_path.is_file():
            raise FileNotFoundError(f"Economy database not found: {self.database_path}")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        destination = self.backup_root / f"reset-backup-{timestamp}"
        destination.mkdir(parents=True, mode=0o700)
        destination.chmod(0o700)
        backup_path = destination / self.database_path.name
        temporary_path = destination / f".{self.database_path.name}.tmp"

        try:
            source = sqlite3.connect(str(self.database_path), timeout=30)
            target = sqlite3.connect(str(temporary_path), timeout=30)
            try:
                integrity = source.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    raise RuntimeError("Source SQLite database failed its integrity check.")
                source.backup(target)
                target.commit()
            finally:
                target.close()
                source.close()

            check = sqlite3.connect(str(temporary_path), timeout=30)
            try:
                integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
            finally:
                check.close()
            if integrity != "ok":
                raise RuntimeError("SQLite backup failed its integrity check.")

            os.replace(temporary_path, backup_path)
            backup_path.chmod(0o600)
            return backup_path
        except Exception:
            if temporary_path.exists():
                temporary_path.unlink()
            if destination.exists() and not any(destination.iterdir()):
                destination.rmdir()
            raise
