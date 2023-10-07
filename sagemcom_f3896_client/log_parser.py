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


ParsedMessage = DownstreamProfileMessage | UpstreamProfileMessage


DS_PROFILE_RE = re.compile(
    r"DS profile assignment change. DS Chan ID: (?P<channel_id>\d+); Previous Profile: (?P<previous_profile>(\d+ \d+ \d+)?); New Profile: (?P<profile>\d+ \d+ \d+)\.;.*"
)  #
US_PROFILE_RE = re.compile(
    r"US profile assignment change. US Chan ID: (?P<channel_id>\d+); Previous Profile: (?P<previous_profile>(\d+ \d+)?); New Profile: (?P<profile>\d+ \d+)\.;.*"
)


def parse_line(line: str) -> Optional[ParsedMessage]:
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
