"""ClickUp tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th

import singer_sdk.helpers._typing

def patched_is_boolean_type(property_schema: dict) -> bool | None:
    """Return true if the JSON Schema type is a boolean or None if detection fails.

    Without this patch, is_boolean_type() will return true for schemas that contain
    non-boolean types, which causes values to be coerced to booleans.

    For example, without this patch, a field with a value of `"abc"` and a jsonschema
    type of `["boolean", "string"]` would cause this function to return `True`. Then the
    SDK's _conform_primitive_property() would coerce `"abc"` to boolean, resulting in
    that field's value being `True`.

    See: https://github.com/MeltanoLabs/tap-universal-file/issues/59
    """
    if "anyOf" not in property_schema and "type" not in property_schema:
        return None  # Could not detect data type
    for property_type in property_schema.get("anyOf", [property_schema.get("type")]):
        schema_type = (
            property_type.get("type", [])
            if isinstance(property_type, dict)
            else property_type
        )
        if schema_type == "boolean" or (
            "boolean" in schema_type
            and (
                len(schema_type) == 1
                or ("null" in schema_type and len(schema_type) == 2)  # noqa: PLR2004
            )
        ):
            return True
    return False


singer_sdk.helpers._typing.is_boolean_type = patched_is_boolean_type  # noqa: SLF001

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
        th.Property(
            "workspace_ids", th.ArrayType(th.IntegerType), required=False, description="Example: '[20214542]'" # fetches the data for workspace_id
        ),
        th.Property(
            "space_ids", th.ArrayType(th.IntegerType), required=False, description="Example: '[45215477, 4547547]'" # fetches the data for workspace_id
        ),
        th.Property(
            "list_ids", th.ArrayType(th.IntegerType), required=False, description="Example: '[454455478, 784552187]'" # fetches the data for workspace_id
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
