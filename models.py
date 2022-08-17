from collections import OrderedDict


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
        self.downstream_channels = []  # GetMotoStatusDownstreamChannelInfo
        self.upstream_channels = []  # GetMotoStatusUpstreamChannelInfo


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
    def __init__(self):
        self.date = None
        self.time = None
        self.priority = None
        self.desc = None
