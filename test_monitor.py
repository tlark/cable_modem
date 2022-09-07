from unittest import TestCase

from hnap import HNAPDevice
from monitor import JobRunSummary, is_reboot_recommended

device = HNAPDevice('test')


class TestMonitor(TestCase):
    def test_is_reboot_recommended(self):
        history = [JobRunSummary('reboot', succeeded=True),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('ping', succeeded=False),
                   ]
        self.assertFalse(is_reboot_recommended(device, history))

        history = [JobRunSummary('reboot', succeeded=True),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=False),
                   ]
        self.assertFalse(is_reboot_recommended(device, history))

        history = [JobRunSummary('reboot', succeeded=True),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=False),
                   ]
        self.assertFalse(is_reboot_recommended(device, history))

        history = [JobRunSummary('reboot', succeeded=True),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=True),
                   ]
        self.assertFalse(is_reboot_recommended(device, history))

        history = [JobRunSummary('reboot', succeeded=True),
                   JobRunSummary('get_stats', succeeded=False),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=True),
                   ]
        self.assertFalse(is_reboot_recommended(device, history))

        history = [JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('reboot', succeeded=True),
                   JobRunSummary('get_stats', succeeded=False),
                   JobRunSummary('ping', succeeded=True),
                   JobRunSummary('ping', succeeded=True),
                   JobRunSummary('ping', succeeded=True),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('ping', succeeded=True)
                   ]
        self.assertFalse(is_reboot_recommended(device, history))

        history = [JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('get_stats', succeeded=False),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('ping', succeeded=False)
                   ]
        self.assertFalse(is_reboot_recommended(device, history))

        history = [JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('get_stats', succeeded=False),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=False),
                   ]
        self.assertFalse(is_reboot_recommended(device, history))

        history = [JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('get_stats', succeeded=False),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=True),
                   JobRunSummary('get_stats', succeeded=False),
                   ]
        self.assertFalse(is_reboot_recommended(device, history))

        history = [JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('get_stats', succeeded=False),
                   JobRunSummary('get_stats', succeeded=True),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=False),
                   JobRunSummary('ping', succeeded=True),
                   ]
        self.assertTrue(is_reboot_recommended(device, history))
