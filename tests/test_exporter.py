from typing import Optional, Set
from unittest.mock import Mock

from sagemcom_f3896_client.exporter import ProfileMessages
from sagemcom_f3896_client.log_parser import (
    DownstreamProfileMessage,
    UpstreamProfileMessage,
)
from sagemcom_f3896_client.models import (
    ModemDownstreamChannelResult,
    ModemUpstreamChannelResult,
)


def test_profile_messages():
    store = ProfileMessages()

    assert len(store) == 0

    store.add(ds_message(1, [1, 2, 3], None))
    assert len(store) == 1
    # drop a profile/overwrite
    store.add(ds_message(1, [1, 3], None))
    assert len(store) == 1

    # but a upstream message can be added in parallel for the channel
    store.add(us_message(1, [9, 13], None))
    assert len(store) == 2

    # Add second upstream
    store.add(us_message(2, [9, 13], None))
    assert len(store) == 3

    # And if the channels are present they stay
    store.update_for_channels([channel(1)], [channel(1), channel(2)])

    assert len(store) == 3

    # But are removed when channel disappears
    store.update_for_channels([], [channel(2)])
    assert len(store) == 1


def channel(id: int) -> ModemDownstreamChannelResult | ModemUpstreamChannelResult:
    res = Mock()
    res.channel_id = id

    return res


def ds_message(
    channel_id: int, profile: Set[int], old_profile: Optional[Set[int]]
) -> DownstreamProfileMessage:
    return DownstreamProfileMessage(
        channel_id=channel_id,
        previous_profile=tuple(old_profile) if old_profile else None,
        profile=tuple(profile),
    )


def us_message(
    channel_id: int, profile: Set[int], old_profile: Optional[Set[int]]
) -> UpstreamProfileMessage:
    return UpstreamProfileMessage(
        channel_id=channel_id,
        previous_profile=tuple(old_profile) if old_profile else None,
        profile=tuple(profile),
    )
