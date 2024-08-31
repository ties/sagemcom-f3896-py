import logging
from typing import List, Set

from sagemcom_f3896_client.log_parser import (
    DownstreamProfileMessage,
    UpstreamProfileMessage,
)
from sagemcom_f3896_client.models import (
    ModemDownstreamChannelResult,
    ModemUpstreamChannelResult,
)

LOG = logging.getLogger(__name__)


class ProfileMessageStore:
    """Keep track of profile messages for channels that are still present"""

    _messages: Set[DownstreamProfileMessage | UpstreamProfileMessage]

    def __init__(self):
        self._messages = set()

    def update_for_channels(
        self,
        ds_channels: List[ModemDownstreamChannelResult],
        us_channels: List[ModemUpstreamChannelResult],
    ) -> int:
        ds_channels_ids = frozenset(c.channel_id for c in ds_channels)
        us_channel_ids = frozenset(c.channel_id for c in us_channels)

        removed = []
        for message in list(self._messages):
            match message:
                case DownstreamProfileMessage(
                    channel_id=channel_id
                ) if channel_id not in ds_channels_ids:
                    removed.append(message)
                case UpstreamProfileMessage(
                    channel_id=channel_id
                ) if channel_id not in us_channel_ids:
                    removed.append(message)

        # do not remove while iterating
        for message in removed:
            self._messages.remove(message)
            LOG.info(
                "Dropping profile message for no longer present channel %d (previous profile: %s, new: %s)",
                message.channel_id,
                message.previous_profile,
                message.profile,
            )

        return len(removed)

    def add(self, message: DownstreamProfileMessage | UpstreamProfileMessage):
        """Add a messsage, removing a message of that type for that channel if present."""
        for existing in list(self._messages):
            if existing.channel_id == message.channel_id and isinstance(
                message, type(existing)
            ):
                self._messages.remove(existing)

        return self._messages.add(message)

    def remove(self, message: DownstreamProfileMessage | UpstreamProfileMessage):
        """Remove a message."""
        self._messages.remove(message)

    def __iter__(self):
        return iter(self._messages)

    def __len__(self):
        return len(self._messages)
