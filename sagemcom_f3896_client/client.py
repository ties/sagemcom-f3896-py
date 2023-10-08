import asyncio
import logging
import operator
import time
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import AsyncGenerator, Dict, List, Literal, Optional

import aiohttp

from sagemcom_f3896_client.exception import LoginFailedException

from .models import (
    EventLogItem,
    ModemATDMAUpstreamChannelResult,
    ModemOFDMAUpstreamChannelResult,
    ModemOFDMDownstreamChannelResult,
    ModemQAMDownstreamChannelResult,
    ModemServiceFlowResult,
    ModemStateResult,
    SystemInfoResult,
    SystemProvisioningResponse,
    UserAuthorisationResult,
    UserTokenResult,
)

LOG = logging.getLogger(__name__)


UNAUTHORIZED_ENDPOINTS = set(
    [
        "rest/v1/user/login",
        "rest/v1/cablemodem/downstream/primary_",
        "rest/v1/cablemodem/state_",
        "rest/v1/cablemodem/downstream",
        "rest/v1/cablemodem/upstream",
        "rest/v1/cablemodem/eventlog",
        "rest/v1/cablemodem/serviceflows",
        "rest/v1/cablemodem/registration",
        "rest/v1/system/gateway/provisioning",
        "rest/v1/echo",
    ]
)

for endpoint in UNAUTHORIZED_ENDPOINTS:
    assert not endpoint.startswith("/"), "URLs should be relative"


def requires_auth(path: str) -> bool:
    return path not in UNAUTHORIZED_ENDPOINTS


class SagemcomModemSessionClient:
    __session: aiohttp.ClientSession
    base_url: str
    password: str
    authorization: Optional[UserAuthorisationResult] = None

    __login_semaphore = asyncio.Semaphore(1)

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
            "Referer": self.base_url,
            "Origin": self.base_url,
        }

    async def _login(self) -> Dict[str, str]:
        try:
            async with self.__request(
                "POST", "/rest/v1/user/login", {"password": self.password}
            ) as res:
                assert res.status == 201

                body = await res.json()
                self.authorization = UserAuthorisationResult.build(body)
        except aiohttp.ClientResponseError as e:
            raise LoginFailedException(
                "Failed to login to modem at %s" % self.base_url
            ) from e

    async def user_tokens(self, user_id, password) -> UserTokenResult:
        async with self.__request(
            "POST",
            f"/rest/v1/user/{user_id}/tokens",
            {"password": password},
            disable_auth=True,
        ) as res:
            assert res.status == 201
            result = UserTokenResult.build(await res.json())
            # Update the token we use iff it got replaced
            if self.authorization and self.authorization.user_id == user_id:
                self.authorization.token = result.token

            return result

    async def delete_token(self, user_id, token) -> None:
        async with self.__request(
            "DELETE", f"/rest/v1/user/{user_id}/token/{token}"
        ) as res:
            assert res.status == 204

    async def _logout(self) -> None:
        async with self.__login_semaphore:
            if self.authorization:
                LOG.debug("Logging out session userId=%d", self.authorization.user_id)
                await self.delete_token(
                    self.authorization.user_id, self.authorization.token
                )
                self.authorization = None

    @asynccontextmanager
    async def __request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        json: Optional[object] = None,
        raise_for_status: bool = True,
        disable_auth: bool = False,
    ) -> AsyncGenerator[aiohttp.ClientResponse, None]:
        path = path[1:] if path.startswith("/") else path
        url = f"{self.base_url if not self.base_url.endswith('/') else self.base_url[:-1]}/{path}"

        headers = self.__headers()
        if not disable_auth and requires_auth(path):
            # log in because this endpoint requires authentication
            if not self.authorization:
                async with self.__login_semaphore:
                    # re-check since parallel thread that was also waiting may have logged in
                    if not self.authorization:
                        LOG.debug(
                            "logging in because '%s' requires authentication", path
                        )
                        await self._login()
            headers["Authorization"] = f"Bearer {self.authorization.token}"

        if json:
            headers["Content-Type"] = "application/json"

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

    async def echo(self, body: object) -> object:
        async with self.__request("POST", "/rest/v1/echo", json=body) as resp:
            return await resp.json()

    async def modem_event_log(self) -> List[EventLogItem]:
        async with self.__request("GET", "/rest/v1/cablemodem/eventlog") as resp:
            res = await resp.json()
            return sorted(
                [EventLogItem.build(e) for e in res["eventlog"]],
                key=operator.attrgetter("time"),
                reverse=True,
            )

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

    async def system_reboot(self) -> bool:
        async with self.__request(
            "POST", "/rest/v1/system/reboot", json={"reboot": {"enable": True}}
        ) as resp:
            body = await resp.json()
            if "accepted" in body:
                # We are now no longer logged in after the reboot
                self.authorization = None
                return True
            return False

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

    async def system_provisioning(self) -> SystemProvisioningResponse:
        async with self.__request(
            "GET", "/rest/v1/system/gateway/provisioning"
        ) as resp:
            return SystemProvisioningResponse.build(await resp.json())


class SagemcomModemClient:
    base_url: str
    password: str
    timeout: int

    session: ContextVar[aiohttp.ClientSession] = ContextVar("session")
    client: ContextVar[SagemcomModemSessionClient] = ContextVar("client")

    def __init__(self, base_url: str, password: str, timeout: int = 15) -> None:
        self.base_url = base_url
        self.password = password
        self.timeout = timeout

    async def __aenter__(self) -> SagemcomModemSessionClient:
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        conn = aiohttp.TCPConnector(limit_per_host=30, force_close=True)

        self.session.set(aiohttp.ClientSession(timeout=timeout, connector=conn))
        self.client.set(
            SagemcomModemSessionClient(self.session.get(), self.base_url, self.password)
        )
        return self.client.get()

    async def __aexit__(self, *args) -> None:
        try:
            await self.client.get()._logout()
        except (
            aiohttp.ClientResponseError,
            aiohttp.client_exceptions.ClientConnectorError,
            asyncio.TimeoutError,
        ):
            LOG.debug("HTTP error during logout", exc_info=True)

        await self.session.get().close()
