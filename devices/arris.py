import logging
from datetime import datetime, timedelta

from hnap import HNAPDevice, HNAPCommand, GetMultipleCommands
from models import ConnectionSummary, ConnectionDetails, EventLogEntry, DownstreamChannelStats, UpstreamChannelStats, \
    DeviceInfo

logger = logging.getLogger(__name__)

level_priorities = {logging.INFO: "6",
                    logging.WARNING: "5",
                    logging.ERROR: "4",
                    logging.CRITICAL: "3"}


class SetStatusSecuritySettings(HNAPCommand):
    def __init__(self):
        super().__init__('SetArrisConfigurationInfo', read_only=False)


class Reboot(SetStatusSecuritySettings):
    def build_payload_data(self, **kwargs) -> dict:
        # {"SetArrisConfigurationInfo":{"Action":"reboot","SetEEEEnable":"0","LED_Status":"1"}}
        return {'Action': 'reboot',
                'SetEEEEnable': '0',
                'LED_Status': '2'}


class ArrisDevice(HNAPDevice):
    def get_commands(self) -> list:
        return [HNAPCommand('GetHomeAddress'),
                HNAPCommand('GetHomeConnection'),
                HNAPCommand('GetArrisConfigurationInfo'),
                HNAPCommand('GetArrisDeviceStatus'),
                HNAPCommand('GetArrisRegisterInfo'),
                HNAPCommand('GetArrisRegisterStatus'),
                HNAPCommand('GetCustomerStatusConnectionInfo'),
                HNAPCommand('GetCustomerStatusDownstreamChannelInfo'),
                HNAPCommand('GetCustomerStatusLog'),
                HNAPCommand('GetCustomerStatusLogXXX'),
                HNAPCommand('GetCustomerStatusSecAccount'),
                HNAPCommand('GetCustomerStatusSoftware'),
                HNAPCommand('GetCustomerStatusStartupSequence'),
                HNAPCommand('GetCustomerStatusUpstreamChannelInfo'),
                HNAPCommand('GetCustomerStatusXXX'),
                HNAPCommand('GetArrisXXX'),
                Reboot()]

    def get_device_info(self) -> DeviceInfo:
        sub_commands = [HNAPCommand('GetArrisDeviceStatus'),
                        HNAPCommand('GetArrisRegisterInfo')]
        response = self.do_command(GetMultipleCommands(sub_commands))

        summary = DeviceInfo()

        section = response['GetArrisRegisterInfoResponse']
        summary.model = self.model = section.get('ModelName')
        summary.serial_number = self.serial_number = section.get('SerialNumber')
        summary.mac_address = self.mac_address = section.get('MacAddress')

        section = response['GetArrisDeviceStatusResponse']
        summary.firmware_version = section.get('FirmwareVersion')
        summary.downstream_freq = section.get('DownstreamFrequency')
        summary.downstream_power = section.get('DownstreamSignalPower')
        summary.downstream_snr = section.get('DownstreamSignalSnr')

        return summary

    def get_connection_summary(self) -> ConnectionSummary:
        sub_commands = [HNAPCommand('GetHomeAddress'),
                        HNAPCommand('GetHomeConnection'),
                        HNAPCommand('GetCustomerStatusSoftware')]
        response = self.do_command(GetMultipleCommands(sub_commands))

        summary = ConnectionSummary()

        section = response['GetHomeAddressResponse']
        summary.ip_address = section.get('MotoHomeIpAddress')
        summary.mac_address = section.get('MotoHomeMacAddress')

        section = response['GetCustomerStatusSoftwareResponse']
        summary.hw_version = section.get('StatusSoftwareHdVer')
        summary.sw_cert_status = section.get('StatusSoftwareCertificate')
        summary.sw_customer_version = section.get('StatusSoftwareCustomerVer')
        summary.sw_serial = section.get('StatusSoftwareSerialNum')
        summary.sw_spec_version = section.get('StatusSoftwareSpecVer')
        summary.sw_version = section.get('StatusSoftwareSfVer')

        section = response['GetHomeConnectionResponse']
        summary.downstream_channel_count = int(section.get('MotoHomeDownNum', 0))
        summary.upstream_channel_count = int(section.get('MotoHomeUpNum', 0))

        return summary

    def get_connection_details(self) -> ConnectionDetails:
        sub_commands = [HNAPCommand('GetCustomerStatusStartupSequence'),
                        HNAPCommand('GetCustomerStatusConnectionInfo'),
                        HNAPCommand('GetCustomerStatusDownstreamChannelInfo'),
                        HNAPCommand('GetCustomerStatusUpstreamChannelInfo')]
        response = self.do_command(GetMultipleCommands(sub_commands))

        details = ConnectionDetails()

        section = response['GetCustomerStatusConnectionInfoResponse']
        details.network_access = section.get('CustomerConnNetworkAccess')
        details.uptime = section.get('CustomerConnSystemUpTime')

        section = response['GetCustomerStatusStartupSequenceResponse']
        details.startup_steps['downstream'].status = section.get('CustomerConnDSFreq')
        details.startup_steps['downstream'].comment = section.get('CustomerConnDSComment')
        details.startup_steps['upstream'].status = section.get('CustomerConnConnectivityStatus')
        details.startup_steps['upstream'].comment = section.get('CustomerConnConnectivityComment')
        details.startup_steps['boot'].status = section.get('CustomerConnBootStatus')
        details.startup_steps['boot'].comment = section.get('CustomerConnBootComment')
        details.startup_steps['config_file'].status = section.get('CustomerConnConfigurationFileStatus')
        details.startup_steps['config_file'].comment = section.get('CustomerConnConfigurationFileComment')
        details.startup_steps['security'].status = section.get('CustomerConnSecurityStatus')
        details.startup_steps['security'].comment = section.get('CustomerConnSecurityComment')

        # 1^Locked^QAM256^32^495.0^-7.8^39.9^0^0^|+|2^Locked^QAM256...
        raw = response['GetCustomerStatusDownstreamChannelInfoResponse'].get('CustomerConnDownstreamChannel').split("|+|")
        details.downstream_channels = []
        for c, channel_stats in enumerate(raw):
            channel_stats_list = channel_stats.split("^")

            dcs = DownstreamChannelStats()
            dcs.lock_status = channel_stats_list[1].strip()
            dcs.modulation = channel_stats_list[2].strip()
            dcs.channel_id = int(channel_stats_list[3].strip())
            dcs.freq_mhz = float(channel_stats_list[4].strip())
            dcs.power_dbmv = float(channel_stats_list[5].strip())
            dcs.snr = float(channel_stats_list[6].strip())
            dcs.corrected = int(channel_stats_list[7].strip())
            dcs.uncorrected = int(channel_stats_list[8].strip())
            details.downstream_channels.append(dcs)
        logger.debug('Found {} downstream channels for {}'.format(len(details.downstream_channels), self))

        # 1^Locked^SC-QAM^1^5120^35.5^50.0^|+|2^Locked^SC-QAM^2^5...
        raw = response['GetCustomerStatusUpstreamChannelInfoResponse'].get('CustomerConnUpstreamChannel').split("|+|")
        details.upstream_channels = []
        for c, channel_stats in enumerate(raw):
            channel_stats_list = channel_stats.split("^")

            ucs = UpstreamChannelStats()
            ucs.lock_status = channel_stats_list[1].strip()
            ucs.channel_type = channel_stats_list[2].strip()
            ucs.channel_id = int(channel_stats_list[3].strip())
            ucs.symb_rate = float(channel_stats_list[4].strip())
            ucs.freq_mhz = float(channel_stats_list[5].strip())
            ucs.power_dbmv = float(channel_stats_list[6].strip())
            details.upstream_channels.append(ucs)
        logger.debug('Found {} upstream channels for {}'.format(len(details.upstream_channels), self))

        return details

    def get_events(self) -> list:
        response = self.do_command(HNAPCommand('GetCustomerStatusLog'))

        events = []

        # 0^00:01:11^1/1/1970^3^SYNC Timing Synchronization failure - Failed...}-{0^00:00:...
        prev_ts = datetime.min
        raw_events = response.get('CustomerStatusLogList').split("}-{")
        for e, raw_event in enumerate(raw_events):
            raw_event_list = raw_event.split("^")

            date = raw_event_list[2].strip()
            time = raw_event_list[1].strip()
            try:
                ts = self.to_timestamp(date, time)
            except ValueError:
                ts = prev_ts + timedelta(seconds=1)
            prev_ts = ts

            event = EventLogEntry(timestamp=ts, priority=raw_event_list[3].strip(), desc=raw_event_list[4].strip())
            events.append(event)

        logger.debug('Found {} events for {}'.format(len(events), self))
        return events

    def reboot(self):
        logger.warning('Rebooting {}'.format(self))
        self.do_command(Reboot())
        self.invalidate_session()

    def to_timestamp(self, date: str, time: str):
        return datetime.strptime('{} {}'.format(date, time), '%d/%m/%Y %H:%M:%S')

    def to_event_priority(self, level: int):
        return level_priorities.get(level, 'UNKNOWN {}'.format(level))
