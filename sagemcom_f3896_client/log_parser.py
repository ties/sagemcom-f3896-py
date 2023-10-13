import re
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class DownstreamProfileMessage:
    channel_id: int
    previous_profile: Optional[Tuple[int, int]]
    profile: Tuple[int, int]


@dataclass
class UpstreamProfileMessage:
    channel_id: int
    previous_profile: Optional[Tuple[int, int]]
    profile: Tuple[int, int]


@dataclass
class CMStatusMessageOFDM:
    """
    Cable Modem status message for OFDM(A) channel.

    Status codes are defined in table 99 in https://www.cablelabs.com/specifications/CM-SP-MULPIv3.1
    """

    channel_id: int
    ds_id: Optional[str]
    profile: int
    event_code: int


ParsedMessage = DownstreamProfileMessage | UpstreamProfileMessage | CMStatusMessageOFDM


DS_PROFILE_RE = re.compile(
    r"DS profile assignment change. DS Chan ID: (?P<channel_id>\d+); Previous Profile: (?P<previous_profile>(\d+ \d+ \d+)?); New Profile: (?P<profile>\d+ \d+ \d+)\.;.*"
)  #
US_PROFILE_RE = re.compile(
    r"US profile assignment change. US Chan ID: (?P<channel_id>\d+); Previous Profile: (?P<previous_profile>(\d+ \d+)?); New Profile: (?P<profile>\d+ \d+)\.;.*"
)
CM_STATUS_OFDM_RE = re.compile(
    r"CM-STATUS message sent. Event Type Code: (?P<event_code>\d+); Chan ID: (?P<channel_id>\d+); DSID: (?P<ds_id>(\d+|N/A)); MAC Addr: N/A; OFDM/OFDMA Profile ID: (?P<profile>\d+).;.*",
)


def parse_line(line: str) -> Optional[ParsedMessage]:
    match = CM_STATUS_OFDM_RE.match(line)
    if match:
        ds_id = match.group("ds_id")

        return CMStatusMessageOFDM(
            channel_id=int(match.group("channel_id")),
            ds_id=int(ds_id) if ds_id != "N/A" else None,
            event_code=int(match.group("event_code")),
            profile=int(match.group("profile")),
        )
    match = DS_PROFILE_RE.match(line)
    if match:
        return DownstreamProfileMessage(
            channel_id=int(match.group("channel_id")),
            previous_profile=tuple(map(int, match.group("previous_profile").split()))
            if match.group("previous_profile")
            else None,
            profile=tuple(map(int, match.group("profile").split())),
        )

    match = US_PROFILE_RE.match(line)
    if match:
        return UpstreamProfileMessage(
            channel_id=int(match.group("channel_id")),
            previous_profile=tuple(map(int, match.group("previous_profile").split()))
            if match.group("previous_profile")
            else None,
            profile=tuple(map(int, match.group("profile").split())),
        )
    return None
