"""REST client handling, including ClickUpStream base class."""

from typing import Any, Optional, Iterable, cast
from pathlib import Path
from datetime import datetime
import time
import requests
import backoff
from requests.exceptions import RequestException
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class ClickUpStream(RESTStream):
    """ClickUp stream class."""

    url_base = "https://api.clickup.com/api/v2"
    records_jsonpath = "$[*]"  # Or override `parse_response`.
    next_page_token_jsonpath = "$.next_page"  # Or override `get_next_page_token`.

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")

        headers["Authorization"] = self.config.get("api_token")
        return headers

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return a token for identifying next page or None if no more pages."""
        if self.next_page_token_jsonpath:
            all_matches = extract_jsonpath(
                self.next_page_token_jsonpath, response.json()
            )
            first_match = next(iter(all_matches), None)
            next_page_token = first_match
        else:
            next_page_token = response.headers.get("X-Next-Page", None)

        return next_page_token

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException),
        max_tries=5,
        giveup=lambda e: e.response is not None
        and (e.response.status_code != 429 and 400 <= e.response.status_code < 500),
        factor=2,
    )
    def _request_with_backoff(
        self, prepared_request, context: Optional[dict]
    ) -> requests.Response:
        response = self.requests_session.send(prepared_request)
        if self._LOG_REQUEST_METRICS:
            extra_tags = {}
            if self._LOG_REQUEST_METRIC_URLS:
                extra_tags["url"] = cast(str, prepared_request.path_url)
            self._write_request_duration_log(
                # Shows useful incremental debugging info for clickup
                # There is no sensitive data here
                endpoint=prepared_request.path_url,
                response=response,
                context=context,
                extra_tags=extra_tags,
            )
        if response.status_code in [401, 403]:
            self.logger.info("Failed request for {}".format(prepared_request.url))
            self.logger.info(
                f"Reason: {response.status_code} - {str(response.content)}"
            )
            raise RuntimeError(
                "Requested resource was unauthorized, forbidden, or not found."
            )
        elif response.status_code == 429:
            # ClickOff api limits to 100 requests/min.
            # There's probably a nicer way to use this with the backoff library
            # Does not rely on any local time information

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

            raise RequestException

        elif response.status_code >= 400:
            raise RuntimeError(
                f"Error making request to API: {prepared_request.url} "
                f"[{response.status_code} - {str(response.content)}]".replace(
                    "\\n", "\n"
                )
            )
        self.logger.debug("Response received successfully.")
        return response

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        yield from extract_jsonpath(self.records_jsonpath, input=response.json())
