from datetime import datetime


class DeviceInfo(object):
    def __init__(self):
        self.model = None
        self.serial_number = None
        self.mac_address = None
        self.firmware_version = None
        self.downstream_freq = None
        self.downstream_power = None
        self.downstream_snr = None

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.__dict__)


class ConnectionSummary(object):
    def __init__(self):
        self.ip_address = None
        self.mac_address = None
        self.downstream_channel_count = 0
        self.upstream_channel_count = 0
        self.hw_version = None
        self.sw_version = None
        self.sw_spec_version = None
        self.sw_serial = None
        self.sw_cert_status = None
        self.sw_customer_version = None

    def __eq__(self, other):
        return vars(self) == vars(other) if not isinstance(other, dict) else other

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.__dict__)


class ConnectionDetails(object):
    def __init__(self, startup_steps=None, uptime=None, network_access=None, downstream_channels=None,
                 upstream_channels=None):
        if startup_steps:
            self.startup_steps = {k: StartupStep(**v) for (k, v) in startup_steps.items()}
        else:
            self.startup_steps = dict(
                {'downstream': StartupStep(),
                 'upstream': StartupStep(),
                 'boot': StartupStep(),
                 'config_file': StartupStep(),
                 'security': StartupStep()})
        self.uptime = uptime
        self.network_access = network_access
        if downstream_channels:
            self.downstream_channels = [DownstreamChannelStats(**c) for c in downstream_channels]
        else:
            self.downstream_channels = list()
        if upstream_channels:
            self.upstream_channels = [UpstreamChannelStats(**c) for c in upstream_channels]
        else:
            self.upstream_channels = list()

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.__dict__)


class StartupStep(object):
    def __init__(self, status=None, comment=None):
        self.status = status
        self.comment = comment

    def __eq__(self, other):
        return vars(self) == vars(other) if not isinstance(other, dict) else other

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.__dict__)


class ChannelStats(object):
    def __init__(self, channel_id=0, lock_status=None, freq_mhz=0.0, power_dbmv=0.0):
        self.channel_id = channel_id
        self.lock_status = lock_status
        self.freq_mhz = freq_mhz
        self.power_dbmv = power_dbmv

    def __eq__(self, other):
        return vars(self) == vars(other) if not isinstance(other, dict) else other

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.__dict__)


class DownstreamChannelStats(ChannelStats):
    def __init__(self, channel_id=0, lock_status=None, freq_mhz=0.0, power_dbmv=0.0, modulation=None, snr=0.0,
                 corrected=0, uncorrected=0):
        super().__init__(channel_id, lock_status, freq_mhz, power_dbmv)
        self.modulation = modulation
        self.snr = snr
        self.corrected = corrected
        self.uncorrected = uncorrected


class UpstreamChannelStats(ChannelStats):
    def __init__(self, channel_id=0, lock_status=None, freq_mhz=0.0, power_dbmv=0.0, channel_type=None, symb_rate=0):
        super().__init__(channel_id, lock_status, freq_mhz, power_dbmv)
        self.channel_type = channel_type
        self.symb_rate = symb_rate


class EventLogEntry(object):
    def __init__(self, timestamp: datetime, priority, desc):
        self.timestamp = timestamp.isoformat()
        self.priority = priority
        self.desc = desc

    def __eq__(self, other):
        return self.timestamp == other.timestamp

    def __hash__(self):
        return hash((self.timestamp, self.priority, self.desc))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.__dict__)
