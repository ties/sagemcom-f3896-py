from dataclasses import dataclass
import datetime
from typing import Dict, List, Literal


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
class EventLogItem:
    priority: Literal['error', 'notice', 'critical', 'warning']
    time: datetime.datetime
    message: str

    @staticmethod
    def build(elem: Dict[str, str]) -> List['EventLogItem']:
        return EventLogItem(
            priority=elem['priority'],
            time=datetime.datetime.fromisoformat(elem['time']),
            message=elem['message'],
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
