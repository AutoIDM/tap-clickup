"""Stream type classes for tap-clickup."""
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable
from singer_sdk import typing as th  # JSON Schema typing helpers
from tap_clickup.client import ClickUpStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class TeamsStream(ClickUpStream):
    """Define custom stream."""
    name = "team"
    path = "/team"
    primary_keys = ["id"]
    replication_key = None
    # Optionally, you may also use `schema_filepath` in place of `schema`:
    schema_filepath = SCHEMAS_DIR / "team.json"
    records_jsonpath = "$.teams[*]"


class GroupsStream(ClickUpStream):
    """Define custom stream."""
    name = "groups"
    path = "/groups"
    primary_keys = ["id"]
    replication_key = "modified"
    schema = th.PropertiesList(
        th.Property("name", th.StringType),
        th.Property("id", th.StringType),
        th.Property("modified", th.DateTimeType),
    ).to_dict()
