from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime,
    Text, ForeignKey , UUID , Integer , 
)
from sqlalchemy.orm import relationship, DeclarativeBase


## Base

class Base(DeclarativeBase):
    pass


## ORM Models 

class PlaylistORM(Base):
    __tablename__ = "playlists"

    id           = Column(String,   primary_key=True)   # YouTube playlist ID
    title        = Column(String,   nullable=False)
    channel_name = Column(String,   nullable=True)
    channel_url  = Column(String,   nullable=True)

    # one playlist → many audio files
    audio_files  = relationship("AudioMetadataORM", back_populates="playlist")

    def __repr__(self):
        return f"<Playlist id={self.id} title={self.title}>"



class AudioMetadataORM(Base):
    __tablename__ = "audio_metadata"

    id               = Column(String,  primary_key=True)   # YouTube video ID
    title            = Column(String,  nullable=False)
    file_name        = Column(String,  nullable=False)
    file_path        = Column(String,  nullable=False)

    # source info
    playlist_id      = Column(String,  ForeignKey("playlists.id"), nullable=True)
    channel_name     = Column(String,  nullable=True)
    channel_url      = Column(String,  nullable=True)

    # video metadata
    duration_seconds = Column(Float,   nullable=True)
    upload_date      = Column(DateTime(timezone=True), nullable=True)
    description      = Column(Text,    nullable=True)
    thumbnail_url    = Column(String,  nullable=True)
    language         = Column(String,  nullable=True)
    tags             = Column(Text,    nullable=True)   # stored as comma-separated string

    # pipeline tracking
    downloaded_at    = Column(DateTime(timezone=True), nullable=False,
                              default=lambda: datetime.now(timezone.utc))
   

    # relationships
    playlist         = relationship("PlaylistORM",    back_populates="audio_files")
    transcript       = relationship(
        "TranscriptORM",
        back_populates="audio",
        uselist=False  # one-to-one
    )

    def __repr__(self):
        return f"<AudioMetadata id={self.id} title={self.title}>"



class TranscriptORM(Base):
    __tablename__ = "transcripts"

    id        = Column(String,  primary_key=True)
    video_id  = Column(String,  ForeignKey("audio_metadata.id"), nullable=False, unique=True)
    full_text = Column(Text,    nullable=False)
    language  = Column(String,  nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # ✅ moved here
    embedded = Column(Boolean, nullable=False, default=False)

    # relationships
    audio = relationship("AudioMetadataORM", back_populates="transcript")

    def __repr__(self):
        return f"<Transcript id={self.id} video_id={self.video_id}>"


class JobORM(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    type   = Column(String, nullable=False)
    status = Column(String, nullable=False)

    total   = Column(Integer, nullable=True)
    success = Column(Integer, nullable=False, default=0)
    failed  = Column(Integer, nullable=False, default=0)
    skipped = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))