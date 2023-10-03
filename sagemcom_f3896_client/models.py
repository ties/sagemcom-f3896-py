import datetime
import logging
from dataclasses import dataclass
from typing import Dict, List, Literal

LOG = logging.getLogger(__name__)


@dataclass
class UserAuthorisationResult:
    token: str
    user_level: str
    user_id: int

    @staticmethod
    def build(body: Dict[str, str]) -> "UserAuthorisationResult":
        return UserAuthorisationResult(
            token=body["created"]["token"],
            user_level=body["created"]["userLevel"],
            user_id=body["created"]["userId"],
        )

@dataclass
class UserTokenResult:
    token: str
    user_level: str

    @staticmethod
    def build(body: Dict[str, str]) -> "UserTokenResult":
        return UserTokenResult(
            token=body["created"]["token"],
            user_level=body["created"]["userLevel"],
        )


@dataclass
class EventLogItem:
    priority: Literal["error", "notice", "critical", "warning"]
    time: datetime.datetime
    message: str

    @staticmethod
    def build(elem: Dict[str, str]) -> List["EventLogItem"]:
        return EventLogItem(
            priority=elem["priority"],
            time=datetime.datetime.fromisoformat(elem["time"]),
            message=elem["message"],
        )


@dataclass
class ModemStateResult:
    boot_file_name: str
    docsis_version: str
    mac_address: str
    serial_number: str
    up_time: int
    access_allowed: bool
    status: str
    max_cpes: int
    baseline_privacy_enabled: bool

    @staticmethod
    def build(body: Dict[str, str]) -> "ModemStateResult":
        return ModemStateResult(
            boot_file_name=body["cablemodem"]["bootFilename"],
            docsis_version=body["cablemodem"]["docsisVersion"],
            mac_address=body["cablemodem"]["macAddress"],
            serial_number=body["cablemodem"]["serialNumber"],
            up_time=body["cablemodem"]["upTime"],
            access_allowed=body["cablemodem"]["accessAllowed"],
            status=body["cablemodem"]["status"],
            max_cpes=body["cablemodem"]["maxCPEs"],
            baseline_privacy_enabled=body["cablemodem"]["baselinePrivacyEnabled"],
        )


@dataclass(kw_only=True)
class ModemDownstreamChannelResult:
    channel_type: Literal["ofdm", "sc_qam"] = "ofdm"
    channel_id: int
    """In MHz. Frequency of the first active carrier for OFDM"""
    frequency: float
    rx_mer: int
    power: float
    lock_status: Literal["locked", "unlocked"]
    corrected_errors: int
    uncorrected_errors: int


@dataclass(kw_only=True)
class ModemQAMDownstreamChannelResult(ModemDownstreamChannelResult):
    # in DB (int)
    snr: int
    modulation: str

    @staticmethod
    def build(elem: Dict[str, str]) -> "ModemQAMDownstreamChannelResult":
        return ModemQAMDownstreamChannelResult(
            channel_type=elem["channelType"],
            channel_id=elem["channelId"],
            frequency=elem["frequency"],
            power=elem["power"] / 1.0,
            modulation=elem["modulation"],
            snr=elem["snr"],
            rx_mer=elem["rxMer"],
            corrected_errors=elem["correctedErrors"],
            uncorrected_errors=elem["uncorrectedErrors"],
            lock_status=elem["lockStatus"],
        )


@dataclass(kw_only=True)
class ModemOFDMDownstreamChannelResult(ModemDownstreamChannelResult):
    """In hz"""
    channel_width: float
    fft_type: Literal["2K", "4K", "8K", "16K"]
    number_of_active_subcarriers: int
    modulation: Literal["qam_256", "qam_512", "qam_1024", "qam_2048", "qam_4096"]

    @staticmethod
    def build(elem: Dict[str, str]) -> "ModemOFDMDownstreamChannelResult":
        return ModemOFDMDownstreamChannelResult(
            channel_type=elem["channelType"],
            channel_id=elem["channelId"],
            channel_width=elem["channelWidth"],
            fft_type=elem["fftType"],
            # note: inconsistent caps in JSON
            number_of_active_subcarriers=elem["numberOfActiveSubCarriers"],
            modulation=elem["modulation"],
            frequency=elem["firstActiveSubcarrier"] * 1_000_000,
            lock_status=elem["lockStatus"],
            rx_mer=elem["rxMer"] / 10.0,
            power=elem["power"] / 10.0,
            corrected_errors=elem["correctedErrors"],
            uncorrected_errors=elem["uncorrectedErrors"],
        )


@dataclass(kw_only=True)
class ModemUpstreamChannelResult:
    channel_type: Literal["atdma", "ofdma"]
    channel_id: int
    """In hz. Frequency of the first active carrier for OFDMA"""
    frequency: float

    lock_status: bool
    power: float
    modulation: Literal["qam_64", "qam_256"]

    t3_timeouts: int
    t4_timeouts: int


@dataclass(kw_only=True)
class ModemATDMAUpstreamChannelResult(ModemUpstreamChannelResult):
    symbol_rate: int
    t1_timeouts: int
    t2_timeouts: int

    @staticmethod
    def build(elem: Dict[str, str]) -> "ModemATDMAUpstreamChannelResult":
        return ModemATDMAUpstreamChannelResult(
            channel_type=elem["channelType"],
            channel_id=elem["channelId"],
            lock_status=elem["lockStatus"],
            power=elem["power"],
            modulation=elem["modulation"],

            frequency=elem["frequency"],
            symbol_rate=elem["symbolRate"],
            t1_timeouts=elem["t1Timeout"],
            t2_timeouts=elem["t2Timeout"],

            t3_timeouts=elem["t3Timeout"],
            t4_timeouts=elem["t4Timeout"],
        )


@dataclass(kw_only=True)
class ModemOFDMAUpstreamChannelResult(ModemUpstreamChannelResult):
    channel_width: float
    fft_type: Literal["2K", "4K"]
    number_of_active_subcarriers: int

    @staticmethod
    def build(elem: Dict[str, str]) -> "ModemOFDMAUpstreamChannelResult":
        return ModemOFDMAUpstreamChannelResult(
            channel_type=elem["channelType"],
            channel_id=elem["channelId"],
            frequency=elem["firstActiveSubcarrier"] * 1_000_000,

            lock_status=elem["lockStatus"],
            power=elem["power"] / 10,
            modulation=elem["modulation"],
            channel_width=elem["channelWidth"],
            fft_type=elem["fftType"],
            # inconsistent capitals in the JSON
            number_of_active_subcarriers=elem["numberOfActiveSubCarriers"],
            t3_timeouts=elem["t3Timeout"],
            t4_timeouts=elem["t4Timeout"],
        )


@dataclass
class ModemServiceFlowResult:
    # https://www.rfc-editor.org/rfc/rfc4323
    id: int
    direction: Literal["upstream", "downstream"]
    max_traffic_rate: int
    max_traffic_burst: int
    min_reserved_rate: int
    max_concatenated_burst: int
    # => DocsIetfQosSchedulingType
    schedule_type: Literal[
        "undefined",
        "bestEffort",
        "nonRealTimePollingService",
        "realTimePollingService",
        "unsolicitedGrantService",
        "unsolicitedGrantServiceWithActivityDetection",
    ]

    @staticmethod
    def build(elem: Dict[str, str]) -> "ModemServiceFlowResult":
        return ModemServiceFlowResult(
            id=elem["serviceFlow"]["serviceFlowId"],
            direction=elem["serviceFlow"]["direction"],
            max_traffic_rate=elem["serviceFlow"]["maxTrafficRate"],
            max_traffic_burst=elem["serviceFlow"]["maxTrafficBurst"],
            min_reserved_rate=elem["serviceFlow"]["minReservedRate"],
            max_concatenated_burst=elem["serviceFlow"]["maxConcatenatedBurst"],
            schedule_type=elem["serviceFlow"]["scheduleType"],
        )


@dataclass
class SystemInfoResult:
    model_name: str
    software_version: str
    hardware_version: str

    @staticmethod
    def build(body: Dict[str, str]) -> "SystemInfoResult":
        return SystemInfoResult(
            model_name=body["info"]["modelName"],
            software_version=body["info"]["softwareVersion"],
            hardware_version=body["info"]["hardwareVersion"],
        )

@dataclass
class SystemProvisioningResponse:
    provisioning_mode: Literal['enable', 'disable']
    mac_address: str
    ds_lite_enabled: bool

    @staticmethod
    def build(body: Dict[str, str]) -> "SystemProvisioningResponse":
        return SystemProvisioningResponse(
            provisioning_mode=body["provisioning"]["mode"],
            mac_address=body["provisioning"]["macAddress"],
            ds_lite_enabled=body["provisioning"]["dsLite"]["enable"],
        )