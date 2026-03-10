from enum import Enum

class ChunkingStrategy(str, Enum):
    RECURSIVE = "recursive"
    TOKEN     = "token"
    SENTENCE  = "sentence"