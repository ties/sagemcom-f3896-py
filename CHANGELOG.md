## 2024-08-31 (v0.6.1)

  * Fix bug in channel profile store: while it would not happen in practice, 
    downstream and upstream channels with same number would cause messages to be kept
    while channel would be gone for their channel type.
  * Improved tests of channel profile store.
  * **removed `modem_downstream_errors` and `modem_upstream_timeouts`.

## 2024-8-29 (v0.6.0)

  * Update dependencies
  * Document `MODEM_URL` option
  * Add `node_boot_time_seconds` metric calculated from uptime.
  * Add `modem_downstream_errors_total` that will replace
    `modem_downstream_errors` metric (clearer name).
  * **deprecated** the `modem_downstream_errors` metric. Will be removed on or after 1-7-2024.

## 2024-03-09 (v0.5.0)

  * Enable dependabot dependency management
  * Add `modem_upstream_timeout_count` metric that will replace
    `modem_upstream_timeouts` metric (clearer name).
  * **deprecated** `modem_upstream_timeouts` metric. Will be removed on or after 1-5-20204.

## 2024-02-17 (v0.4.1)

  * fix: `modem_upstream_ofdm` metric is now called `modem_upstream_ofdma`
  * fix: Return metrics when login fails (main cause: concurrent login)

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
