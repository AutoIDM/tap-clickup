"""Stream type classes for tap-clickup."""
from pathlib import Path
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
