from typing import Optional, Set
from unittest.mock import Mock

from sagemcom_f3896_client.log_parser import (
    DownstreamProfileMessage,
    UpstreamProfileMessage,
)
from sagemcom_f3896_client.models import (
    ModemDownstreamChannelResult,
    ModemUpstreamChannelResult,
)
from sagemcom_f3896_client.profile_messages import ProfileMessageStore


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
    channel_id: int, profile: Set[int], old_profile: Optional[Set[int]] = None
) -> UpstreamProfileMessage:
    return UpstreamProfileMessage(
        channel_id=channel_id,
        previous_profile=tuple(old_profile) if old_profile else None,
        profile=tuple(profile),
    )


def test_profile_messages():
    store = ProfileMessageStore()

    assert len(store) == 0

    store.add(ds_message(1, [1, 2, 3], None))
    assert len(store) == 1
    assert ds_message(1, [1, 2, 3], None) in store

    # drop a profile/overwrite
    store.add(ds_message(1, [1, 3], None))
    assert len(store) == 1
    assert ds_message(1, [1, 3], None) in store

    # but a upstream message can be added in parallel for the channel
    store.add(us_message(1, [9, 13], None))
    assert len(store) == 2
    assert ds_message(1, [1, 3], None) in store
    assert us_message(1, [9, 13]) in store

    # Add second upstream
    store.add(us_message(2, [10, 12], None))
    assert len(store) == 3
    assert ds_message(1, [1, 3], None) in store
    assert us_message(1, [9, 13]) in store
    assert us_message(2, [10, 12]) in store

    # And if the channels are present they stay
    store.update_for_channels([channel(1)], [channel(1), channel(2)])

    assert len(store) == 3
    assert ds_message(1, [1, 3], None) in store
    assert us_message(1, [9, 13]) in store
    assert us_message(2, [10, 12]) in store

    # But are removed when channel disappears
    # remove an upstream first
    store.update_for_channels([channel(1)], [channel(2)])
    assert len(store) == 2
    assert ds_message(1, [1, 3], None) in store
    assert us_message(2, [10, 12]) in store

    # Now remove a downstream
    assert store.update_for_channels([], [channel(2)]) == 1
    assert len(store) == 1
    assert us_message(2, [10, 12]) in store

    # With no channels, it should be empty
    assert store.update_for_channels([], []) == 1
    assert len(store) == 0
