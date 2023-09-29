import logging

from dataclasses import dataclass

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Literal, Optional

import aiohttp

LOG = logging.getLogger(__name__)

@dataclass
class AuthorisationResult:
    token: str
    user_level: str
    user_id: int

    @staticmethod
    def build(body: Dict[str, str]) -> 'AuthorisationResult':
        return AuthorisationResult(
            token=body['created']['token'],
            user_level=body['created']['userLevel'],
            user_id=body['created']['userId'],
        )
    
@dataclass
class ModemStateResult:
    boot_file_name: str
    docsis_version:  str
    mac_address:  str
    serial_number: str
    up_time: int
    access_allowed: bool
    status: str
    max_cpes: int
    baseline_privacy_enabled: bool

    @staticmethod
    def build(body: Dict[str, str]) -> 'ModemStateResult':
        return ModemStateResult(
            boot_file_name=body['cablemodem']['bootFilename'],
            docsis_version=body['cablemodem']['docsisVersion'],
            mac_address=body['cablemodem']['macAddress'],
            serial_number=body['cablemodem']['serialNumber'],
            up_time=body['cablemodem']['upTime'],
            access_allowed=body['cablemodem']['accessAllowed'],
            status=body['cablemodem']['status'],
            max_cpes=body['cablemodem']['maxCPEs'],
            baseline_privacy_enabled=body['cablemodem']['baselinePrivacyEnabled']
        )
    
@dataclass
class SystemInfoResult:
    model_name: str
    software_version: str
    hardware_version: str

    @staticmethod
    def build(body: Dict[str, str]) -> 'SystemInfoResult':
        return SystemInfoResult(
            model_name=body['info']['modelName'],
            software_version=body['info']['softwareVersion'],
            hardware_version=body['info']['hardwareVersion'],
        )


UNAUTHORIZED_ENDPOINTS = [
    'rest/v1/user/login',
]

for endpoint in set(UNAUTHORIZED_ENDPOINTS):
    assert not endpoint.startswith('/'), "URLs should be relative"


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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

    async def _login(self) -> Dict[str, str]:
        async with self.__request('POST', '/rest/v1/user/login', {'password': self.password}) as res:
            assert res.status == 201

            body = await res.json()
            self.authorization = AuthorisationResult.build(body)

    async def _logout(self) -> None:
        if self.authorization:
            LOG.info("Logging out session userId=%d", self.authorization.user_id)
            async with self.__request('DELETE', f'/rest/v1/user/{self.authorization.user_id}/token/{self.authorization.token}') as res:
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
        if not path in UNAUTHORIZED_ENDPOINTS:
            # log in because this endpoint requires authentication
            if not self.authorization:
                LOG.debug("logging in because '%s' requires authentication", path)
                await self._login()
            headers['Authorization'] = f"Bearer {self.authorization.token}"


        async with self.__session.request(
            method,
            url,
            headers=headers,
            json=json,
            raise_for_status=raise_for_status,
        ) as resp:
            yield resp


    async def system_info(self) -> SystemInfoResult:
        async with self.__request('GET', '/rest/v1/system/info') as resp:
            return SystemInfoResult.build(await resp.json())
    
    async def system_state(self) -> ModemStateResult:
        async with self.__request('GET', '/rest/v1/cablemodem/state_') as resp:
            return ModemStateResult.build(await resp.json())


    # async def ca_roas(self, ca: str) -> List[CaRoaGet]:
    #     async with self.__request(
    #         "GET", f"/api/ca/{ca}/roas", raise_for_status=True
    #     ) as resp:
    #         if resp.status == 404:
    #             # 404 if roa configuration entity does not exist
    #             return []

    #         return [CaRoaGet.build(r) for r in await resp.json()]


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
