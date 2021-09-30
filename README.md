# tap-clickup
![Build and Tests](https://github.com/AutoIDM/tap-clickup/actions/workflows/ci.yml/badge.svg?branch=main)

`tap-clickup` is a Singer tap for ClickUp.

## Installation

```bash
pipx install tap-clickup
```

## Configuration

### Accepted Config Options

1. start_date - Example '2010-01-01T00:00:00Z'
2. api_token  - Example 'pk_12345' 


A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-clickup --about
```

### Source Authentication and Authorization

- [ ] `TODO:` Provide step by step instructions for setting up an API Key

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
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any _"TODO"_ items listed in
the file.

Next, install Meltano (if you haven't already) and any needed plugins:

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

This was written with the [Meltano SDK](https://sdk.meltano.com/en/latest/dev_guide.html) , check it out!


