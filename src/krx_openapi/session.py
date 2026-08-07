"""KRXSession -- key injection, one GET over the standard library, the status contract.

The session holds the API key and turns an endpoint + params into rows: a
``list[dict[str, str]]``, the vendor's ``OutBlock_*`` array passed through with its
own field names. No third-party HTTP client -- ``urllib`` carries it, so the package
has zero runtime dependencies.

KRX answers with HTTP 200 even on failure and marks the failure with a non-empty
``respCode`` (+ ``respMsg``) in the JSON body; :meth:`fetch` applies that contract,
raising the typed error and otherwise returning the single array the body carries.
"""

from __future__ import annotations

import http.client
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ._config import resolve_api_key
from ._endpoint import SAMPLE_DATE, SAMPLE_KEY, KRXEndpoint
from .errors import KRXNetworkError, KRXRateLimitError, _error_for
from .types import Row

_AUTH_HEADER = "AUTH_KEY"
_USER_AGENT = "krx-openapi"

# KRX limits each auth key to 10,000 calls/day; over it, the request returns 429.
_RATE_LIMIT_STATUS = 429
# A wrong key/URL, the sample path with a real key, or http:// all return 403.
_FORBIDDEN_STATUS = 403


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse every redirect instead of following it.

    ``urllib`` follows a 3xx automatically and copies the request headers -- the
    ``AUTH_KEY`` among them -- onto the new location, so a redirect (in particular an
    https -> http downgrade) would hand the API key to another host, in cleartext on
    the downgrade. Refusing turns any redirect into an ``HTTPError``, which
    :meth:`KRXSession._get` already surfaces as :class:`KRXNetworkError`; the key
    never leaves the original https host.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        # The redirect target (newurl) is server-controlled -- keep it out of the error
        # so nothing it carries can surface through the chained exception.
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused", headers, fp)


# One opener for the whole package: the default global opener follows redirects, so
# a private opener with the no-redirect handler is what actually closes the leak.
_OPENER = urllib.request.build_opener(_NoRedirect)


class KRXSession:
    """Holds the API key and fetches endpoints as raw rows.

    The key comes from ``api_key``, then ``$KRX_API_KEY``, then the config file
    ``~/.config/krx-openapi/credentials.json``; construction raises
    :class:`KRXConfigError` when none of them supplies one.
    """

    def __init__(self, api_key: str | None = None, *, timeout: float = 60.0) -> None:
        self.api_key = resolve_api_key(api_key)
        self.timeout = timeout

    def __repr__(self) -> str:
        # Never shows the API key, in whole or in part.
        return "KRXSession(...)"

    def fetch(self, endpoint: KRXEndpoint, **params: str) -> list[Row]:
        """Fetch one service and return its ``OutBlock_*`` rows.

        ``params`` are the query arguments the endpoint takes -- for the daily
        endpoints, ``basDd="YYYYMMDD"``. A non-empty ``respCode`` raises the matching
        :class:`KRXResponseError` (``401`` -> :class:`KRXAuthError`); HTTP 429 raises
        :class:`KRXRateLimitError`; a transport or non-JSON failure raises
        :class:`KRXNetworkError`; an empty ``OutBlock_*`` (a no-data date) returns ``[]``.
        """
        return self._get(endpoint.url, self.api_key, params)

    @classmethod
    def fetch_sample(cls, endpoint: KRXEndpoint, *, timeout: float = 60.0) -> list[Row]:
        """Fetch an endpoint's keyless sample (fixed :data:`SAMPLE_DATE`).

        A classmethod: it builds its own session from the public sample key, so it
        needs no configured ``KRX_API_KEY`` at all. Hits the ``/svc/sample/apis``
        twin, never a real service.
        """
        session = cls(SAMPLE_KEY, timeout=timeout)
        return session._get(endpoint.sample_url, SAMPLE_KEY, {"basDd": SAMPLE_DATE})

    def _get(self, url: str, api_key: str, params: dict[str, str]) -> list[Row]:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        full_url = f"{url}?{query}" if query else url
        request = urllib.request.Request(
            full_url, headers={_AUTH_HEADER: api_key.strip(), "User-Agent": _USER_AGENT}
        )
        try:
            with _OPENER.open(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as err:
            with err:  # an HTTPError is an unclosed response; release its socket
                if err.code == _RATE_LIMIT_STATUS:
                    raise KRXRateLimitError(
                        "KRX daily call quota exceeded (10,000/key/day); resets at "
                        "midnight") from err
                hint = ""
                if err.code == _FORBIDDEN_STATUS:
                    hint = (" -- check the key, that the URL is https and /svc/apis "
                            "(not /svc/sample/apis with a real key)")
                raise KRXNetworkError(f"HTTP {err.code} from KRX for {url}{hint}") from err
        except urllib.error.URLError as err:
            raise KRXNetworkError(f"request to KRX failed: {err.reason}") from err
        except (http.client.HTTPException, OSError) as err:
            # A failure during response.read() (IncompleteRead, a socket timeout or
            # reset) is not an HTTPError/URLError; surface it through KRXError too.
            raise KRXNetworkError(f"KRX response read failed for {url}: {err}") from err
        return _rows_from_body(raw, url)


def _rows_from_body(raw: bytes, url: str) -> list[Row]:
    """Apply the KRX status contract to a raw response body.

    A pure function of the bytes: parses JSON, raises on a non-empty ``respCode`` or a
    non-JSON body, and returns the single ``OutBlock_*`` array (``[]`` when the vendor
    sends an empty one for a no-data date).
    """
    try:
        # Decode as UTF-8 explicitly: json.loads(bytes) auto-detects UTF-16/32, which
        # would let a non-UTF-8 body slip through the "must be UTF-8 JSON" contract.
        body: Any = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as err:
        # A 200 whose body is not JSON / not UTF-8 (a proxy or maintenance HTML page), or
        # is nested deep enough to blow the parser's recursion limit, must surface through
        # KRXError, not as a raw decode/recursion error.
        raise KRXNetworkError(f"non-JSON response from KRX for {url}") from err
    if not isinstance(body, dict):
        raise KRXNetworkError(f"unexpected KRX response for {url}: {body!r}")

    code = body.get("respCode")
    if code:  # present only on failure
        raise _error_for(str(code), str(body.get("respMsg", "")))

    blocks = [
        value for key, value in body.items()
        if key.startswith("OutBlock_") and isinstance(value, list)
    ]
    if len(blocks) != 1:
        # Success must carry exactly one OutBlock_* array; zero or several is a shape
        # this contract does not recognize (not a silent empty result).
        raise KRXNetworkError(
            f"expected exactly one OutBlock_* array from KRX for {url}, got {len(blocks)}")
    rows = blocks[0]
    if not all(isinstance(row, dict) for row in rows):
        raise KRXNetworkError(f"a non-object row in KRX OutBlock for {url}")
    return rows
