from typing import Callable, List, Type
from singer_sdk.tap_base import Tap
import datetime
import os
import responses
import json
import pytest
from pathlib import Path

from tap_clickup.tap import TapClickUp

SAMPLE_CONFIG = {
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    "api_token": os.environ["TAP_CLICKUP_API_TOKEN"],
}


def test_default_incremental():
    """Return callable pytest which executes simple discovery and connection tests."""
    # Initialize with basic config
    tap1: Tap = TapClickUp(config=SAMPLE_CONFIG, parse_env_config=True)
    # Test discovery
    tap1.run_discovery()
    catalog1 = tap1.catalog_dict
    task_catalog = [
        taskmetadata
        for taskmetadata in catalog1["streams"]
        if taskmetadata.get("tap_stream_id") == "task"
    ][0]
    assert task_catalog["replication_method"] == "INCREMENTAL"


# Setup 1 api call, state should be set to one date, from start_date, then the state returned should be the latest data set
team_response = """
{
    "teams": [
        {
            "id": "18011725",
            "name": "AutoIDM Workspace",
            "color": "#536cfe",
            "avatar": null,
            "members": [
                {
                    "user": {
                        "id": 30025034,
                        "username": "Derek Visch",
                        "email": "dvisch@autoidm.com",
                        "color": "#d60800",
                        "profilePicture": null,
                        "initials": "DV",
                        "role": 1,
                        "custom_role": null,
                        "last_active": "1650328664978",
                        "date_joined": "1629300591704",
                        "date_invited": "1629300591704"
                    }
                }
            ]
        },
        {
            "id": "18011726",
            "name": "AutoIDM Workspace",
            "color": "#536cfe",
            "avatar": null,
            "members": [
                {
                    "user": {
                        "id": 30025034,
                        "username": "Derek Visch",
                        "email": "dvisch@autoidm.com",
                        "color": "#d60800",
                        "profilePicture": null,
                        "initials": "DV",
                        "role": 1,
                        "custom_role": null,
                        "last_active": "1650328664978",
                        "date_joined": "1629300591704",
                        "date_invited": "1629300591704"
                    }
                }
            ]
        }
        ]
}
        """


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


def test_state_properly_stored(mocked_responses):
    task_response_json = ""
    with open(Path(__file__).parent / Path("task.json")) as task:
        task_response_json = task.read()
    archived_task_response = ""
    with open(Path(__file__).parent / Path("archived_task.json")) as task:
        archived_task_response = task.read()
    task_response_json_two = ""
    with open(Path(__file__).parent / Path("task_two.json")) as task:
        task_response_json_two = task.read()
    archived_task_response_two = ""
    with open(Path(__file__).parent / Path("archived_task_two.json")) as task:
        archived_task_response_two = task.read()
    mocked_responses.add(
        responses.GET,
        "https://api.clickup.com/api/v2/team",
        body=team_response,
        status=200,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        "https://api.clickup.com/api/v2/team/18011725/task?include_closed=true&subtasks=true&archived=true&order_by=updated&reverse=true&date_updated_gt=0",
        body=archived_task_response,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        "https://api.clickup.com/api/v2/team/18011725/task?include_closed=true&subtasks=true&archived=false&order_by=updated&reverse=true&date_updated_gt=0",
        body=task_response_json,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        "https://api.clickup.com/api/v2/team/18011726/task?include_closed=true&subtasks=true&archived=true&order_by=updated&reverse=true&date_updated_gt=0",
        body=archived_task_response_two,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        "https://api.clickup.com/api/v2/team/18011726/task?include_closed=true&subtasks=true&archived=false&order_by=updated&reverse=true&date_updated_gt=0",
        body=task_response_json_two,
        content_type="application/json",
    )
    tap1: Tap = TapClickUp(config=SAMPLE_CONFIG, parse_env_config=True)
    # Inject HTTP response, limit catalog to just task/project data?
    # Task archived
    # Task unarchived
    # Pull code from google for testing with mocked responses
    tap1.run_discovery()
    catalog1 = tap1.catalog_dict
    # select only team and tasks
    for stream in catalog1["streams"]:
        if stream.get("stream") and stream["stream"] not in ("task", "team"):
            for metadata in stream["metadata"]:
                metadata["metadata"]["selected"] = False

    state1 = tap1.state
    # Check initial state is start_date
    task_replication_key = tap1.streams.get("task").replication_key
    # assert state1["task"]["partitions"][0][task_replication_key] != None #Data from Task archived response and unarchived response.
    # print(f"CATALOG: {catalog1}")
    print(f"STATE from tap1 is now: {tap1.state}")
    tap2: Tap = TapClickUp(config=SAMPLE_CONFIG, state=state1, catalog=catalog1)
    tap2.streams.get("team").sync()
    tap2.streams.get("task").sync()
    print(f"STATE is now: {json.dumps(tap2.state, indent=4)}")
    # assert a==b
    task_state = tap2.state["bookmarks"]["task"]["partitions"]
    assert len(task_state) == 4  # Must be 4 tasks
    for state in task_state:
        print(f"state iter: {state}")
        if (
            state["context"]["archived"] == "true"
            and state["context"]["team_id"] == "18011725"
        ):
            value_should_be = "1801172501"  # Data from Task archived response and unarchived response. k
        elif (
            state["context"]["archived"] == "false"
            and state["context"]["team_id"] == "18011725"
        ):
            value_should_be = "1801172502"  # Data from Task archived response and unarchived response. k
        elif (
            state["context"]["archived"] == "true"
            and state["context"]["team_id"] == "18011726"
        ):
            value_should_be = "1801172601"  # Data from Task archived response and unarchived response. k
        elif (
            state["context"]["archived"] == "false"
            and state["context"]["team_id"] == "18011726"
        ):
            value_should_be = "1801172602"  # Data from Task archived response and unarchived response. k
        else:
            raise Exception("State doesn't match expectations")
        assert state["replication_key_value"] == value_should_be


# Setup 2 runs, feed state to next run. URL request should include data from the first state setup.
