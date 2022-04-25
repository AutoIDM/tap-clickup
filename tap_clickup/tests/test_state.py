from singer_sdk.tap_base import Tap
import os
import responses
import pytest
from pathlib import Path

from tap_clickup.tap import TapClickUp

SAMPLE_CONFIG = {
    # "start_date": 0,
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


# Setup 1 api call, state should be set to one date, from start_date, then the state
# returned should be the latest data set
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
        (
            "https://api.clickup.com/api/v2/team/18011725/task?archived=true"
            + "&include_closed=true&subtasks=true&order_by=updated&reverse=true"
        ),
        body=archived_task_response,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        (
            "https://api.clickup.com/api/v2/team/18011725/task?archived=false"
            + "&include_closed=true&subtasks=true&order_by=updated&reverse=true"
        ),
        body=task_response_json,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        (
            "https://api.clickup.com/api/v2/team/18011726/task?archived=true"
            + "&include_closed=true&subtasks=true&order_by=updated&reverse=true"
        ),
        body=archived_task_response_two,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        (
            "https://api.clickup.com/api/v2/team/18011726/task?archived=false"
            + "&include_closed=true&subtasks=true&order_by=updated&reverse=true"
        ),
        body=task_response_json_two,
        content_type="application/json",
    )
    tap1: Tap = TapClickUp(config=SAMPLE_CONFIG, parse_env_config=True)
    tap1.run_discovery()
    catalog1 = tap1.catalog_dict
    for stream in catalog1["streams"]:
        if stream.get("stream") and stream["stream"] not in ("task", "team"):
            for metadata in stream["metadata"]:
                metadata["metadata"]["selected"] = False
    state1 = tap1.state
    tap2: Tap = TapClickUp(config=SAMPLE_CONFIG, state=state1, catalog=catalog1)
    tap2.streams.get(
        "team"
    ).sync()  # This calls team, and task as task is a child stream

    task_state = tap2.state["bookmarks"]["task"]["partitions"]
    assert len(task_state) == 4  # Must be 4 tasks
    for state in task_state:
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
