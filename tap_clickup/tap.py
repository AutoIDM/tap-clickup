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
        th.Property("api_token", th.StringType, required=True),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
