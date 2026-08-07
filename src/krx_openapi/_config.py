"""Resolve the KRX API key from the caller, the environment, or the config file.

The key is looked up in a fixed order, so an explicit value always wins and a set
environment variable beats a file on disk:

1. the ``api_key`` passed to ``KRX(...)``
2. the ``KRX_API_KEY`` environment variable
3. ``"KRX_API_KEY"`` in ``$XDG_CONFIG_HOME/krx-openapi/credentials.json``
   (``$XDG_CONFIG_HOME`` defaults to ``~/.config``)

The file is optional -- its absence just means "no key here." But a file that is
present and unreadable, not JSON, or not a JSON object is an error, because a caller
who wrote one meant it to be used and a silent skip would hide the mistake.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import KRXConfigError

_ENV_VAR = "KRX_API_KEY"
_CONFIG_DIR = "krx-openapi"
_CONFIG_FILE = "credentials.json"


def resolve_api_key(explicit: str | None) -> str:
    """Return the first key found across the three sources, or raise if none exists."""
    key = (explicit or "").strip() or os.environ.get(_ENV_VAR, "").strip() or _key_from_file()
    if not key:
        raise KRXConfigError(
            f"no KRX API key: pass api_key=, set the {_ENV_VAR} environment "
            f"variable, or put it in {credentials_path()}"
        )
    if any(ord(ch) < 0x20 or ord(ch) == 0x7f for ch in key):
        # A control character (a stray newline/tab, often from a copy-paste) would make
        # an invalid HTTP header: urllib raises ValueError echoing the whole value -- the
        # key. Reject it as a config error, before it becomes a request, and never echo it.
        raise KRXConfigError(
            "the KRX API key contains a control character (a stray newline or tab?)")
    return key


def credentials_path() -> Path:
    """The path krx-openapi reads a stored key from (honoring ``$XDG_CONFIG_HOME``)."""
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home) / _CONFIG_DIR / _CONFIG_FILE


def _key_from_file() -> str:
    path = credentials_path()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError as err:
        # A present file that is not UTF-8 is "unreadable" in the same sense as an
        # OSError: the caller wrote it meaning it to be used, so surface it, not a
        # raw decode error. (UnicodeDecodeError is a ValueError, not an OSError.)
        raise KRXConfigError(f"{path} is not valid UTF-8: {err}") from err
    except OSError as err:
        raise KRXConfigError(f"could not read {path}: {err}") from err

    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise KRXConfigError(f"{path} is not valid JSON: {err}") from err
    if not isinstance(data, dict):
        raise KRXConfigError(f"{path} must contain a JSON object")

    key = data.get(_ENV_VAR)
    return key.strip() if isinstance(key, str) else ""
