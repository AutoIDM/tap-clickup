"""Stream type classes for tap-clickup."""
from pathlib import Path
from typing import Optional, Any
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
    # Optionally, you may also use `schema_filepath` in place of `schema`:
    schema_filepath = SCHEMAS_DIR / "team.json"
    records_jsonpath = "$.teams[*]"

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "team_id": record["id"],
        }


class SpacesStream(ClickUpStream):
    """Spaces"""

    name = "space"
    path = "/team/{team_id}/space"
    primary_keys = ["id"]
    replication_key = None
    # Optionally, you may also use `schema_filepath` in place of `schema`:
    schema_filepath = SCHEMAS_DIR / "space.json"
    records_jsonpath = "$.spaces[*]"
    parent_stream_type = TeamsStream

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

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "list_id": record["id"],
        }


class ListsStream(ClickUpStream):
    """Lists"""

    name = "list"
    path = "/folder/{folder_id}/list"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "list.json"
    records_jsonpath = "$.lists[*]"
    parent_stream_type = FoldersStream

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
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "tag.json"
    records_jsonpath = "$.tags[*]"
    parent_stream_type = SpacesStream


class SharedHierarchyStream(ClickUpStream):
    """SharedHierarchy"""

    name = "shared_hierarchy"
    path = "/team/{team_id}/shared"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "shared.json"
    records_jsonpath = "$.shared"
    parent_stream_type = TeamsStream


class FolderlessTasksStream(ClickUpStream):
    """Tasks can come from lists not under folders"""

    name = "folderless_task"
    path = "/list/{list_id}/task"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "task.json"
    records_jsonpath = "$.tasks[*]"
    parent_stream_type = FolderlessListsStream

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return the page number, Null if we should stop going to the next page."""
        self.logger.info(f"Previous Token: {previous_token}")
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


class FolderTasksStream(ClickUpStream):
    """Tasks can come from under Folders"""

    name = "folder_task"
    path = "/list/{list_id}/task"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "task.json"
    records_jsonpath = "$.tasks[*]"
    parent_stream_type = FolderListsStream

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return the page number, Null if we should stop going to the next page."""
        self.logger.info(f"Previous Token: {previous_token}")
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


class CustomFieldsStream(ClickUpStream):
    """CustomField"""

    name = "custom_field"
    path = "/list/{list_id}/field"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "custom_field.json"
    records_jsonpath = "$.fields[*]"
    parent_stream_type = FolderlessListsStream
