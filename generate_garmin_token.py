#!/usr/bin/env python3
"""Generate a Garmin Connect token store for headless / GitHub Actions use.

Run this ONCE on your own machine:

    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python generate_garmin_token.py

It logs in (handling MFA if your account has it), then prints a base64 blob.
Copy that blob into a GitHub Actions secret named GARMIN_TOKEN_BASE64.

Tokens are valid ~1 year; re-run this when Garmin auth starts failing.
"""

import getpass
import sys

from garminconnect import Garmin


def main() -> int:
    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password: ")

    client = Garmin(email, password, prompt_mfa=lambda: input("MFA code: ").strip())
    client.login()

    token_b64 = client.garth.dumps()
    print("\n" + "=" * 70)
    print("GARMIN_TOKEN_BASE64 (add this as a GitHub Actions secret):")
    print("=" * 70)
    print(token_b64)
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
