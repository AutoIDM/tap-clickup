"""ClickUp tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_clickup.streams import (
    ClickUpStream,
    TeamsStream,
    GroupsStream,
)
STREAM_TYPES = [
    TeamsStream,
]


class TapClickUp(Tap):
    """ClickUp tap class."""
    name = "tap-clickup"

    config_jsonschema = th.PropertiesList(
        th.Property("api_token", th.StringType, required=True),
        th.Property("team_ids", th.ArrayType(th.StringType), required=True),
        th.Property("start_date", th.DateTimeType),
        #th.Property("api_url", th.StringType, default="https://api.clickup.com/api/v2"),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
