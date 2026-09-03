"""Garmin service for handling authentication and activity uploads."""

import logging
from datetime import datetime
from typing import Any

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


class GarminService:
    """Service for interacting with Garmin Connect."""

    def __init__(self, username: str, password: str, token_base64: str | None = None):
        """Initialize GarminService with credentials.

        Args:
            username: Garmin Connect username
            password: Garmin Connect password
            token_base64: Optional base64 garth token store. When set, login uses
                the saved tokens (works with MFA accounts and headless/CI) instead
                of username/password.
        """
        self.username = username
        self.password = password
        # Tolerate a token that lost its trailing "=" padding in a copy-paste
        # or when stored as a CI secret.
        if token_base64:
            token_base64 = token_base64.strip()
            token_base64 += "=" * (-len(token_base64) % 4)
        self.token_base64 = token_base64
        self.client: Garmin = Garmin(username, password)
        self.logger = logging.getLogger(__name__)
        self._authenticated = False

    def authenticate(self) -> None:
        """Authenticate with Garmin Connect.

        Raises:
            GarminConnectAuthenticationError: Invalid credentials
            GarminConnectTooManyRequestsError: Rate limit exceeded
            GarminConnectConnectionError: Network connection issues
            RuntimeError: Other authentication failures
        """
        self.logger.info("Logging in to Garmin Connect...")

        try:
            if self.token_base64:
                self.logger.info("Using saved Garmin token store (GARMIN_TOKEN_BASE64)")
                self.client.login(self.token_base64)
            else:
                self.client.login()
            self._authenticated = True
            self.logger.info("Successfully authenticated with Garmin Connect")
        except GarminConnectAuthenticationError:
            self.logger.exception("Authentication error. Check your credentials.")
            raise
        except GarminConnectTooManyRequestsError:
            self.logger.exception("Too many requests. Try again later.")
            raise
        except GarminConnectConnectionError:
            self.logger.exception("Connection error. Check your internet connection.")
            raise
        except Exception as e:
            self.logger.exception(f"Failed to login to Garmin Connect: {e}")
            raise RuntimeError(f"Authentication failed: {e}") from e

    def upload_activity(self, fit_file_path: str) -> Any:
        """Upload a .fit file to Garmin Connect.

        Args:
            fit_file_path: Path to the FIT file to upload

        Returns:
            Upload response from Garmin Connect or success dict if 409 Conflict (duplicate)

        Raises:
            RuntimeError: If not authenticated or upload fails (other than 409)
        """
        if not self._authenticated:
            raise RuntimeError("Must authenticate before uploading activities")

        self.logger.info(f"Uploading {fit_file_path} to Garmin Connect...")

        try:
            response = self.client.upload_activity(fit_file_path)
            self.logger.info("Upload successful")
            self.logger.debug(f"Upload response: {response}")
            return response
        except Exception as e:
            error_str = str(e)

            # Handle 409 Conflict gracefully (activity already exists)
            if "409" in error_str or "Conflict" in error_str:
                self.logger.info("⚠ Activity already exists on Garmin Connect (409 Conflict)")
                self.logger.info("Treating as success - no duplicate upload needed")
                return {"status": "skipped", "message": "Activity already exists on Garmin Connect"}

            self.logger.exception(f"Failed to upload activity: {e}")
            raise RuntimeError(f"Upload failed: {e}") from e

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._authenticated

    def check_duplicate_activity(
        self, activity_date: datetime, activity_name: str | None = None, threshold_hours: int = 2
    ) -> bool:
        """Check if an activity already exists on Garmin Connect.

        Uses a time window approach: if an activity exists within
        threshold_hours of the given activity_date, it's considered a duplicate.

        Args:
            activity_date: Date/time when the activity occurred
            activity_name: Optional activity name for additional matching
            threshold_hours: Time window in hours (default: 2)

        Returns:
            True if duplicate found, False otherwise

        Raises:
            RuntimeError: If not authenticated
        """
        if not self._authenticated:
            raise RuntimeError("Must authenticate before checking activities")

        self.logger.info(
            f"Checking for duplicate activity around {activity_date} (±{threshold_hours}h window)"
        )

        try:
            # Get activities for the date
            date_str = activity_date.strftime("%Y-%m-%d")
            activities = self.client.get_activities_by_date(date_str, date_str)

            if not activities:
                self.logger.info("No activities found on this date")
                return False

            self.logger.info(f"Found {len(activities)} activities on {date_str}")

            # Check each activity
            for activity in activities:
                try:
                    # Compare on the underlying UTC instant. beginTimestamp is
                    # epoch milliseconds (UTC) and is timezone-proof; the string
                    # fields are a fallback. activity_date is naive local, so
                    # .timestamp() gives its epoch in the same frame.
                    begin_ms = activity.get("beginTimestamp")
                    if begin_ms is not None:
                        activity_start = datetime.fromtimestamp(begin_ms / 1000)
                    else:
                        start_time_str = activity.get("startTimeLocal", activity.get("startTime"))
                        if not start_time_str:
                            continue
                        activity_start = datetime.fromisoformat(
                            start_time_str.replace("Z", "+00:00")
                        )

                    time_diff = abs(activity_start.timestamp() - activity_date.timestamp()) / 3600

                    if time_diff <= threshold_hours:
                        self.logger.info(
                            f"Found potential duplicate: '{activity.get('activityName')}' "
                            f"at {activity_start} (Δ{time_diff:.2f}h)"
                        )

                        # A near-exact start time is the same ride, even though
                        # Garmin renames indoor rides to the route/world name.
                        if time_diff <= 0.1:  # ~6 minutes
                            self.logger.info("✓ Start time matches - confirmed duplicate")
                            return True

                        # Additional name matching if provided
                        if activity_name:
                            garmin_name = activity.get("activityName", "").lower()
                            if (
                                activity_name.lower() in garmin_name
                                or garmin_name in activity_name.lower()
                            ):
                                self.logger.info("✓ Activity name matches - confirmed duplicate")
                                return True
                            else:
                                self.logger.info("✗ Activity name doesn't match, checking next...")
                                continue
                        else:
                            # No name provided, time match is sufficient
                            return True

                except Exception as e:
                    self.logger.warning(f"Error parsing activity: {e}")
                    continue

            self.logger.info("No duplicate found")
            return False

        except Exception as e:
            self.logger.warning(f"Error checking for duplicates: {e}")
            # Don't block upload if duplicate check fails
            return False
