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
