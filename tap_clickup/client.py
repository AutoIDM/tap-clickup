"""REST client handling, including ClickUpStream base class."""

from typing import Any, Optional, Iterable, Dict
from pathlib import Path
from datetime import datetime
import time
import requests
import singer
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream
from singer_sdk.exceptions import RetriableAPIError, FatalAPIError

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class ClickUpStream(RESTStream):
    """ClickUp stream class."""

    url_base = "https://api.clickup.com/api/v2"
    records_jsonpath = "$[*]"  # Or override `parse_response`.
    next_page_token_jsonpath = "$.next_page"  # Or override `get_next_page_token`.
    _LOG_REQUEST_METRIC_URLS: bool = True

    @property
    def schema(self) -> dict:
        """Get schema.

        We are waiting on https://gitlab.com/meltano/sdk/-/issues/299 this works
        well until then
        Returns:
            JSON Schema dictionary for this stream.
        """
        return singer.resolve_schema_references(self._schema)

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {}
        if next_page_token:
            params["page"] = next_page_token
        if context:
            params["archived"] = context.get("archived")
        return params

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")

        headers["Authorization"] = self.config.get("api_token")
        return headers

    def validate_response(self, response: requests.Response) -> None:
        """Validate HTTP response.

        In case an error is deemed transient and can be safely retried, then this
        method should raise an :class:`singer_sdk.exceptions.RetriableAPIError`.

        Args:
            response: A `requests.Response`_ object.

        Raises:
            FatalAPIError: If the request is not retriable.
            RetriableAPIError: If the request is retriable.

        .. _requests.Response:
            https://docs.python-requests.org/en/latest/api/#requests.Response
        """
        if response.status_code == 429:
            msg = (
                f"{response.status_code} Server Error: "
                f"{response.reason} for path: {self.path}"
            )
            reset_epoch: int = int(response.headers.get("X-RateLimit-Reset"))
            date = response.headers.get("Date")
            dformat = "%a, %d %b %Y %H:%M:%S %Z"
            epoch = datetime(1970, 1, 1)
            currentEpoch = (datetime.strptime(date, dformat) - epoch).total_seconds()
            waitTime = reset_epoch - currentEpoch
            self.logger.info(
                f"API Limit reached, waiting {waitTime} seconds and will try again."
            )
            if waitTime > 120:
                self.logger.warning(
                    "Wait time is more than 2 minutes, Waiting 60s and trying again."
                )
                time.sleep(60)
            else:
                time.sleep(waitTime)
            # This will cause us to wait a bit longer than we need to due
            # to exponential backoff but it's minimal, and is actually better
            # for the clickup servers to have clients add some randomness
            raise RetriableAPIError(msg)

        if 400 <= response.status_code < 500:
            msg = (
                f"{response.status_code} Client Error: "
                f"{response.reason} for path: {self.path}"
            )
            raise FatalAPIError(msg)

        elif 500 <= response.status_code < 600:
            msg = (
                f"{response.status_code} Server Error: "
                f"{response.reason} for path: {self.path}"
            )
            raise RetriableAPIError(msg)

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        yield from extract_jsonpath(self.records_jsonpath, input=response.json())

    def from_parent_context(self, context: dict):
        """ """
        if self.partitions is None:
            return context
        else:
            # Goal here is to combine Parent/Child relationships with Partions
            # Another way to think about this is that Partitions are now
            # Lists of contexts, used to create multiple requests based on one context.
            # ie we have one team_id and we need a requst
            # for archieved=true and archieved=False
            # For N Child relationships if we have K base_partitions we'll end up with N*K partitions
            # Assumption is that base_partition is a list of dicts
            child_context_plus_base_partition = []
            for partition in self.base_partition:  # pylint: disable=not-an-iterable
                child_plus_partition = context.copy()
                child_plus_partition.update(partition)
                child_context_plus_base_partition.append(child_plus_partition)
            self.partitions = child_context_plus_base_partition

            return None  # self.partitions handles context in the _sync call. Important this is None to use partitions

    def _sync_children(self, child_context: dict) -> None:
        for child_stream in self.child_streams:
            if child_stream.selected or child_stream.has_selected_descendents:
                child_stream.sync(
                    child_stream.from_parent_context(context=child_context)
                )
