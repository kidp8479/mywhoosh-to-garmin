import pytest

import main

REQUIRED_ENV = {
    "MYWHOOSH_EMAIL": "rider@example.com",
    "MYWHOOSH_PASSWORD": "mw-secret",
    "GARMIN_USERNAME": "rider@example.com",
    "GARMIN_PASSWORD": "garmin-secret",
}


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    """Run load_config against a clean environment, ignoring any local .env."""
    monkeypatch.setattr(main, "load_dotenv", lambda *a, **kw: None)
    for key in [*REQUIRED_ENV, "GARMIN_TOKEN_BASE64", "LOG_LEVEL"]:
        monkeypatch.delenv(key, raising=False)


def test_load_config_returns_expected_keys(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)

    config = main.load_config()

    assert config["mywhoosh_email"] == "rider@example.com"
    assert config["garmin_password"] == "garmin-secret"
    assert config["log_level"] == "INFO"  # default when LOG_LEVEL is unset


def test_load_config_raises_when_required_var_missing(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("MYWHOOSH_EMAIL")

    with pytest.raises(ValueError, match="MYWHOOSH_EMAIL"):
        main.load_config()


def test_load_config_accepts_token_instead_of_garmin_password(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("GARMIN_PASSWORD")
    monkeypatch.setenv("GARMIN_TOKEN_BASE64", "base64-token-store")

    config = main.load_config()

    assert config["garmin_password"] is None
    assert config["garmin_token_base64"] == "base64-token-store"


def test_load_config_requires_password_or_token(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("GARMIN_PASSWORD")

    with pytest.raises(ValueError, match="GARMIN_PASSWORD"):
        main.load_config()
