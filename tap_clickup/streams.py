"""Stream type classes for tap-clickup."""
from pathlib import Path
from typing import Optional, Any, Dict, Iterable
import requests
from singer_sdk.helpers.jsonpath import extract_jsonpath
from tap_clickup.client import ClickUpStream
import yaml #added to read information specifying spaces and workspaces

# Load the YAML config file from meltano
with open("meltano.yml", "r") as yaml_file:
    cu_config = yaml.safe_load(yaml_file)

#funcions to read the extra configuration data from the YAML file
#read and split lists to create list
def extract_and_convert_list(config, key):
    value = config.get(key, "")
    if value:
        split_values = value.split(',')
        return [int(item) for item in split_values]
    return []

#specify which setting from which tap to read the config.info from ISSUE HERE the yaml read is hardcoded so breaks when i have multiple "tap-clickup" one for each env that i want to switch between
def find_tap_clickup_config(plugins):
    for plugin in plugins:
        if plugin.get("name") == "tap-clickup":
            return plugin.get("config", {})
    return {}

# Find the tap-clickup configuration
tap_clickup_config = find_tap_clickup_config(cu_config["plugins"]["extractors"])

# Extract and convert workspace ID
cu_workspace = tap_clickup_config.get("workspace_id")

# Extract and convert spaces and lists into lists
spaces_id_list = extract_and_convert_list(tap_clickup_config, "spaces_id")
lists_id_list = extract_and_convert_list(tap_clickup_config, "list_ids")

workteamid = cu_workspace  # store workspace id E.g:30979640  
space_ids = spaces_id_list # store list of spaces to be fetched E.g: [90100432266,90100432289,90100437857]
list_ids = lists_id_list #store lists of  lists to be fetched E.g: [900101856869,901002404954]

# Check if there's only one value in the list, this is necessary because of a bug on click up's API. 
if len(list_ids) == 1:
    # Duplicate the value to ensure at least two parameters due to a bug on clickups API (the values returned by the API are NOT duplicated)
    list_ids.append(list_ids[0])
if len(space_ids) == 1:
    # Duplicate the value to ensure at least two parameters due to a bug on clickups API (the values returned by the API are NOT duplicated)
    space_ids.append(space_ids[0])    


SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class TeamsStream(ClickUpStream):
    """Teams"""

    name = "team"
    path = "/team"
    primary_keys = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "team.json"
    # Necessary because if you have access to multiple workteams, the responses are replicated N times where N = # of worspaces you have access to
    records_jsonpath = f"$.teams[?(@.id == {workteamid})]" 
    

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "team_id": record["id"],
        }

    def get_records(self, context: Optional[dict]) -> Iterable[dict]:
        """Return a generator of row-type dictionary objects."""
        # If workspace_ids is empty, null, or nonexistant, default to using the API to
        # determine all workspaces/teams.
        if "workspace_ids" in self.config and self.config.get("workspace_ids"):
            return [{"id": id} for id in self.config.get("workspace_ids")]
        else:
            return super().get_records(context=context)



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
    basepath = "/team/{team_id}/task"
    space_ids_param = "&space_ids=" + "&space_ids=".join(map(str, space_ids)) if space_ids else "" #Dinamically create the spaces path to be passed on API call
    list_ids_param = "?list_ids=" + "&list_ids=".join(map(str, list_ids)) if list_ids else "" #Dinamically create the spaces path to be passed on API call
    # Necessary because if you pass list and space, lists MUST go first in the parameter string
    if list_ids_param:
        path = f"{basepath}{list_ids_param}{space_ids_param}"
    else:
        path = f"{basepath}?{space_ids_param}"
   
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

        # If list_ids is empty, null, or nonexistant, default to using the API to
        if "list_ids" in self.config and self.config.get("list_ids"):
            params["list_ids"] = [item for item in self.config.get("list_ids")]

        # If space_ids is empty, null, or nonexistant, default to using the API to
        if "space_ids" in self.config and self.config.get("space_ids"):
            params["space_ids"] = [item for item in self.config.get("space_ids")]

        if "list_ids" in params and len(params["list_ids"]) == 1:
            # To work around the ClickUp API bug that returns an error message stating 
            # "List ids must be an array" (ECODE: OAUTH_042), we should duplicate the list_id
            # when there is only one, as the API requires an array format for list IDs.
            params["list_ids"].append(params["list_ids"][0])

        if "space_ids" in params and len(params["space_ids"]) == 1:
            # To work around the ClickUp API bug that returns an error message stating 
            # "Space ids must be an array" (ECODE: OAUTH_042), we should duplicate the space_id
            # when there is only one, as the API requires an array format for space IDs.
            params["space_ids"].append(params["space_ids"][0])

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