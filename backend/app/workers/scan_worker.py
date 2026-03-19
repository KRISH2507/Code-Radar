"""
Scan Worker

Executes repository analysis as a background job.
Can run via Celery (when Redis is available) or in a plain daemon thread.

Flow
----
1. Create Scan record  (status=running)
2. Load repository     (clone or unzip)
3. Analyse files       (analyser.py)
4. Persist FileMetrics + Issues in bulk
5. Compute health score
6. Update Scan + Repository  (status=completed / failed)
"""

import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.repository import Repository, RepositoryStatus
from app.models.scan import Scan, ScanStatus
from app.models.issue import Issue
from app.models.file_metrics import FileMetrics

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core synchronous implementation
# ---------------------------------------------------------------------------

def _scan_repository_impl(repository_id: int) -> Dict[str, Any]:
    """
    End-to-end scan.  Called synchronously from either Celery or a thread.
    All DB interaction uses a local session that is always closed in finally.
    """
    db = SessionLocal()
    repo_path: Optional[str] = None
    scan: Optional[Scan] = None

    try:
        # ------------------------------------------------------------------ #
        # 1. Fetch repository record
        # ------------------------------------------------------------------ #
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        if not repo:
            logger.error("[WORKER] Repository %s not found", repository_id)
            return {"status": "error", "message": f"Repository {repository_id} not found"}

        # ------------------------------------------------------------------ #
        # 2. Create Scan record  (idempotent: reuse an existing PENDING one)
        # ------------------------------------------------------------------ #
        scan = (
            db.query(Scan)
            .filter(Scan.repository_id == repository_id, Scan.status == ScanStatus.PENDING)
            .order_by(Scan.created_at.desc())
            .first()
        )
        if scan is None:
            scan = Scan(repository_id=repository_id)
            db.add(scan)
            db.flush()

        scan.status     = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)

        repo.status = RepositoryStatus.PROCESSING
        db.commit()
        db.refresh(scan)

        logger.info("[WORKER] Scan %s started for repo '%s' (id=%s)",
                    scan.id, repo.name, repository_id)

        # ------------------------------------------------------------------ #
        # 3. Load repository files
        # ------------------------------------------------------------------ #
        from app.services.repo_loader import RepoLoader, RepoLoaderError
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            if repo.source_type.value == "github":
                loader_result = loop.run_until_complete(
                    RepoLoader.clone_github_repo(repo.repo_url)
                )
            else:
                loader_result = loop.run_until_complete(
                    RepoLoader.extract_zip_file(repo.repo_url)
                )
        finally:
            loop.close()

        repo_path = loader_result["repo_path"]
        logger.info("[WORKER] Repo loaded at %s", repo_path)

        # ------------------------------------------------------------------ #
        # 4. Static analysis
        # ------------------------------------------------------------------ #
        from app.services.analyzer import analyze_repository
        analysis = analyze_repository(repo_path)

        total_files    = analysis["total_files"]
        total_lines    = analysis["total_lines"]
        language_stats = analysis["language_stats"]
        file_results   = analysis["file_results"]
        raw_issues     = analysis["all_issues"]

        logger.info(
            "[WORKER] Analysis done: %d files, %d lines, %d issues",
            total_files, total_lines, len(raw_issues),
        )

        # ------------------------------------------------------------------ #
        # 5. Bulk-insert FileMetrics
        # ------------------------------------------------------------------ #
        fm_rows = [
            FileMetrics(
                scan_id=scan.id,
                repository_id=repository_id,
                file_path=fr.file_path,
                language=fr.language,
                total_lines=fr.total_lines,
                code_lines=fr.code_lines,
                blank_lines=fr.blank_lines,
                comment_lines=fr.comment_lines,
                complexity_score=fr.complexity_score,
            )
            for fr in file_results
        ]
        if fm_rows:
            db.bulk_save_objects(fm_rows)
            db.flush()

        # ------------------------------------------------------------------ #
        # 6. Bulk-insert Issues
        # ------------------------------------------------------------------ #
        issue_rows = [
            Issue(
                scan_id=scan.id,
                repository_id=repository_id,
                severity=issue.severity,
                issue_type=issue.issue_type,
                file_path=issue.file_path,
                line_number=issue.line_number,
                message=issue.message,
                rule=issue.rule,
            )
            for issue in raw_issues
        ]
        if issue_rows:
            db.bulk_save_objects(issue_rows)
            db.flush()

        # ------------------------------------------------------------------ #
        # 7. Compute health score + severity counts
        # ------------------------------------------------------------------ #
        sev_count: Dict[str, int] = {
            "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0
        }
        for issue in raw_issues:
            sev_count[issue.severity] = sev_count.get(issue.severity, 0) + 1

        from app.services.scoring import calculate_health_score
        health_score = calculate_health_score(
            critical=sev_count["critical"],
            high=sev_count["high"],
            medium=sev_count["medium"],
            low=sev_count["low"],
            info=sev_count["info"],
        )
        # Defensive: ensure health_score is always a finite float in [0, 100]
        try:
            health_score = float(health_score)
            if health_score != health_score:  # NaN check
                health_score = 0.0
        except (TypeError, ValueError):
            health_score = 0.0
        health_score = max(0.0, min(100.0, health_score))

        # ------------------------------------------------------------------ #
        # 8. Persist results
        # ------------------------------------------------------------------ #
        scan.status         = ScanStatus.COMPLETED
        scan.completed_at   = datetime.now(timezone.utc)
        scan.total_files    = total_files
        scan.total_lines    = total_lines
        scan.health_score   = health_score
        scan.language_stats = language_stats
        scan.critical_count = sev_count["critical"]
        scan.high_count     = sev_count["high"]
        scan.medium_count   = sev_count["medium"]
        scan.low_count      = sev_count["low"]
        scan.info_count     = sev_count["info"]

        repo.status        = RepositoryStatus.COMPLETED
        repo.completed_at  = datetime.now(timezone.utc)
        repo.file_count    = total_files
        repo.line_count    = total_lines
        repo.health_score  = health_score

        db.commit()

        logger.info(
            "[WORKER] Scan %s completed. Score=%.1f | C=%d H=%d M=%d L=%d I=%d",
            scan.id, health_score,
            sev_count["critical"], sev_count["high"],
            sev_count["medium"], sev_count["low"], sev_count["info"],
        )

        return {
            "status":        "success",
            "scan_id":       scan.id,
            "repository_id": repository_id,
            "health_score":  health_score,
            "total_files":   total_files,
            "total_lines":   total_lines,
            **sev_count,
        }

    except Exception as exc:
        tb = traceback.format_exc()
        logger.error("[WORKER] Scan failed for repo %s: %s\n%s", repository_id, exc, tb)

        try:
            if scan is not None:
                scan.status        = ScanStatus.FAILED
                scan.completed_at  = datetime.now(timezone.utc)
                scan.error_message = str(exc)[:2000]

            # Re-query repo in case session is dirty
            repo = db.query(Repository).filter(Repository.id == repository_id).first()
            if repo:
                repo.status = RepositoryStatus.FAILED

            db.commit()
        except Exception as commit_err:
            logger.error("[WORKER] Could not persist failure state: %s", commit_err)
            try:
                db.rollback()
            except Exception:
                pass

        return {
            "status":       "error",
            "repository_id": repository_id,
            "message":      str(exc),
        }

    finally:
        if repo_path:
            try:
                from app.services.repo_loader import RepoLoader
                RepoLoader.cleanup_repository(repo_path)
            except Exception as cleanup_err:
                logger.warning("[WORKER] Cleanup failed for %s: %s", repo_path, cleanup_err)
        try:
            db.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Celery task registration
# ---------------------------------------------------------------------------

def _celery_scan_task(self, repository_id: int) -> Dict[str, Any]:
    logger.info("[CELERY] Task %s started for repo %s", self.request.id, repository_id)
    return _scan_repository_impl(repository_id)


if celery_app is not None:
    scan_repository = celery_app.task(
        bind=True,
        name="scan_repository",
        max_retries=2,
        default_retry_delay=30,
    )(_celery_scan_task)
else:
    class _FallbackTask:
        def delay(self, repository_id: int):
            raise RuntimeError("Celery not available")

        def __call__(self, repository_id: int) -> Dict[str, Any]:
            return _scan_repository_impl(repository_id)

    scan_repository = _FallbackTask()
