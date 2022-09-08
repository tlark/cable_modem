from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase

from etl.details import extract_connection_stats, is_channel_stats_changed, transform_details
from hnap import HNAPDevice
from models import ConnectionDetails, StartupStep

device = HNAPDevice('test')


class TestDetails(TestCase):
    def test_extract_connection_details_when_no_timestamp(self):
        json_filepath = Path('data', 'details', '20220830_185833.json')
        act = extract_connection_stats(json_filepath)
        self.assertEqual(datetime(2022, 8, 30, 18, 58, 33).isoformat(), act.timestamp)
        self.assertEqual(5, len(act.details.startup_steps))
        self.assertEqual(4, len(act.details.upstream_channels))
        self.assertEqual(32, len(act.details.downstream_channels))
        self.assertEqual('Allowed', act.details.network_access)

    def test_extract_connection_details_when_timestamp(self):
        json_filepath = Path('data', 'details', '20220907_120800.json')
        act = extract_connection_stats(json_filepath)
        # 2022-09-07T12:08:05.751985
        self.assertEqual(datetime(2022, 9, 7, 12, 8, 5, 751985).isoformat(), act.timestamp)
        self.assertEqual(5, len(act.details.startup_steps))
        self.assertEqual(4, len(act.details.upstream_channels))
        self.assertEqual(32, len(act.details.downstream_channels))
        self.assertEqual('Allowed', act.details.network_access)

    def test_model_init(self):
        cd = ConnectionDetails()
        self.assertEqual(5, len(cd.startup_steps))
        self.assertEqual(0, len(cd.downstream_channels))
        self.assertEqual(0, len(cd.upstream_channels))

    def test_model_equality(self):
        json_filepath = Path('data', 'details', '20220907_120800.json')
        act = extract_connection_stats(json_filepath)
        ch1 = act.details.downstream_channels[0]
        ch2 = act.details.downstream_channels[1]
        self.assertNotEqual(ch1, ch2)

        # Assign ALL ch1 values to ch2 (should now be equal)
        ch2.channel_id = ch1.channel_id
        ch2.lock_status = ch1.lock_status
        ch2.freq_mhz = ch1.freq_mhz
        ch2.power_dbmv = ch1.power_dbmv
        ch2.modulation = ch1.modulation
        ch2.snr = ch1.snr
        ch2.corrected = ch1.corrected
        ch2.uncorrected = ch1.uncorrected
        self.assertEqual(ch1, ch2)

    def test_is_channel_stats_change_when_no_history(self):
        json_filepath = Path('data', 'details', '20220907_120800.json')
        cur_ts_stats = extract_connection_stats(json_filepath)

        for cur_stats in cur_ts_stats.details.downstream_channels:
            history = list()
            self.assertTrue(is_channel_stats_changed(history, vars(cur_stats).copy(), cur_ts_stats.timestamp))
            self.assertEqual(1, len(history))

    def test_is_channel_stats_change_when_no_change(self):
        json_filepath = Path('data', 'details', '20220907_120800.json')
        cur_ts_stats = extract_connection_stats(json_filepath)

        for cur_stats in cur_ts_stats.details.downstream_channels:
            history = list()
            prev_ts_stats = vars(cur_stats).copy()
            prev_ts_stats['timestamp'] = datetime.fromisoformat(cur_ts_stats.timestamp) - timedelta(minutes=10)
            history.append(prev_ts_stats)
            self.assertFalse(is_channel_stats_changed(history, vars(cur_stats).copy(), cur_ts_stats.timestamp))
            self.assertEqual(1, len(history))

    def test_is_channel_stats_change_when_change(self):
        json_filepath = Path('data', 'details', '20220907_120800.json')
        cur_ts_stats = extract_connection_stats(json_filepath)

        for cur_stats in cur_ts_stats.details.downstream_channels:
            history = list()
            prev_ts_stats = vars(cur_stats).copy()
            prev_ts_stats['corrected'] = cur_stats.corrected + 10
            prev_ts_stats['timestamp'] = datetime.fromisoformat(cur_ts_stats.timestamp) - timedelta(minutes=10)
            history.append(prev_ts_stats)
            self.assertTrue(is_channel_stats_changed(history, vars(cur_stats).copy(), cur_ts_stats.timestamp))
            self.assertEqual(2, len(history))

    def test_transform_details_when_no_history(self):
        json_filepath = Path('data', 'details', '20220907_120800.json')
        cur_ts_stats = extract_connection_stats(json_filepath)

        history = list()
        self.assertTrue(transform_details(history, cur_ts_stats))
        self.assertEqual(1, len(history))

    def test_transform_details_when_no_change(self):
        json_filepath = Path('data', 'details', '20220907_120800.json')
        cur_ts_stats = extract_connection_stats(json_filepath)

        history = list()
        prev_ts_details = vars(cur_ts_stats.details).copy()
        prev_ts_details['timestamp'] = datetime.fromisoformat(cur_ts_stats.timestamp) - timedelta(minutes=10)
        history.append(prev_ts_details)

        self.assertFalse(transform_details(history, cur_ts_stats))
        self.assertEqual(1, len(history))

    def test_transform_details_when_change(self):
        json_filepath = Path('data', 'details', '20220907_120800.json')
        cur_ts_stats = extract_connection_stats(json_filepath)
        history = list()

        prev_ts_details = vars(cur_ts_stats.details).copy()
        prev_ts_details.pop('upstream_channels', None)
        prev_ts_details.pop('downstream_channels', None)
        prev_ts_details.pop('uptime', None)

        # When network_access changes
        prev_ts_details['network_access'] = 'Denied'
        prev_ts_details['timestamp'] = datetime.fromisoformat(cur_ts_stats.timestamp) - timedelta(minutes=10)
        history.append(prev_ts_details)
        self.assertTrue(transform_details(history, cur_ts_stats))
        self.assertEqual(2, len(history))
        self.assertFalse('upstream_channels' in history[len(history) - 1])
        self.assertFalse('downstream_channels' in history[len(history) - 1])
        self.assertFalse('uptime' in history[len(history) - 1])

        # When startup_steps changes
        prev_ts_details = prev_ts_details.copy()
        prev_ts_details['startup_steps'] = {'downstream': StartupStep(status='Not Ready')}
        prev_ts_details['timestamp'] = datetime.fromisoformat(cur_ts_stats.timestamp) - timedelta(minutes=5)
        history.append(prev_ts_details)
        self.assertTrue(transform_details(history, cur_ts_stats))
        self.assertEqual(4, len(history))
        self.assertFalse('upstream_channels' in history[len(history) - 1])
        self.assertFalse('downstream_channels' in history[len(history) - 1])
        self.assertFalse('uptime' in history[len(history) - 1])
