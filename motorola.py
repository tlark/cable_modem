from hnap import HNAPSystem, HNAPCommand, HNAPSession, GetMultipleCommands
from models import ConnectionSummary, ConnectionDetails, EventLogEntry, DownstreamChannelStats, UpstreamChannelStats


class SetStatusSecuritySettings(HNAPCommand):
    def __init__(self):
        super().__init__('SetStatusSecuritySettings', read_only=False)


class Reboot(SetStatusSecuritySettings):
    def build_payload_data(self, **kwargs) -> dict:
        return {'MotoStatusSecurityAction': '1',
                'MotoStatusSecXXX': 'XXX'}


class MotorolaSystem(HNAPSystem):
    def get_commands(self, session: HNAPSession) -> list:
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

    def get_connection_summary(self, session: HNAPSession) -> ConnectionSummary:
        sub_commands = [HNAPCommand('GetHomeAddress'),
                        HNAPCommand('GetHomeConnection'),
                        HNAPCommand('GetMotoStatusSoftware')]
        response = self.do_command(session, GetMultipleCommands(sub_commands))

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

    def get_connection_details(self, session: HNAPSession) -> ConnectionDetails:
        sub_commands = [HNAPCommand('GetMotoStatusStartupSequence'),
                        HNAPCommand('GetMotoStatusConnectionInfo'),
                        HNAPCommand('GetMotoStatusDownstreamChannelInfo'),
                        HNAPCommand('GetMotoStatusUpstreamChannelInfo')]
        response = self.do_command(session, GetMultipleCommands(sub_commands))

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

        return details

    def get_events(self, session: HNAPSession) -> list:
        response = self.do_command(session, HNAPCommand('GetMotoStatusLog'))

        events = []

        # '12:14:11^Tue Aug 16 2022\n^Critical (3)^Started Unicast Maintenance Ranging...}-{12:18:05^Tue Aug 16 2022
        raw_events = response.get('MotoStatusLogList').split("}-{")
        for e, raw_event in enumerate(raw_events):
            raw_event_list = raw_event.split("^")
            event = EventLogEntry()
            event.date = raw_event_list[1].strip()
            event.time = raw_event_list[0].strip()
            event.priority = raw_event_list[2].strip()
            event.desc = raw_event_list[3].strip()
            events.append(event)

        return events

    def reboot(self, session: HNAPSession):
        self.do_command(session, Reboot())
