from unittest.mock import MagicMock, patch

import pytest
from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectTooManyRequestsError,
)

from services.garmin_service import GarminService


def test_garmin_service_init():
    svc = GarminService(username="user", password="pass")
    assert svc.username == "user"
    assert svc.password == "pass"


def test_authenticate_succeeds_on_first_try():
    svc = GarminService(username="user", password="pass", sleep=MagicMock())

    with patch.object(svc.client, "login") as login:
        svc.authenticate()

    login.assert_called_once_with()
    assert svc.is_authenticated() is True


def test_authenticate_retries_a_rate_limit_then_succeeds():
    sleep = MagicMock()
    svc = GarminService(username="user", password="pass", rate_limit_retries=3, sleep=sleep)

    with patch.object(
        svc.client,
        "login",
        side_effect=[GarminConnectTooManyRequestsError("429"), None],
    ) as login:
        svc.authenticate()

    assert login.call_count == 2
    sleep.assert_called_once_with(30)
    assert svc.is_authenticated() is True


def test_authenticate_raises_once_retries_are_exhausted():
    sleep = MagicMock()
    svc = GarminService(username="user", password="pass", rate_limit_retries=2, sleep=sleep)

    with (
        patch.object(
            svc.client,
            "login",
            side_effect=GarminConnectTooManyRequestsError("429"),
        ),
        pytest.raises(GarminConnectTooManyRequestsError),
    ):
        svc.authenticate()

    sleep.assert_called_once_with(30)
    assert svc.is_authenticated() is False


def test_authenticate_does_not_retry_bad_credentials():
    sleep = MagicMock()
    svc = GarminService(username="user", password="pass", sleep=sleep)

    with (
        patch.object(
            svc.client,
            "login",
            side_effect=GarminConnectAuthenticationError("bad creds"),
        ),
        pytest.raises(GarminConnectAuthenticationError),
    ):
        svc.authenticate()

    sleep.assert_not_called()
