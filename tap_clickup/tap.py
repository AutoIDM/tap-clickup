"""ClickUp tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th

from tap_clickup.streams import (
    TeamsStream,
    SpacesStream,
    FoldersStream,
    FolderListsStream,
    FolderlessListsStream,
    TaskTemplatesStream,
    GoalsStream,
    TagsStream,
    SharedHierarchyStream,
    TasksStream,
    FolderCustomFieldsStream,
    FolderlessCustomFieldsStream,
    TimeEntries,
)

STREAM_TYPES = [
    TeamsStream,
    SpacesStream,
    FoldersStream,
    FolderListsStream,
    FolderlessListsStream,
    TaskTemplatesStream,
    GoalsStream,
    TagsStream,
    SharedHierarchyStream,
    TasksStream,
    FolderCustomFieldsStream,
    FolderlessCustomFieldsStream,
    TimeEntries,
]


class TapClickUp(Tap):
    """ClickUp tap class."""

    name = "tap-clickup"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_token", th.StringType, required=True, description="Example: 'pk_12345"
        ),
        # Removing "official" start_date support re https://github.com/AutoIDM/tap-clickup/issues/118
        #        th.Property(
        #            "start_date",
        #            th.StringType,
        #            description="""We recommended to leave this null as state will handle the
        #            tasks start date for you and get all the streams that support incremental
        #            on the first run. start_date officially only supports RFC 3339. But
        #           you can get away with anything Pendulum.parse can handle.
        #            See https://pendulum.eustace.io/docs/.
        #            Examples 2019-10-12T07:20:50.52Z 2022-04-01
        #            """,
        #        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
