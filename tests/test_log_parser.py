from typing import Set

from sagemcom_f3896_client.log_parser import (
    CMStatusMessageOFDM,
    DownstreamProfileMessage,
    RebootMessage,
    UpstreamProfileMessage,
    parse_line,
)

LOG_MESSAGES = [
    "CM-STATUS message sent. Event Type Code: 24; Chan ID: 33; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: 3.;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "CM-STATUS message sent. Event Type Code: 16; Chan ID: 33; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: 3.;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "US profile assignment change. US Chan ID: 27; Previous Profile: 10 13; New Profile: 9 13.;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "US profile assignment change. US Chan ID: 27; Previous Profile: 9 13; New Profile: 10 13.;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "US profile assignment change. US Chan ID: 27; Previous Profile: 10 13; New Profile: 9 13.;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "US profile assignment change. US Chan ID: 27; Previous Profile: 9 13; New Profile: 10 13.;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "REGISTRATION COMPLETE - Waiting for Operational status",
    "DS profile assignment change. DS Chan ID: 32; Previous Profile: ; New Profile: 1 2 3.;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "TLV-11 - unrecognized OID;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "DHCP WARNING - Non-critical field invalid in response ;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "Honoring MDD; IP provisioning mode = IPv4",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "No Ranging Response received - T3 time-out;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "Cable Modem Reboot because of - Reboot UI",
    "No Ranging Response received - T3 time-out;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "Cable Modem Reboot because of - Reboot UI",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "No Ranging Response received - T3 time-out;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "Cable Modem Reboot because of - Reboot UI",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "Cable Modem Reboot because of - Reboot UI",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "Cable Modem Reboot because of - Reboot UI",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "No Ranging Response received - T3 time-out;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "Cable Modem Reboot because of - Reboot UI",
    "No Ranging Response received - T3 time-out;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
    "No Ranging Response received - T3 time-out;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "SYNC Timing Synchronization failure - Failed to acquire QAM/QPSK symbol timing;;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:00:00:00:00:00;CM-QOS=1.1;CM-VER=3.1;",
]


def test_log_parser_integration_test():
    types: Set[type] = set()

    for line in LOG_MESSAGES:
        parsed = parse_line(line)
        types.add(type(parsed))
        match parsed:
            case CMStatusMessageOFDM(
                channel_id=channel_id,
                ds_id=ds_id,
                event_code=event_code,
                profile=profile,
            ):
                assert channel_id == 33
                assert event_code in (16, 24)
                assert profile == 3
                assert ds_id is None
            case DownstreamProfileMessage(
                channel_id=channel_id,
                previous_profile=previous_profile,
                profile=profile,
            ):
                assert channel_id > 0
                assert len(profile) == 3
                assert profile[0] > 0
                assert profile[1] > profile[0]
                assert profile[2] > profile[1]

                if previous_profile is not None:
                    assert len(previous_profile) == 3
                    assert previous_profile[0] > 0
                    assert previous_profile[1] > previous_profile[0]
                    assert previous_profile[2] > previous_profile[1]
            case UpstreamProfileMessage(
                channel_id=channel_id,
                previous_profile=previous_profile,
                profile=profile,
            ):
                assert channel_id > 0
                assert len(profile) == 2
                assert profile[0] > 0
                assert profile[1] > profile[0]

                if previous_profile is not None:
                    assert previous_profile[0] > 0
                    assert previous_profile[1] > previous_profile[0]
            case RebootMessage(message=message):
                assert "Reboot UI" in message

    assert CMStatusMessageOFDM in types
    assert DownstreamProfileMessage in types
    assert UpstreamProfileMessage in types
    assert RebootMessage in types
