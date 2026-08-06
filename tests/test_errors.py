"""_error_for maps a KRX respCode to the right subclass."""

from krx_openapi.errors import (
    KRXAuthError,
    KRXError,
    KRXResponseError,
    _error_for,
)


def test_401_is_auth_error():
    err = _error_for("401", "service not applied")
    assert isinstance(err, KRXAuthError)
    assert err.code == "401"
    assert "service not applied" in err.message


def test_other_code_is_response_error():
    err = _error_for("500", "boom")
    assert isinstance(err, KRXResponseError)
    assert not isinstance(err, KRXAuthError)
    assert err.code == "500" and err.message == "boom"


def test_subclasses_are_all_krx_errors():
    assert issubclass(KRXAuthError, KRXResponseError)
    assert issubclass(KRXResponseError, KRXError)


def test_auth_error_has_a_default_message():
    assert _error_for("401", "").message  # non-empty even when the vendor sends none
