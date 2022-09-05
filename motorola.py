import logging
from datetime import datetime, timedelta

from hnap import HNAPDevice, HNAPCommand, GetMultipleCommands
from models import ConnectionSummary, ConnectionDetails, EventLogEntry, DownstreamChannelStats, UpstreamChannelStats

logger = logging.getLogger(__name__)


class SetStatusSecuritySettings(HNAPCommand):
    def __init__(self):
        super().__init__('SetStatusSecuritySettings', read_only=False)


class Reboot(SetStatusSecuritySettings):
    def build_payload_data(self, **kwargs) -> dict:
        return {'MotoStatusSecurityAction': '1',
                'MotoStatusSecXXX': 'XXX'}


class MotorolaDevice(HNAPDevice):
    def get_commands(self) -> list:
        return [HNAPCommand('GetHomeAddress'),
                HNAPCommand('GetHomeConnection'),
                HNAPCommand('GetMotoStatusSoftware'),
                HNAPCommand('GetMotoStatusStartupSequence'),
                HNAPCommand('GetMotoStatusConnectionInfo'),
                HNAPCommand('GetMotoStatusDownstreamChannelInfo'),
                HNAPCommand('GetMotoStatusUpstreamChannelInfo'),
                HNAPCommand('GetMotoLagStatus'),
                HNAPCommand('GetMotoStatusLog'),
                HNAPCommand('GetMotoStatusSecAccount'),
                Reboot()]

    def get_connection_summary(self) -> ConnectionSummary:
        sub_commands = [HNAPCommand('GetHomeAddress'),
                        HNAPCommand('GetHomeConnection'),
                        HNAPCommand('GetMotoStatusSoftware')]
        response = self.do_command(GetMultipleCommands(sub_commands))

        summary = ConnectionSummary()

        section = response['GetHomeAddressResponse']
        summary.ip_address = section.get('MotoHomeIpAddress')
        summary.mac_address = section.get('MotoHomeMacAddress')

        section = response['GetMotoStatusSoftwareResponse']
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
        sub_commands = [HNAPCommand('GetMotoStatusStartupSequence'),
                        HNAPCommand('GetMotoStatusConnectionInfo'),
                        HNAPCommand('GetMotoStatusDownstreamChannelInfo'),
                        HNAPCommand('GetMotoStatusUpstreamChannelInfo')]
        response = self.do_command(GetMultipleCommands(sub_commands))

        details = ConnectionDetails()

        section = response['GetMotoStatusConnectionInfoResponse']
        details.network_access = section.get('MotoConnNetworkAccess')
        details.uptime = section.get('MotoConnSystemUpTime')

        section = response['GetMotoStatusStartupSequenceResponse']
        details.startup_steps['downstream'].status = section.get('MotoConnDSFreq')
        details.startup_steps['downstream'].comment = section.get('MotoConnDSComment')
        details.startup_steps['upstream'].status = section.get('MotoConnConnectivityStatus')
        details.startup_steps['upstream'].comment = section.get('MotoConnConnectivityComment')
        details.startup_steps['boot'].status = section.get('MotoConnBootStatus')
        details.startup_steps['boot'].comment = section.get('MotoConnBootComment')
        details.startup_steps['config_file'].status = section.get('MotoConnConfigurationFileStatus')
        details.startup_steps['config_file'].comment = section.get('MotoConnConfigurationFileComment')
        details.startup_steps['security'].status = section.get('MotoConnSecurityStatus')
        details.startup_steps['security'].comment = section.get('MotoConnSecurityComment')

        # 1^Locked^QAM256^32^495.0^-7.8^39.9^0^0^|+|2^Locked^QAM256...
        raw = response['GetMotoStatusDownstreamChannelInfoResponse'].get('MotoConnDownstreamChannel').split("|+|")
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
        raw = response['GetMotoStatusUpstreamChannelInfoResponse'].get('MotoConnUpstreamChannel').split("|+|")
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
        response = self.do_command(HNAPCommand('GetMotoStatusLog'))

        events = []

        # '12:14:11^Tue Aug 16 2022\n^Critical (3)^Started Unicast Maintenance Ranging...}-{12:18:05^Tue Aug 16 2022
        prev_ts = datetime.min
        raw_events = response.get('MotoStatusLogList').split("}-{")
        for e, raw_event in enumerate(raw_events):
            raw_event_list = raw_event.split("^")

            date = raw_event_list[1].strip()
            time = raw_event_list[0].strip()
            try:
                ts = self.to_timestamp(date, time)
            except ValueError:
                ts = prev_ts + timedelta(seconds=1)
            prev_ts = ts

            event = EventLogEntry(timestamp=ts, priority=raw_event_list[2].strip(), desc=raw_event_list[3].strip())
            events.append(event)

        logger.debug('Found {} events for {}'.format(len(events), self))
        return events

    def reboot(self):
        logger.warning('Rebooting {}'.format(self))
        self.do_command(Reboot())
        self.invalidate_session()

    def to_timestamp(self, date: str, time: str):
        return datetime.strptime('{} {}'.format(date, time), '%a %b %d %Y %H:%M:%S')
