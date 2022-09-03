from collections import OrderedDict
from datetime import datetime


class DeviceInfo:
    def __init__(self):
        self.model = None
        self.serial_number = None
        self.mac_address = None
        self.firmware_version = None
        self.downstream_freq = None
        self.downstream_power = None
        self.downstream_snr = None


class ConnectionSummary:
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


class ConnectionDetails:
    def __init__(self):
        self.startup_steps = OrderedDict({'downstream': StartupStep(),
                                          'upstream': StartupStep(),
                                          'boot': StartupStep(),
                                          'config_file': StartupStep(),
                                          'security': StartupStep()})
        self.uptime = None
        self.network_access = None
        self.downstream_channels = []
        self.upstream_channels = []


class StartupStep:
    def __init__(self):
        self.status = None
        self.comment = None


class ChannelStats:
    def __init__(self):
        self.channel_id = 0
        self.lock_status = None
        self.freq_mhz = 0.0
        self.power_dbmv = 0.0


class DownstreamChannelStats(ChannelStats):
    def __init__(self):
        super().__init__()
        self.modulation = None
        self.snr = 0.0
        self.corrected = 0
        self.uncorrected = 0


class UpstreamChannelStats(ChannelStats):
    def __init__(self):
        super().__init__()
        self.channel_type = None
        self.symb_rate = 0


class EventLogEntry:
    def __init__(self, timestamp: datetime, priority, desc):
        self.timestamp = timestamp.isoformat()
        self.priority = priority
        self.desc = desc

    def __eq__(self, other):
        return self.timestamp == other.timestamp

    def __hash__(self):
        return hash((self.timestamp, self.priority, self.desc))
