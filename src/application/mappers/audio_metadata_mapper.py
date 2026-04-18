from src.domain.models.audio_metadata import AudioMetadata
from src.domain.models.playlist_metadata import PlaylistMetadata
from src.infrastructure.persistence.orm_models import AudioMetadataORM


class AudioMetadataMapper:

    @staticmethod
    def to_orm(
        audio: AudioMetadata,
        playlist: PlaylistMetadata = None,
    ) -> AudioMetadataORM:
        return AudioMetadataORM(
            id               = audio.id,
            title            = audio.title,
            file_name        = audio.file_name,
            file_path        = audio.file_path,
            playlist_id      = playlist.id if playlist else None,
            channel_name     = audio.channel_name,
            channel_url      = audio.channel_url,
            duration_seconds = audio.duration_seconds,
            upload_date      = audio.upload_date,
            description      = audio.description,
            thumbnail_url    = audio.thumbnail_url,
            language         = audio.language,
            tags             = ",".join(audio.tags) if audio.tags else None,
            downloaded_at    = audio.downloaded_at,
        )
