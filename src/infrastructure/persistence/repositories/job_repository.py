from typing import Optional
from sqlalchemy import update

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.orm_models import JobORM
from src.logger.logger import setup_logger

logger = setup_logger(__name__)


class JobRepository:

    def create(self, job: JobORM) -> JobORM:
        with get_db() as db:
            db.add(job)
            db.flush()   # ensures ID is generated
            logger.info(f"Job created: {job.id}")
            return job

    def get_by_id(self, job_id: str) -> Optional[JobORM]:
        with get_db() as db:
            return db.get(JobORM, job_id)

    # ── Generic update (core method) ───────────────────────────────

    def update(self, job_id: str, **fields) -> None:
        """
        Generic update method.
        Example:
            update(job_id, status="running", total=100)
        """
        if not fields:
            return

        with get_db() as db:
            result = (
                db.query(JobORM)
                .filter(JobORM.id == job_id)
                .update(fields)
            )

            if result == 0:
                logger.warning(f"Job not found for update: {job_id}")
            else:
                logger.info(f"Job updated: {job_id} → {fields}")

    # ── Atomic increments (important for Celery) ───────────────────

    def increment_success(self, job_id: str, count: int = 1) -> None:
        self._increment_field(job_id, JobORM.success, count)

    def increment_failed(self, job_id: str, count: int = 1) -> None:
        self._increment_field(job_id, JobORM.failed, count)

    def increment_skipped(self, job_id: str, count: int = 1) -> None:
        self._increment_field(job_id, JobORM.skipped, count)

    def _increment_field(self, job_id: str, field, count: int) -> None:
        with get_db() as db:
            result = (
                db.query(JobORM)
                .filter(JobORM.id == job_id)
                .update({field: field + count})
            )

            if result == 0:
                logger.warning(f"Job not found for increment: {job_id}")

    # ── Convenience helpers (optional but clean) ───────────────────

    def set_total(self, job_id: str, total: int) -> None:
        self.update(job_id, total=total)

    def set_status(self, job_id: str, status: str) -> None:
        self.update(job_id, status=status)