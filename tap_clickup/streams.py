"""Stream type classes for tap-clickup."""
from pathlib import Path
from typing import Optional, Any, Dict
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
    # TODO not clear why this is needed
    partitions = None


class SpacesStream(ClickUpStream):
    """Spaces"""

    name = "space"
    path = "/team/{team_id}/space"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "space.json"
    records_jsonpath = "$.spaces[*]"
    parent_stream_type = TeamsStream
    partitions = []

    @property
    def base_partition(self):
        return [{"archived": "true"}, {"archived": "false"}]

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
    partitions = []

    @property
    def base_partition(self):
        return [{"archived": "true"}, {"archived": "false"}]

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
    partitions = []

    @property
    def base_partition(self):
        return [{"archived": "true"}, {"archived": "false"}]

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
    partitions = []

    @property
    def base_partition(self):
        return [{"archived": "true"}, {"archived": "false"}]

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
    # TODO not clear why this is needed
    partitions = None


class GoalsStream(ClickUpStream):
    """Goals"""

    name = "goal"
    path = "/team/{team_id}/goal"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "goal.json"
    records_jsonpath = "$.goals[*]"
    parent_stream_type = TeamsStream
    # TODO not clear why this is needed
    partitions = None


class TagsStream(ClickUpStream):
    """Tags"""

    name = "tag"
    path = "/space/{space_id}/tag"
    primary_keys = ["name"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "tag.json"
    records_jsonpath = "$.tags[*]"
    # TODO not clear why this is needed
    partitions = None
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
    # TODO not clear why this is needed
    partitions = None


class FolderlessCustomFieldsStream(ClickUpStream):
    """CustomField from folderless lists"""

    name = "folderless_customfield"
    path = "/list/{list_id}/field"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "custom_field.json"
    records_jsonpath = "$.fields[*]"
    parent_stream_type = FolderlessListsStream
    # TODO not clear why this is needed
    partitions = None


class FolderCustomFieldsStream(ClickUpStream):
    """CustomFields from foldered lists"""

    name = "folder_customfield"
    path = "/list/{list_id}/field"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "custom_field.json"
    records_jsonpath = "$.fields[*]"
    parent_stream_type = FolderListsStream
    # TODO not clear why this is needed
    partitions = None


class TasksStream(ClickUpStream):
    """Tasks Stream"""

    name = "task"
    # Date_updated_gt is greater than or equal to not just greater than
    path = "/team/{team_id}/task"
    primary_keys = ["id"]
    replication_key = "date_updated"
    is_sorted = True
    # ignore_parent_replication_key = True
    schema_filepath = SCHEMAS_DIR / "task.json"
    records_jsonpath = "$.tasks[*]"
    parent_stream_type = TeamsStream

    # Need this stub as a hack on _sync to force it to use Partitions
    # Since this is a child stream we want each team_id to create a request for
    # archived:true and archived:false. And we want state to track properly
    partitions = []

    @property
    def base_partition(self):
        return [{"archived": "true"}, {"archived": "false"}]

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params = super().get_url_params(context, next_page_token)
        params["archived"] = context["archived"]
        params["include_closed"] = "true"
        params["subtasks"] = "true"
        params["order_by"] = "updated"
        params["reverse"] = "true"
        params["date_updated_gt"] = self.get_starting_replication_key_value(context)
        return params

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
