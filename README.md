# Sagemcom F3896 client

A client for the Sagemcom F3896 modem.

Main goal of @ties is to have metrics from the modem, but the general structure should allow this libary to be used to add other features.

## Compatibility

| Router model | Provider(s) | Comments |
| -------------------------- | ---------- | --------------------------------- |
| Connectbox Giga (F3896-LG) | Ziggo (NL) | Primary development on this modem |

## Running

For example, using docker compose:
```yaml
version: '3.7'

services:
  sagemcom_exporter:
    image: ghcr.io/ties/sagemcom-f3896-py:latest
    deploy:
      resources:
        limits:
          cpus: 0.1
          memory: 128M
    restart: always
    ports:
      - 8080:8080
    environment:
      MODEM_PASSWORD: PASSWORD123
```

## Changelog

  * 18-10-2023:
    * Keep the profile messages if they expire and channel is still present on
      modem.

## Endpoints

The client implements some endpoints. Others are:
```
GET /rest/v1/system/gateway/provisioning

{"provisioning":{"mode":"disable","macAddress":"44:05:3f:92:a2:4c","dsLite":{"enable":false}}}

GET /rest/v1/system/languages

GET /rest/v1/mta/lines
{"lines":[{"id":1,"line":{"enable":false,"operational":false}},{"id":2,"line":{"enable":false,"operational":false}}]}

GET /rest/v1/wifi/band2g/defaults
{"defaults":{"ssid":{"name":"Ziggo1234567","passphrase":"DEADBEEFjc8pdmko"}}}

GET /rest/v1/system/ui/defaults
{"defaults":{"password":"DEADBEEFpxeo"}}

POST /rest/v1/system/factoryreset
> {"factoryReset":{"enable":true}}
< {"accepted":true}

GET /rest/v1/cablemodem/registration

GET /rest/v1/echo
> {"echoStatus":"success"}
< 

GET /rest/v1/system/firstinstall
{"firstInstall":{"complete":false}}

GET /rest/v1/system/softwareupdate
{"softwareUpdate":{"status":"complete_from_provisioning"}}

POST /rest/v1/user/3/tokens
> {"password":"DEADBEEFxeo"}
< {"created":{"token":"18ae8b1525b76f2b3c151f3dd1c73499","userLevel":"regular"}}

PATCH /rest/v1/user/3/password


PUT /rest/v1/system/firstinstall
> {"password":{"password":"DEADBEEFpxeo","newPassword":"DEADBEEF123"}}
204 No Content

PUT /rest/v1/system/firstinstall
> {"firstInstall":{"complete":true}}
204 No Content
```
