"""Exception hierarchy for krx-openapi.

Every *operational* error this package raises derives from :class:`KRXError`, so one
``except KRXError`` catches them all. The subclasses separate the failure modes a
caller handles differently: a misconfiguration caught before any request
(:class:`KRXConfigError`), a rejected or un-applied service key
(:class:`KRXAuthError`), a daily-quota exhaustion (:class:`KRXRateLimitError`), any
other vendor-reported error inside a well-formed response
(:class:`KRXResponseError`), and a transport failure that never produced a KRX body
(:class:`KRXNetworkError`). Invalid *caller input* -- an unknown ``market`` code, an
unknown ``api_id`` -- raises the standard ``ValueError`` / ``KeyError`` instead, the
usual signal for a caller mistake rather than a runtime failure.

KRX answers every request with HTTP 200 and marks failure with a non-empty
``respCode`` in the JSON body; :func:`_error_for` turns that code into the right
subclass.
"""

from __future__ import annotations


class KRXError(RuntimeError):
    """Base class for every operational error raised by krx-openapi."""


class KRXConfigError(KRXError):
    """The client is misconfigured; raised before any request goes out.

    The usual cause is a missing API key -- neither passed to ``KRX(...)`` nor
    present in the ``KRX_API_KEY`` environment variable nor the config file.
    """


class KRXNetworkError(KRXError):
    """The request failed at the transport or HTTP layer.

    A timeout, DNS failure, connection reset, an interrupted read, a non-success HTTP
    status, or a 200 whose body is not JSON (a proxy/maintenance page). The underlying
    exception is chained as ``__cause__``.
    """


class KRXRateLimitError(KRXError):
    """The daily call quota was exceeded (HTTP 429).

    KRX limits each *auth key* (not IP) to 10,000 calls per day, reset at midnight.
    It is its own class -- not a :class:`KRXNetworkError` -- so a bulk caller can
    catch it distinctly and stop until the quota resets rather than retry.
    """


class KRXResponseError(KRXError):
    """KRX returned a well-formed response carrying an error ``respCode``.

    ``code`` and ``message`` are the vendor's own (``respCode`` / ``respMsg``), so a
    caller can branch on the code without parsing the message text.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"KRX {code}: {message}")


class KRXAuthError(KRXResponseError):
    """KRX rejected the key, or the service was not applied for (respCode 401).

    Each KRX service (지수, 주식, ...) is authorized separately on the account; a
    request for an un-applied service returns 401 exactly as a bad key does. It
    subclasses :class:`KRXResponseError`, so ``except KRXResponseError`` still
    catches it while a caller can catch an auth failure distinctly.
    """

    def __init__(self, message: str) -> None:
        super().__init__("401", message)


def _error_for(code: str, message: str) -> KRXResponseError:
    """Build the most specific :class:`KRXResponseError` for a KRX ``respCode``.

    A rate limit (429) arrives as an HTTP status, not a ``respCode`` -- handled in
    the session -- so it is not mapped here; this only covers the in-body codes.
    """
    if code == "401":
        return KRXAuthError(message or "KRX rejected the key or the service is not applied for")
    return KRXResponseError(code, message)
