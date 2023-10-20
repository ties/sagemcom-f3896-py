import re
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(eq=True, frozen=True)
class DownstreamProfileMessage:
    channel_id: int
    previous_profile: Optional[Tuple[int, int]]
    profile: Tuple[int, int]


@dataclass(eq=True, frozen=True)
class UpstreamProfileMessage:
    channel_id: int
    previous_profile: Optional[Tuple[int, int]]
    profile: Tuple[int, int]


@dataclass(eq=True, frozen=True)
class CMStatusMessageOFDM:
    """
    Cable Modem status message for OFDM(A) channel.

    Status codes are defined in table 99 in https://www.cablelabs.com/specifications/CM-SP-MULPIv3.1
    """

    channel_id: int
    ds_id: Optional[str]
    profile: int
    event_code: int


@dataclass(eq=True, frozen=True)
class RebootMessage:
    reason: str


ParsedMessage = (
    CMStatusMessageOFDM
    | DownstreamProfileMessage
    | UpstreamProfileMessage
    | RebootMessage
)


DS_PROFILE_RE = re.compile(
    r"^DS profile assignment change. DS Chan ID: (?P<channel_id>\d+); Previous Profile: (?P<previous_profile>(\d+ \d+ \d+)?); New Profile: (?P<profile>\d+ \d+ \d+)\.;.*$"
)
US_PROFILE_RE = re.compile(
    r"^US profile assignment change. US Chan ID: (?P<channel_id>\d+); Previous Profile: (?P<previous_profile>(\d+ \d+)?); New Profile: (?P<profile>\d+ \d+)\.;.*$"
)
CM_STATUS_OFDM_RE = re.compile(
    r"^CM-STATUS message sent. Event Type Code: (?P<event_code>\d+); Chan ID: (?P<channel_id>\d+); DSID: (?P<ds_id>(\d+|N/A)); MAC Addr: N/A; OFDM/OFDMA Profile ID: (?P<profile>\d+).;.*$"
)
REBOOT_RE = re.compile(r"^Cable Modem Reboot because of - (?P<message>.*)$")


def parse_message(message: str) -> Optional[ParsedMessage]:
    """Parse a message in the modem log"""
    match = CM_STATUS_OFDM_RE.match(message)
    if match:
        ds_id = match.group("ds_id")

        return CMStatusMessageOFDM(
            channel_id=int(match.group("channel_id")),
            ds_id=int(ds_id) if ds_id != "N/A" else None,
            event_code=int(match.group("event_code")),
            profile=int(match.group("profile")),
        )
    match = DS_PROFILE_RE.match(message)
    if match:
        return DownstreamProfileMessage(
            channel_id=int(match.group("channel_id")),
            previous_profile=tuple(map(int, match.group("previous_profile").split()))
            if match.group("previous_profile")
            else None,
            profile=tuple(map(int, match.group("profile").split())),
        )

    match = US_PROFILE_RE.match(message)
    if match:
        return UpstreamProfileMessage(
            channel_id=int(match.group("channel_id")),
            previous_profile=tuple(map(int, match.group("previous_profile").split()))
            if match.group("previous_profile")
            else None,
            profile=tuple(map(int, match.group("profile").split())),
        )

    match = REBOOT_RE.match(message)
    if match:
        return RebootMessage(reason=match.group("message"))
    return None
