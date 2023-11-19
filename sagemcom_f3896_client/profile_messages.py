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
        all_channels = frozenset(c.channel_id for c in ds_channels) | frozenset(
            c.channel_id for c in us_channels
        )
        removed = 0
        for message in list(self._messages):
            if message.channel_id not in all_channels:
                LOG.info(
                    "Dropping profile message for no longer present downstream channel %d",
                    message.channel_id,
                )
                self._messages.remove(message)
                removed += 1

        return removed

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
