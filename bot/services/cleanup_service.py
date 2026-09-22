"""
Conservative project cleanup reporting for the /condemned admin command.

This module intentionally has a very small deletion allowlist.  It can only
remove generated Python __pycache__ directories inside the project.  Source
files, databases, manifests, configuration, assets, archives, and all
runtime modules are report-only and are never automatic cleanup candidates.
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("kingdom_treasury")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_FILENAME = "kingdom_treasury.db"

# These directories are dependencies/build products, not project source.
# They are excluded from the report so the command never proposes touching
# the environment that runs the bot.
_SCAN_EXCLUDED_PARTS = frozenset({
    ".git",
    ".pythonlibs",
    ".cache",
    ".upm",
    "node_modules",
    "dist",
})

PROTECTED_SYSTEMS = (
    "Économie, DevilCoins, soldes, trésorerie et transactions",
    "Données utilisateurs, inventaires, investissements et missions",
    "Base SQLite, schéma, migrations et sauvegardes",
    "Permissions Discord, rôles et commandes administratives",
    "Configuration, variables d’environnement et token Discord",
    "Cooldowns, anti-abus, Cerberus, ledger et tâches automatiques",
    "Dashboard/API, synchronisation des guildes et fichiers générés",
)

VOLUNTARILY_KEPT = (
    "archive/ : versions historiques documentées pour référence ou retour arrière",
    "artifacts/ et lib/ : dashboard, API, contrats et code généré actifs",
    "attached_assets/ : fichiers fournis par l’utilisateur, conservés par prudence",
    "bot/ et main.py : runtime Discord et systèmes critiques",
    "kingdom_treasury.db, manifests, lockfiles et configuration",
)


@dataclass(frozen=True)
class CleanupCandidate:
    relative_path: str
    category: str
    reason: str
    confidence: str = "CERTAIN"


@dataclass(frozen=True)
class CleanupReport:
    generated_at: str
    report_id: str
    candidates: tuple[CleanupCandidate, ...]
    command_count: int
    cog_count: int
    protected_systems: tuple[str, ...] = PROTECTED_SYSTEMS
    voluntarily_kept: tuple[str, ...] = VOLUNTARILY_KEPT

    def text(self) -> str:
        candidate_lines = (
            "\n".join(
                f"- [{item.confidence}] {item.relative_path} — "
                f"{item.category}: {item.reason}"
                for item in self.candidates
            )
            or "- Aucun fichier source ou élément métier certain."
        )
        return "\n".join(
            [
                "KINGDOM TREASURY — RAPPORT /CONDEMNED",
                f"Rapport : {self.report_id}",
                f"Généré : {self.generated_at}",
                "",
                "SYSTÈMES CRITIQUES DÉTECTÉS ET PROTÉGÉS",
                *[f"- {item}" for item in self.protected_systems],
                "",
                f"RÉFÉRENCE CROISÉE : {self.cog_count} cogs enregistrés, "
                f"{self.command_count} commandes app_commands détectées.",
                "",
                "CANDIDATS CERTAINS (ALLOWLIST STRICTE)",
                candidate_lines,
                "",
                "ÉLÉMENTS CONSERVÉS VOLONTAIREMENT",
                *[f"- {item}" for item in self.voluntarily_kept],
                "",
                "Règle appliquée : l’incertitude conserve l’élément. "
                "Aucune base de données ou donnée utilisateur n’est modifiée.",
            ]
        )


@dataclass(frozen=True)
class CleanupResult:
    report_before: CleanupReport
    report_after: CleanupReport
    removed: tuple[str, ...] = ()
    backup_status: str = "Aucune sauvegarde nécessaire en mode rapport."
    error: str | None = None

    def text(self) -> str:
        removed_lines = "\n".join(f"- {item}" for item in self.removed) or "- Aucun élément supprimé."
        return "\n".join(
            [
                self.report_after.text(),
                "",
                "RÉSULTAT DE L’EXÉCUTION",
                f"Sauvegarde : {self.backup_status}",
                "Éléments supprimés :",
                removed_lines,
                f"Erreur : {self.error}" if self.error else "Erreur : aucune",
            ]
        )


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _is_project_cache(path: Path) -> bool:
    try:
        relative_parts = path.relative_to(PROJECT_ROOT).parts
    except ValueError:
        return False
    return (
        path.name == "__pycache__"
        and not any(part in _SCAN_EXCLUDED_PARTS for part in relative_parts)
        and not path.is_symlink()
        and path.is_dir()
    )


def _count_registered_commands() -> tuple[int, int]:
    """Count source registrations without importing or executing bot code."""
    command_count = 0
    cog_count = 0

    for source_path in sorted((PROJECT_ROOT / "bot" / "cogs").glob("*.py")):
        try:
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "command"
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "app_commands"
                ):
                    command_count += 1

    bot_path = PROJECT_ROOT / "bot" / "bot.py"
    try:
        tree = ast.parse(bot_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Await)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "add_cog"
            ):
                cog_count += 1
    except (OSError, SyntaxError):
        pass

    return command_count, cog_count


def build_cleanup_report() -> CleanupReport:
    """Build a report without importing the bot or touching persistent data."""
    cache_paths: list[Path] = []
    root_cache = PROJECT_ROOT / "__pycache__"
    if _is_project_cache(root_cache):
        cache_paths.append(root_cache)
    bot_root = PROJECT_ROOT / "bot"
    if bot_root.is_dir():
        for current_root, directories, _ in os.walk(bot_root, topdown=True):
            directories[:] = [
                name for name in directories
                if name not in _SCAN_EXCLUDED_PARTS
            ]
            current_path = Path(current_root)
            cache_path = current_path / "__pycache__"
            if _is_project_cache(cache_path):
                cache_paths.append(cache_path)

    candidates = tuple(
        CleanupCandidate(
            relative_path=_relative(path),
            category="cache généré",
            reason="__pycache__ ne contient pas de source et peut être recréé.",
        )
        for path in sorted(cache_paths)
    )
    command_count, cog_count = _count_registered_commands()
    generated_at = datetime.now(timezone.utc).isoformat()
    fingerprint_payload = {
        "candidates": [item.relative_path for item in candidates],
        "commands": command_count,
        "cogs": cog_count,
    }
    report_id = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    return CleanupReport(
        generated_at=generated_at,
        report_id=report_id,
        candidates=candidates,
        command_count=command_count,
        cog_count=cog_count,
    )


def _backup_root() -> Path:
    configured = os.environ.get("CONDEMNED_BACKUP_DIR", "").strip()
    root = Path(configured).expanduser().resolve() if configured else (
        PROJECT_ROOT.parent / ".kingdom-treasury-condemned-backups"
    ).resolve()
    if root == PROJECT_ROOT or PROJECT_ROOT in root.parents:
        raise ValueError("Le dossier de sauvegarde doit être hors du projet.")
    return root


def _backup_database(destination: Path) -> str:
    database_path = PROJECT_ROOT / DATABASE_FILENAME
    if not database_path.exists():
        return "Base SQLite absente (aucune copie nécessaire)."

    backup_path = destination / DATABASE_FILENAME
    source = sqlite3.connect(str(database_path))
    target = sqlite3.connect(str(backup_path))
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close()
        source.close()

    check = sqlite3.connect(str(backup_path))
    try:
        integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        check.close()
    if integrity != "ok":
        raise RuntimeError("La vérification de la copie SQLite a échoué.")
    return f"copie SQLite vérifiée ({backup_path.name})."


def _create_backup() -> str:
    """Create a best-effort backup without including secrets or untracked files."""
    destination = _backup_root() / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination.mkdir(parents=True, exist_ok=False)
    archive_path = destination / "project-tracked.tar"
    result = subprocess.run(
        ["git", "archive", "--format=tar", "--output", str(archive_path), "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not archive_path.exists() or archive_path.stat().st_size == 0:
        raise RuntimeError("La sauvegarde Git du projet a échoué.")

    database_status = _backup_database(destination)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tracked_project_archive": archive_path.name,
        "database": DATABASE_FILENAME,
        "database_status": database_status,
        "note": "git archive ne contient pas les fichiers non suivis.",
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return f"archive Git et {database_status}"


def _validate_candidate(path: Path) -> bool:
    """Keep deletion restricted to the fixed generated-cache allowlist."""
    return _is_project_cache(path) and path.resolve().parent.exists()


def run_cleanup(confirm: bool = False) -> CleanupResult:
    """
    Report by default.  With explicit confirmation, back up first and remove
    only the currently re-scanned generated-cache candidates.
    """
    before = build_cleanup_report()
    if not confirm:
        return CleanupResult(report_before=before, report_after=before)
    if not before.candidates:
        return CleanupResult(
            report_before=before,
            report_after=before,
            backup_status="Aucune sauvegarde nécessaire : aucun candidat certain.",
        )

    try:
        backup_status = _create_backup()
    except Exception as exc:
        logger.exception("Condemned cleanup aborted because backup failed.")
        return CleanupResult(
            report_before=before,
            report_after=before,
            backup_status="Échec de sauvegarde — aucune suppression effectuée.",
            error=str(exc),
        )

    fresh = build_cleanup_report()
    removed: list[str] = []
    for candidate in fresh.candidates:
        candidate_path = PROJECT_ROOT / candidate.relative_path
        if not _validate_candidate(candidate_path):
            continue
        try:
            shutil.rmtree(candidate_path)
            removed.append(candidate.relative_path)
        except OSError as exc:
            logger.warning("Could not remove generated cache %s: %s", candidate.relative_path, exc)

    after = build_cleanup_report()
    logger.info(
        "Condemned cleanup completed: report=%s removed=%d remaining=%d",
        before.report_id,
        len(removed),
        len(after.candidates),
    )
    return CleanupResult(
        report_before=before,
        report_after=after,
        removed=tuple(removed),
        backup_status=backup_status,
    )