import logging
import time

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Literal, Optional

import aiohttp

from .models import (
    AuthorisationResult,
    EventLogItem,
    ModemATDMAUpstreamChannelResult,
    ModemOFDMAUpstreamChannelResult,
    ModemOFDMDownstreamChannelResult,
    ModemQAMDownstreamChannelResult,
    ModemServiceFlowResult,
    ModemStateResult,
    SystemInfoResult,
)

LOG = logging.getLogger(__name__)


UNAUTHORIZED_ENDPOINTS = [
    "rest/v1/user/login",
    "rest/v1/cablemodem/downstream/primary_",
    "rest/v1/cablemodem/state_",
    "rest/v1/cablemodem/downstream",
    "rest/v1/cablemodem/upstream",
    "rest/v1/cablemodem/eventlog",
    "rest/v1/cablemodem/serviceflows",
]

for endpoint in set(UNAUTHORIZED_ENDPOINTS):
    assert not endpoint.startswith("/"), "URLs should be relative"


class SagemcomModemSessionClient:
    __session: aiohttp.ClientSession
    base_url: str
    password: str
    authorization: Optional[AuthorisationResult] = None

    def __init__(
        self, session: aiohttp.ClientSession, base_url: str, password: str
    ) -> None:
        assert session
        self.__session = session

        self.base_url = base_url
        self.password = password

    def __headers(self) -> Dict[str, str]:
        return {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Referer": self.base_url,
            "Origin": self.base_url,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }

    async def _login(self) -> Dict[str, str]:
        async with self.__request(
            "POST", "/rest/v1/user/login", {"password": self.password}
        ) as res:
            assert res.status == 201

            body = await res.json()
            self.authorization = AuthorisationResult.build(body)

    async def _logout(self) -> None:
        if self.authorization:
            LOG.info("Logging out session userId=%d", self.authorization.user_id)
            async with self.__request(
                "DELETE",
                f"/rest/v1/user/{self.authorization.user_id}/token/{self.authorization.token}",
            ) as res:
                assert res.status == 204
                self.authorization = None

    @asynccontextmanager
    async def __request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        json: Optional[object] = None,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[aiohttp.ClientResponse, None]:
        path = path[1:] if path.startswith("/") else path
        url = f"{self.base_url if not self.base_url.endswith('/') else self.base_url[:-1]}/{path}"

        headers = self.__headers()
        if path not in UNAUTHORIZED_ENDPOINTS:
            # log in because this endpoint requires authentication
            if not self.authorization:
                LOG.debug("logging in because '%s' requires authentication", path)
                await self._login()
            headers["Authorization"] = f"Bearer {self.authorization.token}"


        t0 = time.time()

        async with self.__session.request(
            method,
            url,
            headers=headers,
            json=json,
            raise_for_status=raise_for_status,
        ) as resp:
            LOG.debug(
                "%s %s %s %.3f %s",
                method,
                url,
                resp.status,
                time.time() - t0,
                resp.reason,
            )
            yield resp

    async def modem_event_log(self) -> List[EventLogItem]:
        async with self.__request("GET", "/rest/v1/cablemodem/eventlog") as resp:
            res = await resp.json()
            return [EventLogItem.build(e) for e in res["eventlog"]]

    async def modem_service_flows(self) -> List[ModemServiceFlowResult]:
        async with self.__request("GET", "/rest/v1/cablemodem/serviceflows") as resp:
            res = await resp.json()
            return [ModemServiceFlowResult.build(e) for e in res["serviceFlows"]]

    async def system_info(self) -> SystemInfoResult:
        async with self.__request("GET", "/rest/v1/system/info") as resp:
            return SystemInfoResult.build(await resp.json())

    async def system_state(self) -> ModemStateResult:
        async with self.__request("GET", "/rest/v1/cablemodem/state_") as resp:
            return ModemStateResult.build(await resp.json())

    async def modem_downstreams(
        self,
    ) -> List[ModemQAMDownstreamChannelResult | ModemOFDMDownstreamChannelResult]:
        async with self.__request("GET", "/rest/v1/cablemodem/downstream") as resp:
            return [
                ModemQAMDownstreamChannelResult.build(e)
                if e["channelType"] == "sc_qam"
                else ModemOFDMDownstreamChannelResult.build(e)
                for e in (await resp.json())["downstream"]["channels"]
            ]

    async def modem_upstreams(
        self,
    ) -> List[ModemATDMAUpstreamChannelResult | ModemOFDMAUpstreamChannelResult]:
        async with self.__request("GET", "/rest/v1/cablemodem/upstream") as resp:
            return [
                ModemATDMAUpstreamChannelResult.build(e)
                if e["channelType"] == "atdma"
                else ModemOFDMAUpstreamChannelResult.build(e)
                for e in (await resp.json())["upstream"]["channels"]
            ]


@asynccontextmanager
async def SagemcomModemClient(
    base_url: str, password: str, timeout: int = 5
) -> AsyncGenerator[SagemcomModemSessionClient, None]:
    timeout = aiohttp.ClientTimeout(total=timeout)
    conn = aiohttp.TCPConnector(limit_per_host=30)

    async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
        client = SagemcomModemSessionClient(session, base_url, password)
        yield client
        await client._logout()
