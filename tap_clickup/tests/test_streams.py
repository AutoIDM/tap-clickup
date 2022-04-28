"""Tests standard tap features using the built-in SDK tests library."""
import os
import responses
import pytest
from tap_clickup.tap import TapClickUp

SAMPLE_CONFIG = {
    "api_token": os.environ["TAP_CLICKUP_API_TOKEN"],
}


# Run standard built-in tap tests from the SDK:


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


def test_empty_folderless_list(mocked_responses):
    """This should run without failure. Failed at one point re https://github.com/AutoIDM/tap-clickup/issues/121"""
    empty_folderless_list_response = """
    {"lists":[]}
    """

    team_response = """
{
    "teams": [
        {
            "id": "123",
            "name": "AutoIDM Workspace",
            "color": "#536cfe",
            "avatar": null,
            "members": [
                {
                    "user": {
                        "id":123,
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
    space_response = """
{
    "spaces": [
        {
            "id": "456",
            "name": "Space",
            "private": false,
            "statuses": [
                {
                    "id": "p30029929_3GnQgTsE",
                    "status": "to do",
                    "type": "open",
                    "orderindex": 0,
                    "color": "#d3d3d3"
                },
                {
                    "id": "p30029929_t8FMGxQZ",
                    "status": "complete",
                    "type": "closed",
                    "orderindex": 1,
                    "color": "#6bc950"
                }
            ],
            "multiple_assignees": true,
            "features": {
                "due_dates": {
                    "enabled": true,
                    "start_date": true,
                    "remap_due_dates": true,
                    "remap_closed_due_date": false
                },
                "sprints": {
                    "enabled": true
                },
                "time_tracking": {
                    "enabled": true,
                    "harvest": false,
                    "rollup": false
                },
                "points": {
                    "enabled": true
                },
                "custom_items": {
                    "enabled": false
                },
                "priorities": {
                    "enabled": true,
                    "priorities": [
                        {
                            "id": "1",
                            "priority": "urgent",
                            "color": "#f50000",
                            "orderindex": "1"
                        },
                        {
                            "id": "2",
                            "priority": "high",
                            "color": "#ffcc00",
                            "orderindex": "2"
                        },
                        {
                            "id": "3",
                            "priority": "normal",
                            "color": "#6fddff",
                            "orderindex": "3"
                        },
                        {
                            "id": "4",
                            "priority": "low",
                            "color": "#d8d8d8",
                            "orderindex": "4"
                        }
                    ]
                },
                "tags": {
                    "enabled": true
                },
                "time_estimates": {
                    "enabled": true,
                    "rollup": false,
                    "per_assignee": false
                },
                "check_unresolved": {
                    "enabled": true,
                    "subtasks": true,
                    "checklists": null,
                    "comments": null
                },
                "zoom": {
                    "enabled": false
                },
                "milestones": {
                    "enabled": true
                },
                "custom_fields": {
                    "enabled": true
                },
                "remap_dependencies": {
                    "enabled": true
                },
                "dependency_warning": {
                    "enabled": true
                },
                "multiple_assignees": {
                    "enabled": true
                },
                "emails": {
                    "enabled": true
                }
            },
            "archived": false
        }
    ]
}
"""
    mocked_responses.add(
        responses.GET,
        ("https://api.clickup.com/api/v2/space/456/list?archived=false"),
        body=empty_folderless_list_response,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        ("https://api.clickup.com/api/v2/space/456/list?archived=true"),
        body=empty_folderless_list_response,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        "https://api.clickup.com/api/v2/team",
        body=team_response,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        "https://api.clickup.com/api/v2/team/123/space?archived=false",
        body=space_response,
        content_type="application/json",
    )
    mocked_responses.add(
        responses.GET,
        "https://api.clickup.com/api/v2/team/123/space?archived=true",
        body=space_response,
        content_type="application/json",
    )

    tap: TapClickUp = TapClickUp(config=SAMPLE_CONFIG, parse_env_config=True)
    tap.run_discovery()
    catalog1 = tap.catalog_dict
    for stream in catalog1["streams"]:
        if stream.get("stream") and stream["stream"] not in ("folderless_list", "team"):
            for metadata in stream["metadata"]:
                metadata["metadata"]["selected"] = False
    state = tap.state
    tap: TapClickUp = TapClickUp(config=SAMPLE_CONFIG, state=state, catalog=catalog1)
    tap.streams.get(
        "team"
    ).sync()  # This calls team, and task as task is a child stream
