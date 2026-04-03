from src.domain.models.playlist_metadata import PlaylistMetadata
from src.infrastructure.persistence.orm_models import PlaylistORM


class PlaylistMapper:

    @staticmethod
    def to_orm(playlist: PlaylistMetadata) -> PlaylistORM:
        return PlaylistORM(
            id           = playlist.id,
            title        = playlist.title,
            channel_name = playlist.channel_name,
            channel_url  = playlist.channel_url,
        )
