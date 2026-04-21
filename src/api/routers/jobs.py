from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID

from src.infrastructure.persistence.repositories.job_repository import JobRepository
from src.infrastructure.celery.tasks.ingest_video_task import ingest_video_task
from src.infrastructure.celery.tasks.ingest_playlist_task import ingest_playlist_task
from src.api.schemas.jobs import JobResponse , IngestPlaylistRequest , IngestVideoRequest , EmbedRequest , JobProgress
from src.infrastructure.persistence.orm_models import JobORM
from src.application.mappers.job_mapper import JobMapper

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def get_job_repo():
    return JobRepository()


@router.post("/playlist",response_model=JobResponse)
def create_playlist(request:IngestPlaylistRequest , job_repo:JobRepository = Depends(get_job_repo)):

    # define new job
    job = JobORM(
        status = "pending",
        type = "ingest_playlist"
    )

    # create new job (DB)
    job = job_repo.create(job=job)

    # append to celery
    ingest_playlist_task.delay(request.playlist_url , job.id , request.limit)

    return JobResponse(
        job_id=job.id,
        status=job.status , 
        type = job.type
    )



@router.get("/{job_id}" , response_model= JobProgress)
def get_job_progress(job_id : UUID , job_repo : JobRepository = Depends(get_job_repo)):

    # get jobORM
    job = job_repo.get_by_id(job_id=job_id)

    if job :
        # map to response schema (JobProgress)
        return JobMapper.to_response(job=job)
    else :
        raise HTTPException(status_code=404, detail="Job not found")


