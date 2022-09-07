from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase

from etl.details import extract_connection_stats, is_channel_stats_change
from hnap import HNAPDevice

device = HNAPDevice('test')


class TestDetails(TestCase):
    def test_extract_connection_details_when_no_timestamp(self):
        json_filepath = Path('testdata', 'details', '20220830_185833.json')
        act = extract_connection_stats(json_filepath)
        self.assertEqual(datetime(2022, 8, 30, 18, 58, 33).isoformat(), act.timestamp)
        self.assertEqual(5, len(act.stats.startup_steps))
        self.assertEqual(4, len(act.stats.upstream_channels))
        self.assertEqual(32, len(act.stats.downstream_channels))
        self.assertEqual('Allowed', act.stats.network_access)

    def test_extract_connection_details_when_timestamp(self):
        json_filepath = Path('testdata', 'details', '20220907_120800.json')
        act = extract_connection_stats(json_filepath)
        # 2022-09-07T12:08:05.751985
        self.assertEqual(datetime(2022, 9, 7, 12, 8, 5, 751985).isoformat(), act.timestamp)
        self.assertEqual(5, len(act.stats.startup_steps))
        self.assertEqual(4, len(act.stats.upstream_channels))
        self.assertEqual(32, len(act.stats.downstream_channels))
        self.assertEqual('Allowed', act.stats.network_access)

    def test_model_equality(self):
        json_filepath = Path('testdata', 'details', '20220907_120800.json')
        act = extract_connection_stats(json_filepath)
        ch1 = act.stats.downstream_channels[0]
        ch2 = act.stats.downstream_channels[1]
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
        json_filepath = Path('testdata', 'details', '20220907_120800.json')
        cur_ts_stats = extract_connection_stats(json_filepath)

        for cur_stats in cur_ts_stats.stats.downstream_channels:
            history = list()
            self.assertTrue(is_channel_stats_change(history, vars(cur_stats).copy(), cur_ts_stats.timestamp))
            self.assertEquals(1, len(history))

    def test_is_channel_stats_change_when_no_change(self):
        json_filepath = Path('testdata', 'details', '20220907_120800.json')
        cur_ts_stats = extract_connection_stats(json_filepath)

        for cur_stats in cur_ts_stats.stats.downstream_channels:
            history = list()
            prev_ts_stats = vars(cur_stats).copy()
            prev_ts_stats['timestamp'] = datetime.fromisoformat(cur_ts_stats.timestamp) - timedelta(minutes=10)
            history.append(prev_ts_stats)
            self.assertFalse(is_channel_stats_change(history, vars(cur_stats).copy(), cur_ts_stats.timestamp))
            self.assertEquals(1, len(history))

    def test_is_channel_stats_change_when_change(self):
        json_filepath = Path('testdata', 'details', '20220907_120800.json')
        cur_ts_stats = extract_connection_stats(json_filepath)

        for cur_stats in cur_ts_stats.stats.downstream_channels:
            history = list()
            prev_ts_stats = vars(cur_stats).copy()
            prev_ts_stats['corrected'] = cur_stats.corrected + 10
            prev_ts_stats['timestamp'] = datetime.fromisoformat(cur_ts_stats.timestamp) - timedelta(minutes=10)
            history.append(prev_ts_stats)
            self.assertTrue(is_channel_stats_change(history, vars(cur_stats).copy(), cur_ts_stats.timestamp))
            self.assertEquals(2, len(history))
