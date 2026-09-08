from aap_gateway_api.utils.preferences import PreferenceCorruptError
from aap_gateway_api.views import gateway_exception_handler


def test_exception_handler_returns_500_on_preference_corrupt_error():
    exc = PreferenceCorruptError("Preference 'proxy__jwt_private_key' has corrupt data.")
    response = gateway_exception_handler(exc, context={"view": None, "request": None})
    assert response.status_code == 500
    assert "proxy__jwt_private_key" in response.data["detail"]
    assert "corrupt" in response.data["detail"]


def test_exception_handler_does_not_catch_other_exceptions():
    exc = ValueError("some other error")
    response = gateway_exception_handler(exc, context={"view": None, "request": None})
    assert response is None, "Non-handled exceptions should pass through to DRF's default handler which returns None"
