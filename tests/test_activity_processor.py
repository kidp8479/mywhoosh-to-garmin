from datetime import datetime
from unittest.mock import MagicMock

import pytest

from services.activity_processor import ActivityProcessor

ACTIVITY = {"id": "act-1", "name": "Morning Ride", "date": "2026-09-01T07:30:00Z"}


@pytest.fixture
def services():
    """Three mocked collaborators wired for the happy path."""
    mywhoosh = MagicMock()
    mywhoosh.get_latest_activity.return_value = ACTIVITY
    mywhoosh.get_activities.return_value = [ACTIVITY]
    mywhoosh.download_activity.return_value = "/tmp/act-1.fit"

    fit_file = MagicMock()
    fit_file.modify_device_info.return_value = "/tmp/act-1-edge840.fit"

    garmin = MagicMock()
    garmin.is_authenticated.return_value = False
    garmin.check_duplicate_activity.return_value = False

    return mywhoosh, fit_file, garmin


def test_init_stores_collaborators():
    mywhoosh, fit_file, garmin = MagicMock(), MagicMock(), MagicMock()

    ap = ActivityProcessor(mywhoosh, fit_file, garmin)

    assert ap.mywhoosh_service is mywhoosh
    assert ap.fit_file_service is fit_file
    assert ap.garmin_service is garmin


def test_latest_activity_runs_the_full_pipeline(services):
    mywhoosh, fit_file, garmin = services

    ok = ActivityProcessor(mywhoosh, fit_file, garmin).process_latest_activity()

    assert ok is True
    mywhoosh.authenticate.assert_called_once()
    mywhoosh.download_activity.assert_called_once_with(ACTIVITY)
    fit_file.modify_device_info.assert_called_once_with("/tmp/act-1.fit")
    garmin.upload_activity.assert_called_once_with("/tmp/act-1-edge840.fit")
    # both temp files cleaned up in the finally block
    assert fit_file.cleanup_file.call_count == 2


def test_latest_activity_returns_false_when_nothing_to_sync(services):
    mywhoosh, fit_file, garmin = services
    mywhoosh.get_latest_activity.return_value = None

    ok = ActivityProcessor(mywhoosh, fit_file, garmin).process_latest_activity()

    assert ok is False
    mywhoosh.download_activity.assert_not_called()
    garmin.upload_activity.assert_not_called()


def test_latest_activity_skips_upload_on_duplicate(services):
    mywhoosh, fit_file, garmin = services
    garmin.check_duplicate_activity.return_value = True

    ok = ActivityProcessor(mywhoosh, fit_file, garmin).process_latest_activity()

    # a skipped duplicate is a success, not a failure
    assert ok is True
    mywhoosh.download_activity.assert_not_called()
    garmin.upload_activity.assert_not_called()


def test_latest_activity_returns_false_and_cleans_up_on_upload_failure(services):
    mywhoosh, fit_file, garmin = services
    garmin.upload_activity.side_effect = RuntimeError("Garmin 500")

    ok = ActivityProcessor(mywhoosh, fit_file, garmin).process_latest_activity()

    assert ok is False
    assert fit_file.cleanup_file.call_count == 2  # finally still ran


def test_latest_activity_can_disable_duplicate_check(services):
    mywhoosh, fit_file, garmin = services

    ActivityProcessor(mywhoosh, fit_file, garmin).process_latest_activity(check_duplicates=False)

    garmin.check_duplicate_activity.assert_not_called()


def test_multiple_activities_tallies_synced_skipped_and_errored(services):
    mywhoosh, fit_file, garmin = services
    good = {"id": "a", "name": "A", "date": "2026-09-01T07:00:00Z"}
    dupe = {"id": "b", "name": "B", "date": "2026-09-02T07:00:00Z"}
    bad = {"id": "c", "name": "C", "date": "2026-09-03T07:00:00Z"}
    mywhoosh.get_activities.return_value = [good, dupe, bad]
    garmin.check_duplicate_activity.side_effect = [False, True, False]
    garmin.upload_activity.side_effect = [None, RuntimeError("boom")]

    stats = ActivityProcessor(mywhoosh, fit_file, garmin).process_multiple_activities(limit=3)

    assert stats == {"total": 3, "synced": 1, "skipped": 1, "errors": 1}


@pytest.mark.parametrize(
    "raw",
    [
        "2026-09-01T07:30:00Z",
        "2026-09-01T07:30:00.500Z",
        "2026-09-01 07:30:00",
        "2026-09-01",
        "1756711800",
    ],
)
def test_parse_activity_date_accepts_known_formats(raw):
    ap = ActivityProcessor(MagicMock(), MagicMock(), MagicMock())

    assert isinstance(ap._parse_activity_date(raw), datetime)


def test_parse_activity_date_returns_none_for_garbage():
    ap = ActivityProcessor(MagicMock(), MagicMock(), MagicMock())

    assert ap._parse_activity_date("not-a-date") is None
    assert ap._parse_activity_date(None) is None
