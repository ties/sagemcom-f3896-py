from typing import Set

from sagemcom_f3896_client.log_parser import (
    CMStatusMessageOFDM,
    DownstreamProfileMessage,
    RebootMessage,
    UpstreamProfileMessage,
    parse_message,
)

LOG_MESSAGES = [
    "CM-STATUS message sent. Event Type Code: 4; Chan ID: 14 15; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: N/A.;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "CM-STATUS message sent. Event Type Code: 5; Chan ID: 14 15; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: N/A.;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "CM-STATUS message sent. Event Type Code: 1; Chan ID: 14 15; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: N/A.;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "MDD message timeout;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "CM-STATUS message sent. Event Type Code: 2; Chan ID: 14 15; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: N/A.;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "CM-STATUS message sent. Event Type Code: 8; Chan ID: 13 14 15 16; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: N/A.;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "No Ranging Response received - T3 time-out;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "16 consecutive T3 timeouts while trying to range on upstream channel 0;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "Unicast Maintenance Ranging attempted - No response - Retries exhausted;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "Started Unicast Maintenance Ranging - No Response received - T3 time-out;CM-MAC=44:05:3f:92:a2:4a;CMTS-MAC=00:01:5c:aa:8a:4b;CM-QOS=1.1;CM-VER=3.1;",
    "Cable Modem Reboot because of - Software_Upgrade",
    "SW download Successful - Via NMS",
    "SW Download INIT - Via NMS",
    "CM-STATUS message sent. Event Type Code: 8; Chan ID: 27; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: N/A.;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "Unicast Maintenance Ranging attempted - No response - Retries exhausted;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "16 consecutive T3 timeouts while trying to range on upstream channel 8;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
    "Started Unicast Maintenance Ranging - No Response received - T3 time-out;CM-MAC=44:05:a5:a5:a5:4a;CMTS-MAC=00:01:5c:de:ad:be;CM-QOS=1.1;CM-VER=3.1;",
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
    """Test the log parser on the set of real messages."""
    types: Set[type] = set()

    for line in LOG_MESSAGES:
        parsed = parse_message(line)
        types.add(type(parsed))
        match parsed:
            case CMStatusMessageOFDM(
                channel_id=channel_id,
                ds_id=ds_id,
                event_code=event_code,
                profile=profile,
            ):
                if event_code in (16, 24):
                    assert channel_id == 33
                    assert profile == 3
                    assert ds_id is None
                elif event_code == 8:
                    assert channel_id == 8
                    assert profile is None
                    assert ds_id is None
                else:
                    assert False, "Unexpected event code"
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
