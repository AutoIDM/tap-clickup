# `tap-clickup`
![Build and Tests](https://github.com/AutoIDM/tap-clickup/actions/workflows/ci.yml/badge.svg?branch=main)
[![PyPI download month](https://img.shields.io/pypi/dm/tap-clickup.svg)](https://pypi.python.org/pypi/tap-clickup/)

`tap-clickup` is a Singer tap for ClickUp.

## Capabilities

* `sync`
* `catalog`
* `state`
* `discover`

## Settings

| Setting   | Required | Default | Description |
|:----------|:--------:|:-------:|:------------|
| api_token | True     | None    | Example: 'pk_12345'            |
| start_date| False    | None    | Example:  '2010-01-01T00:00:00Z'            |

A full list of supported settings and capabilities is available by running: `tap-clickup --about`

### Getting an API Token

1. Login at https://app.clickup.com/
1. Click your icon at the bottom left of the screen
1. Click My Settings
1. Click Apps (Bottom leftish of screen under the My Apps sub section)
1. At the top of the screen is an API Token. This can be used in the api_token location. 
    * This is a personal token, it's fine to use a personal token as this tap is only for the business that's using the data. 

## Clickup Replication
Incremental Replication keys are available for Tasks. The Task uses the updated at field as [documented in the tasks section](https://clickup.com/apiv1) of the api.

Start Date is used for the initial updated at value for the updated at field with tasks. 

Let's say that you only want tasks that have been updated in the last year. To accomplish this you would pass in a start date of the first of this year!

## Clickup Table Schemas
Note that the most up to date information is located in tap_clickup/streams.py. We will try to keep these docs updated

### Teams
- Table name: team
- Description: Teams Data, each user can be in multiple teams
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Teams](https://jsapi.apiary.io/apis/clickup20/reference/0/teams/get-teams.html)

### Spaces
- Table name: space
- Description: Each team has multiple spaces
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Spaces](https://jsapi.apiary.io/apis/clickup20/reference/0/spaces.html)

### Folders
- Table name: folder
- Description: Each space can have multiple folders
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Folders](https://jsapi.apiary.io/apis/clickup20/reference/0/folders.html)

### Folder Lists
- Table name: folder_list
- Description: Each Folder can have multiple lists
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation:[Folder Lists](https://jsapi.apiary.io/apis/clickup20/reference/0/lists/get-lists.html)


### Folderless Lists
- Table name: folderless_list
- Description: Some lists do not exist in a folder
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Folderless Lists](https://jsapi.apiary.io/apis/clickup20/reference/0/lists/get-folderless-lists.html)

### Task Templates
- Table name: task_template
- Description: Tasks can be templated for any reason you can imagine!
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Task Templates](https://jsapi.apiary.io/apis/clickup20/reference/0/task-templates/get-task-templates.html)

### Goals
- Table name: goal 
- Description: Teams can set goals for themselves
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Goals](https://jsapi.apiary.io/apis/clickup20/reference/0/goals/get-goals.html)

### Tags
- Table name: tag
- Description: Each space can have multiple tags
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Tags](https://jsapi.apiary.io/apis/clickup20/reference/0/tags/get-space-tags.html)

### Shared Hierarchy
- Table name: shared_hierarchy
- Description: Returns all resources you have access to where you don't have access to its parent. For example, if you have a access to a shared task, but don't have access to its parent list, it will come back in this request.
- Primary key column(s): (No primary key column)
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Shared Hierarchy](https://jsapi.apiary.io/apis/clickup20/reference/0/shared-hierarchy/shared-hierarchy.html)

### Custom Fields from Folderless Lists
- Table name: folderless_customfield
- Description: Each Folderless lists can have custom fields associated with them
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Custom Field](https://jsapi.apiary.io/apis/clickup20/reference/0/custom-fields/get-accessible-custom-fields.html)

### Custom Field from Folder Lists
- Table name: folder_customfield
- Description: Each Foldere list can have custom fields associated with them
- Primary key column(s):  id
- Replicated fully or incrementally: No
- Bookmark column(s): N/A
- Link to API endpoint documentation: [Custom Field](https://jsapi.apiary.io/apis/clickup20/reference/0/custom-fields/get-accessible-custom-fields.html)

### Folderless Tasks
- Table name: folderless_task
- Description: Some tasks do not sit under folders. This comes from the folderless_list endpoint
- Primary key column(s):  id
- Replicated fully or incrementally: Yes
- Bookmark column(s): date_updated. Note that the api endpoint date_updated_gt is great than or equal to, not just greater than. 
- Link to API endpoint documentation: [Get Tasks](https://jsapi.apiary.io/apis/clickup20/reference/0/tasks/get-tasks.html)

### Folder Tasks
- Table name: folder_task
- Description: Some tasks do not sit under folders. This comes from the folderless_list endpoint
- Primary key column(s):  id
- Replicated fully or incrementally: Yes
- Bookmark column(s): date_updated. Note that the api endpoint date_updated_gt is great than or equal to, not just greater than. 
- Link to API endpoint documentation: [Get Tasks](https://jsapi.apiary.io/apis/clickup20/reference/0/tasks/get-tasks.html)

## Other Info

* Dates are returned in UNIX time 
* API Limiting uses [X-RateLimit headers](https://tools.ietf.org/id/draft-polli-ratelimit-headers-00.html)

## Installation

```bash
pipx install tap-clickup
```

## Usage

You can easily run `tap-clickup` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-clickup --version
tap-clickup --help
tap-clickup --config CONFIG --discover > ./catalog.json
```

## Developer Resources

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tap_clickup/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-clickup` CLI interface directly using `poetry run`:

```bash
poetry run tap-clickup --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.

Install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-clickup
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-clickup --version
# OR run a test `elt` pipeline:
meltano elt tap-clickup target-jsonl
```

### SDK

Built with the [Meltano SDK](https://sdk.meltano.com) for Singer Taps and Targets.

