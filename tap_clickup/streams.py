"""Stream type classes for tap-clickup."""
from pathlib import Path
from typing import Optional, Any, Dict, cast
import datetime
import pendulum
import requests
from singer_sdk.helpers.jsonpath import extract_jsonpath
from tap_clickup.client import ClickUpStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class TeamsStream(ClickUpStream):
    """Teams"""

    name = "team"
    path = "/team"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "team.json"
    records_jsonpath = "$.teams[*]"

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "team_id": record["id"],
        }


class TimeEntries(ClickUpStream):
    """Time Entries"""

    name = "time_entries"
    path = "/team/{team_id}/time_entries"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "time_entries.json"
    records_jsonpath = "$.data[*]"
    parent_stream_type = TeamsStream


class SpacesStream(ClickUpStream):
    """Spaces"""

    name = "space"
    path = "/team/{team_id}/space"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "space.json"
    records_jsonpath = "$.spaces[*]"
    parent_stream_type = TeamsStream
    partitions = [{"archived": "true"}, {"archived": "false"}]

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "space_id": record["id"],
        }


class FoldersStream(ClickUpStream):
    """Folders"""

    name = "folder"
    path = "/space/{space_id}/folder"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "folder.json"
    records_jsonpath = "$.folders[*]"
    parent_stream_type = SpacesStream
    partitions = [{"archived": "true"}, {"archived": "false"}]

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "folder_id": record["id"],
        }


class FolderListsStream(ClickUpStream):
    """Lists"""

    name = "folder_list"
    path = "/folder/{folder_id}/list"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "list.json"
    records_jsonpath = "$.lists[*]"
    parent_stream_type = FoldersStream
    partitions = [{"archived": "true"}, {"archived": "false"}]

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "list_id": record["id"],
        }


class FolderlessListsStream(ClickUpStream):
    """Folderless Lists"""

    name = "folderless_list"
    path = "/space/{space_id}/list"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "list.json"
    records_jsonpath = "$.lists[*]"
    parent_stream_type = SpacesStream
    partitions = [{"archived": "true"}, {"archived": "false"}]

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "list_id": record["id"],
        }


class TaskTemplatesStream(ClickUpStream):
    """TaskTemplates"""

    name = "task_template"
    path = "/team/{team_id}/task_template?page=0"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "task_template.json"
    records_jsonpath = "$.templates[*]"
    parent_stream_type = TeamsStream


class GoalsStream(ClickUpStream):
    """Goals"""

    name = "goal"
    path = "/team/{team_id}/goal"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "goal.json"
    records_jsonpath = "$.goals[*]"
    parent_stream_type = TeamsStream


class TagsStream(ClickUpStream):
    """Tags"""

    name = "tag"
    path = "/space/{space_id}/tag"
    primary_keys = ["name"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "tag.json"
    records_jsonpath = "$.tags[*]"
    parent_stream_type = SpacesStream


class SharedHierarchyStream(ClickUpStream):
    """SharedHierarchy"""

    name = "shared_hierarchy"
    path = "/team/{team_id}/shared"
    primary_keys = []
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "shared.json"
    records_jsonpath = "$.shared"
    parent_stream_type = TeamsStream


class FolderlessCustomFieldsStream(ClickUpStream):
    """CustomField from folderless lists"""

    name = "folderless_customfield"
    path = "/list/{list_id}/field"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "custom_field.json"
    records_jsonpath = "$.fields[*]"
    parent_stream_type = FolderlessListsStream


class FolderCustomFieldsStream(ClickUpStream):
    """CustomFields from foldered lists"""

    name = "folder_customfield"
    path = "/list/{list_id}/field"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "custom_field.json"
    records_jsonpath = "$.fields[*]"
    parent_stream_type = FolderListsStream


class TasksStream(ClickUpStream):
    """Tasks Stream"""

    name = "task"
    # Date_updated_gt is greater than or equal to not just greater than
    path = "/team/{team_id}/task?include_closed=true&subtasks=true"
    primary_keys = ["id"]
    # replication_key = "date_updated"
    # is_sorted = True
    # ignore_parent_replication_key = True
    schema_filepath = SCHEMAS_DIR / "task.json"
    records_jsonpath = "$.tasks[*]"
    parent_stream_type = TeamsStream
    partitions = [{"archived": "true"}, {"archived": "false"}]

    initial_replication_key_dict = {}

    def initial_replication_key(self, context) -> int:
        path = self.get_url(context) + context.get("archived")
        key_cache: Optional[int] = self.initial_replication_key_dict.get(path, None)
        if key_cache is None:
            key_cache = self.get_starting_replication_key_value(context)
            self.initial_replication_key_dict[path] = key_cache
        assert key_cache is not None
        return key_cache

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params = super().get_url_params(context, next_page_token)
        params["order_by"] = "updated"
        params["reverse"] = "true"
        params["date_updated_gt"] = 0
        return params

    def get_starting_replication_key_value(
        self, context: Optional[dict]
    ) -> Optional[int]:
        """Return starting replication key value."""
        if self.replication_key:
            state = self.get_context_state(context)
            replication_key_value = state.get("replication_key_value")
            if replication_key_value and self.replication_key == state.get(
                "replication_key"
            ):
                return replication_key_value
            if "start_date" in self.config:
                datetime_startdate = cast(
                    datetime.datetime, pendulum.parse(self.config["start_date"])
                )
                startdate_seconds_after_epoch = int(
                    datetime_startdate.replace(tzinfo=datetime.timezone.utc).timestamp()
                )
                return startdate_seconds_after_epoch
            else:
                self.logger.info(
                    """Setting replication value to 0 as there wasn't a
                    start_date provided in the config."""
                )
                return 0
        return None

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return the page number, Null if we should stop going to the next page."""
        newtoken = None
        recordcount = 0
        if previous_token is None:
            previous_token = 0

        for _ in extract_jsonpath(self.records_jsonpath, input=response.json()):
            recordcount = recordcount + 1

        # I wonder if a better approach is to just check for 0 records and stop
        # For now I'll follow the docs verbatium
        # From the api docs, https://clickup.com/api.
        # you should check list limit against the length of each response
        # to determine if you are on the last page.
        if recordcount == 100:
            newtoken = previous_token + 1
        else:
            newtoken = None

        return newtoken
