from typing import Callable, List, Type
from singer_sdk.tap_base import Tap
import datetime
import os

from tap_clickup.tap import TapClickUp

SAMPLE_CONFIG = {
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    "api_token": os.environ["TAP_CLICKUP_API_TOKEN"],
}

def test_default_incremental():
    """Return callable pytest which executes simple discovery and connection tests.
    """
    # Initialize with basic config
    tap1: Tap = TapClickUp(config=SAMPLE_CONFIG, parse_env_config=True)
    # Test discovery
    tap1.run_discovery()
    catalog1 = tap1.catalog_dict
    task_catalog = [taskmetadata for taskmetadata in catalog1["streams"] if taskmetadata.get("tap_stream_id") == "task"][0]
    assert task_catalog["replication_method"] == "INCREMENTAL"

#Setup 1 api call, state should be set to one date, from start_date, then the state returned should be the latest data set
def test_state_properly_stored():
    tap1: Tap = TapClickUp(config=SAMPLE_CONFIG, parse_env_config=True)
    #Inject HTTP response, limit catalog to just task/project data? 
    #TODO what response data?
    tap1.run_discovery()
    catalog1 = tap1.catalog_dict
    state1 = tap1.state
    assert state1 == ? #TODO what should? be
    #tap2: Tap = TapClickUp(config=SAMPLE_CONFIG, state=state1, catalog=catalog1)

#Setup 2 runs, feed state to next run. URL request should include data from the first state setup.  
