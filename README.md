# MyWhoosh to Garmin Connect

MyWhoosh has no integration with Garmin Connect. If you ride indoors on MyWhoosh
but keep your training history on Garmin, every ride means exporting a FIT file
by hand and uploading it somewhere else.

This is a fork of [marcelorodrigo/mywhoosh-to-garmin](https://github.com/marcelorodrigo/mywhoosh-to-garmin)
adapted to run on its own, on a schedule, with no machine to keep switched on.
Twice a day a GitHub Actions job checks MyWhoosh for a new activity. If it finds
one it has not seen before, it rewrites the FIT file so Garmin records it as
coming from an Edge 840, then uploads it to Garmin Connect. If there is nothing
new, or the ride is already on Garmin, it does nothing.

## Credit

All the hard parts (talking to the MyWhoosh API, parsing and rebuilding FIT
files, the duplicate check) are the work of Marcelo Rodrigo in the
[upstream project](https://github.com/marcelorodrigo/mywhoosh-to-garmin),
released under GPL-3.0.

## What this fork changes

* Runs on GitHub Actions instead of a local cron job. The workflow lives at
  `.github/workflows/sync.yml`, runs twice a day, and can also be started by hand
  from the Actions tab.
* Logs in to Garmin with a saved token instead of a password. Password login
  breaks as soon as the account hits MFA or a captcha, which does not work for
  an unattended job. `generate_garmin_token.py` logs in once on your own
  machine and prints a token blob you store as a secret. It lasts about a year.
* Config comes from environment variables and Actions secrets, and the run log
  is uploaded as an artifact when a job fails.

## Running it on GitHub Actions

1. This fork is public, so do not put real values anywhere in the code. All
   credentials go into Actions secrets.
2. Generate a Garmin token once, on your own machine:

   ```bash
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python generate_garmin_token.py
   ```

   It asks for your Garmin email, password, and MFA code if you use one, then
   prints a base64 blob.

3. In the repo, open Settings > Secrets and variables > Actions and add:

   | Secret | Value |
   |--------|-------|
   | `MYWHOOSH_EMAIL` | your MyWhoosh email |
   | `MYWHOOSH_PASSWORD` | your MyWhoosh password |
   | `GARMIN_USERNAME` | your Garmin email |
   | `GARMIN_TOKEN_BASE64` | the blob from step 2 |

4. Open the Actions tab, enable workflows, and run "Sync MyWhoosh to Garmin"
   once by hand to check it works.

When the job starts failing on Garmin auth, the token has expired. Re-run
`generate_garmin_token.py` and update the secret. To change how often it runs,
edit the `cron:` line in the workflow.

## Running it locally

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then fill it in
python main.py
```

For local use you can put a plain `GARMIN_PASSWORD` in `.env` instead of a
token, as long as your Garmin account is not behind MFA. See `.env.example`
for the options.

A crontab line works too:

```bash
0 * * * * cd /path/to/mywhoosh-to-garmin && ./venv/bin/python main.py >> sync.log 2>&1
```

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

* Garmin auth fails on Actions: the token expired, regenerate it.
* MyWhoosh auth fails: check the credentials, and open the MyWhoosh app to
  confirm the account and that the ride actually synced.
* "Duplicate detected": not an error, the ride is already on Garmin.
* Upload fails: check [status.garmin.com](https://status.garmin.com), read
  `mywhoosh_to_garmin.log`, try again in a few minutes.
* Cannot find a download URL: the MyWhoosh activity format may have changed.
  The log shows the keys it saw.

## Limitations

* One activity at a time, the latest one. No bulk backfill.
* Duplicate detection is a 2 hour time window, not a content hash.
* MyWhoosh download URLs are short lived.

## License

GPL-3.0, same as the upstream project.
