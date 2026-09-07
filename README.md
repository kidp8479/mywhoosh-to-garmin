# MyWhoosh to Garmin Connect

A command-line tool that copies your latest MyWhoosh indoor ride into Garmin
Connect, with the ride attributed to a Garmin Edge 840 so it counts towards your
training load like any other bike computer.

MyWhoosh has no Garmin integration. Without this, every indoor ride means
exporting a FIT file by hand and uploading it somewhere else. Here you run one
command after a ride and it is done.

This is a personal fork of
[marcelorodrigo/mywhoosh-to-garmin](https://github.com/marcelorodrigo/mywhoosh-to-garmin).
See [Differences from upstream](#differences-from-upstream).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```bash
MYWHOOSH_EMAIL=you@example.com
MYWHOOSH_PASSWORD=...
GARMIN_USERNAME=you@example.com     # your Garmin email
GARMIN_PASSWORD=...
```

If your Garmin account uses MFA, a password login will not work. Instead run
`python generate_garmin_token.py` once, and put the base64 blob it prints into
`GARMIN_TOKEN_BASE64` in `.env` (leave `GARMIN_PASSWORD` unset). The token lasts
about a year.

## Usage

After a ride:

```bash
./sync.sh              # sync the latest activity
./sync.sh --batch 5    # or catch up the last 5 activities
```

`sync.sh` is a thin wrapper around `.venv/bin/python main.py`. Duplicate
detection means re-running it is always safe — a ride already on Garmin is
skipped.

## Automating it

There is a GitHub Actions workflow at `.github/workflows/sync.yml`, **kept for
reference but disabled**. Garmin rejects logins from GitHub Actions IP ranges
with a hard `429 Too Many Requests`, so scheduled runs there fail every time.
The same is true of most cloud/shared IPs.

If you have a machine at home that is always on, a cron job works:

```cron
30 21 * * *  cd /path/to/mywhoosh-to-garmin && ./sync.sh >> cron.log 2>&1
```

Otherwise, running it by hand after each ride is the intended workflow.

## Differences from upstream

* `GARMIN_TOKEN_BASE64` as an alternative to a password, for MFA accounts and
  any non-interactive use.
* A bounded retry with backoff when Garmin returns `429` on login.
* ruff + mypy + a CI workflow (`ci.yml`) running format, lint, typecheck and
  tests on every push and PR; more coverage on `garmin_service`.
* Dead Zwift code removed; GPL-3.0 `LICENSE` file added.
* `sync.sh` wrapper.

## How a run goes

1. Authenticate with MyWhoosh (official API, no captcha).
2. Fetch the latest activity.
3. Check Garmin Connect for a matching activity in a 2 hour window. If it is
   already there, stop.
4. Download the FIT file (handles the `.dms` extension MyWhoosh sometimes uses).
5. Rewrite the device info to Garmin Edge 840 (manufacturer 1, product 4024).
6. Upload to Garmin Connect.
7. Delete the temporary files.

Logs go to the console and to `mywhoosh_to_garmin.log`.

## Changing the device

To make the FIT file look like a different Garmin unit, change the `product`
default in `services/fit_file_service.py` (around line 44). For example, `3121`
is an Edge 530.

## When it does not work

* **Garmin auth fails with `429`**: you are rate limited on the OAuth
  token-exchange endpoint. Wait (minutes to hours) and avoid rapid re-runs.
  From a home IP this is rare; from a shared or cloud IP it is close to
  permanent.
* **Garmin auth fails on credentials**: check `GARMIN_USERNAME` /
  `GARMIN_PASSWORD`, and whether the account now needs MFA — if so, switch to
  `GARMIN_TOKEN_BASE64`.
* **MyWhoosh auth fails**: check the credentials, and open the MyWhoosh app to
  confirm the ride actually synced.
* **"Duplicate detected"**: not an error, the ride is already on Garmin.
* **Upload fails**: check [status.garmin.com](https://status.garmin.com), read
  `mywhoosh_to_garmin.log`, try again in a few minutes.
* **Cannot find a download URL**: the MyWhoosh activity format may have changed.
  The log shows the keys it saw.

## Limitations

* One activity at a time by default, the latest. `--batch N` covers the last N.
  No full backfill.
* Duplicate detection is a 2 hour time window, not a content hash.
* MyWhoosh download URLs are short lived.

## License

GPL-3.0, same as the upstream project.
