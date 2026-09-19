"""Resolve the KRX API key from the caller, the environment, or the config file.

The key is looked up in a fixed order, so an explicit value always wins and a set
environment variable beats a file on disk:

1. the ``api_key`` passed to ``KRX(...)``
2. the ``KRX_API_KEY`` environment variable
3. ``"KRX_API_KEY"`` in ``$XDG_CONFIG_HOME/krx-openapi/credentials.json``
   (``$XDG_CONFIG_HOME`` defaults to ``~/.config``)

The resolution, the whitespace trimming, the permission handling (a group/other-readable
file is warned about, not refused), and the storage backend are delegated to credbox. The
store binding is not hardcoded: ``Credentials.for_app("krx-openapi")`` lets a host
embedding krx-openapi redirect it via ``KRX_OPENAPI_STORE_APP`` / ``KRX_OPENAPI_NAMESPACE``;
standalone it is exactly the flat ``~/.config/krx-openapi/credentials.json`` krx-openapi has
always read. A file that is present but unreadable, not JSON, or not a JSON object is still
an error rather than a silent skip.

Once a key is found, it is still checked for characters it cannot send as an HTTP header
here -- credbox trims surrounding whitespace but keeps an embedded newline/tab or a
non-ASCII character, any of which would make an invalid header and let urllib echo part of
the key while encoding it. That check is krx-openapi's own concern, not something the
credential store knows about.
"""

from __future__ import annotations

from functools import lru_cache

from credbox import CredBoxError, Credentials

from .errors import KRXConfigError

_ENV_VAR = "KRX_API_KEY"
_STORE_APP = "krx-openapi"


def resolve_api_key(explicit: str | None) -> str:
    """Return the first key found across the three sources, or raise if none exists."""
    try:
        found = _get_credentials().secret(_ENV_VAR, override=explicit)
    except CredBoxError as err:
        # credbox's message already names the store path + fault; don't prepend a static
        # path (wrong under a KRX_OPENAPI_STORE_APP redirect). credbox detaches
        # secret-bearing context, so chaining `from err` keeps the key out of any traceback.
        raise KRXConfigError(f"could not read the credential store: {err}") from err
    if found is None:
        # Binding validated cleanly above (None, not error), so store_location() is safe
        # and gives the real store (the host's under a redirect).
        raise KRXConfigError(
            f"no KRX API key: pass api_key=, set the {_ENV_VAR} environment "
            f"variable, or put it in {_get_credentials().store_location()}"
        )
    key = found.reveal()
    if any(not (0x20 <= ord(ch) < 0x7f) for ch in key):
        # The key rides an HTTP header (AUTH_KEY). Any byte outside printable ASCII -- a
        # stray newline/tab from a copy-paste, or a non-ASCII character -- makes an invalid
        # header, and urllib raises *while encoding it*, echoing the offending character
        # (part of the key). Reject it here, before it becomes a request, and never echo
        # it. KRX keys are ASCII tokens, so no legitimate key is lost.
        raise KRXConfigError(
            "the KRX API key contains a character it cannot send as an HTTP header "
            "(a stray newline, tab, or non-ASCII character?)")
    return key


@lru_cache(maxsize=1)
def _get_credentials() -> Credentials:
    """krx-openapi's credbox credential store, built on first use and cached.

    Built via ``for_app`` (not the bare ``Credentials(...)``) so a host embedding
    krx-openapi can redirect the binding with ``KRX_OPENAPI_STORE_APP`` /
    ``KRX_OPENAPI_NAMESPACE`` before the first lookup. credbox re-resolves the store
    *path* per call (honouring a later ``XDG_CONFIG_HOME``); the binding is read from the
    environment once, when this facade is built. A malformed binding surfaces as
    ``KRXConfigError`` on the first lookup that actually reaches the store -- an explicit
    argument or ``KRX_API_KEY`` resolves first, so a bad binding with the env var set
    never raises.
    """
    return Credentials.for_app(_STORE_APP)
