from src.api.schemas.jobs import JobProgress
from src.infrastructure.persistence.orm_models import JobORM   # or ORM if you skip domain mapping

class JobMapper:

    @staticmethod
    def to_response(job : JobORM) -> JobProgress:
        return JobProgress(
            id=job.id,
            type=job.type,
            status=job.status,
            total=job.total,
            success=job.success,
            failed=job.failed,
            skipped=job.skipped,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )