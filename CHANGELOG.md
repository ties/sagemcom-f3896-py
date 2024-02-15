## 2024-xx-yy (v0.4.1)

  * fix: `modem_upstream_ofdm` metric is now called `modem_upstream_ofdma`

## 2024-02-xx (v0.4.0)

  * 10 second timeout for fetching data
  * Keep previous metrics when a fetch fails (or times out).
  * Metrics duration now tracks fetching time, not web request delay.
  * Uses locking to prevent concurrent update requests

## 2024-02-09 (v0.3.1)

  * Container based on python 3.12
  * Parse more sample log messages
  * Updated dependencies

## 2023-12-30 (v0.3.0):

  * Fixed a bug where the metrics endpoint would break if the modem forgot
    about the session (for example: reboot while a session was active).
  * Updated pre-commit hooks
  * cli `logs` command prints all log entries (except for logins), not first 10.

## 2023-12-19 (v0.2.1)

  * Filter the "login success" messages by default.

## 2023-12-11 (v0.2.0)

  * Add a stable sort for event log items and use it in the web
    index page.
  * Build with Python 3.12
  * Update pre-commit settings
  * Log new modem log items with `f3896.eventlog` tag:
```
INFO:f3896.eventlog:2023-12-09T19:46:45+00:00 [notice]: US profile assignment change. US Chan ID: 27; Previous Profile: 10 13; New Profile: 11 13.;CM-MAC=44:05:de:ad:be:ef;CMTS-MAC=00:01:de:ad:be:ef;CM-QOS=1.1;CM-VER=3.1;
INFO:f3896.eventlog:2023-12-09T18:36:26+00:00 [notice]: US profile assignment change. US Chan ID: 27; Previous Profile: 9 13; New Profile: 10 13.;CM-MAC=44:05:de:ad:be:ef;CMTS-MAC=00:01:de:ad:be:ef;CM-QOS=1.1;CM-VER=3.1;
```
  * Log these messages in chronological order (newest last)
