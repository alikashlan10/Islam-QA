from enum import Enum

class IngestStatus(str, Enum):
    SUCCESS  = "success"
    SKIPPED  = "skipped"
    FAILED   = "failed"