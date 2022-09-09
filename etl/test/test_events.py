import json
from datetime import datetime
from pathlib import Path
from unittest import TestCase

from devices.motorola import MotorolaDevice
from etl.events import combine_events

device = MotorolaDevice('test')


class TestEvents(TestCase):
    def test_combine_events_when_old_format(self):
        json_filepath = Path('data', 'events', '20220817_182857.json')
        with json_filepath.open() as file:
            cur_events = json.load(file)
            if not isinstance(cur_events, list):
                cur_events = cur_events['result']

        act = combine_events(cur_events, device)
        self.assertEqual(32, len(act))

    def test_combine_events_when_new_format(self):
        json_filepath = Path('data', 'events', '20220909_094503.json')
        with json_filepath.open() as file:
            cur_events = json.load(file)
            if not isinstance(cur_events, list):
                cur_events = cur_events['result']

        act = combine_events(cur_events, device)
        self.assertEqual(32, len(act))

    def test_combine_events_when_no_ts(self):
        cur_events = list()
        cur_events.append({"timestamp": "0001-01-01T00:00:01", "priority": "Critical (3)", "desc": "d1"})
        cur_events.append({"timestamp": "0001-01-01T00:00:01", "priority": "Critical (3)", "desc": "d2"})
        cur_events.append({"timestamp": "0001-01-01T00:00:01", "priority": "Critical (3)", "desc": "d3"})

        act = combine_events(cur_events, device)
        self.assertEqual(3, len(act))
        self.assertEqual('d1', cur_events[0].get('desc', None))
        self.assertEqual('d2', cur_events[1].get('desc', None))
        self.assertEqual('d3', cur_events[2].get('desc', None))

    def test_combine_events_when_no_ts_middle(self):
        cur_events = list()
        cur_events.append({"timestamp": "2022-09-01T11:22:33", "priority": "Warning (2)", "desc": "w1"})
        cur_events.append({"timestamp": "0001-01-01T00:00:01", "priority": "Critical (3)", "desc": "d1"})
        cur_events.append({"timestamp": "0001-01-01T00:00:01", "priority": "Critical (3)", "desc": "d2"})
        cur_events.append({"timestamp": "2022-09-01T12:00:00", "priority": "Warning (2)", "desc": "w2"})

        act = combine_events(cur_events, device)
        self.assertEqual(4, len(act))
        self.assertEqual('w1', act[0].get('desc', None))
        self.assertEqual('d1', act[1].get('desc', None))
        self.assertEqual('d2', act[2].get('desc', None))
        self.assertEqual('w2', act[3].get('desc', None))

        # Verify synthetic timestamps are between the real timestamps
        real_1 = datetime.fromisoformat(act[0].get('timestamp', None))
        real_2 = datetime.fromisoformat(act[3].get('timestamp', None))
        synth_1 = datetime.fromisoformat(act[1].get('timestamp', None))
        synth_2 = datetime.fromisoformat(act[2].get('timestamp', None))
        self.assertTrue(real_1 <= synth_1 <= real_2)
        self.assertTrue(real_1 <= synth_2 <= real_2)
