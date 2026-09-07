import pytest

import main

# Distinct value per variable so a copy-paste bug in load_config (reading the
# wrong env var) produces a wrong value that the assertions below catch.
REQUIRED_ENV = {
    "MYWHOOSH_EMAIL": "mw-email@example.com",
    "MYWHOOSH_PASSWORD": "mw-password",
    "GARMIN_USERNAME": "garmin-user@example.com",
    "GARMIN_PASSWORD": "garmin-password",
}
OPTIONAL_ENV = ["GARMIN_TOKEN_BASE64", "LOG_LEVEL"]


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    """Run load_config against a clean environment, ignoring any local .env."""
    monkeypatch.setattr(main, "load_dotenv", lambda *a, **kw: None)
    for key in [*REQUIRED_ENV, *OPTIONAL_ENV]:
        monkeypatch.delenv(key, raising=False)


def _set(monkeypatch, **overrides):
    """Apply REQUIRED_ENV plus any overrides; a None override deletes the var."""
    env = {**REQUIRED_ENV, **overrides}
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


def test_load_config_maps_every_env_var_to_its_key(monkeypatch):
    _set(monkeypatch, GARMIN_TOKEN_BASE64="token-store", LOG_LEVEL="DEBUG")

    assert main.load_config() == {
        "mywhoosh_email": "mw-email@example.com",
        "mywhoosh_password": "mw-password",
        "garmin_username": "garmin-user@example.com",
        "garmin_password": "garmin-password",
        "garmin_token_base64": "token-store",
        "log_level": "DEBUG",
    }


def test_load_config_defaults_log_level_to_info(monkeypatch):
    _set(monkeypatch)

    assert main.load_config()["log_level"] == "INFO"


def test_load_config_raises_when_required_var_missing(monkeypatch):
    _set(monkeypatch, MYWHOOSH_EMAIL=None)

    with pytest.raises(ValueError, match="MYWHOOSH_EMAIL"):
        main.load_config()


def test_load_config_accepts_token_instead_of_garmin_password(monkeypatch):
    _set(monkeypatch, GARMIN_PASSWORD=None, GARMIN_TOKEN_BASE64="token-store")

    config = main.load_config()

    assert config["garmin_password"] is None
    assert config["garmin_token_base64"] == "token-store"


def test_load_config_error_names_both_garmin_credential_options(monkeypatch):
    _set(monkeypatch, GARMIN_PASSWORD=None)

    with pytest.raises(ValueError, match="GARMIN_PASSWORD.*GARMIN_TOKEN_BASE64"):
        main.load_config()
