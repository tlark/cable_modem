import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import log_config
from devices import create_device
from models import ConnectionDetails

log_config.configure('details.log')
logger = logging.getLogger('transformer')


class TimestampedConnectionStats:
    def __init__(self, timestamp: str, stats: ConnectionDetails):
        self.timestamp = timestamp
        self.stats = stats


def extract_connection_stats(input_file_path: Path) -> TimestampedConnectionStats:
    with input_file_path.open() as json_file:
        logger.debug('Processing {}'.format(input_file_path))
        json_stats = json.load(json_file)

    # json_stats will be a dict that SHOULD contain 'timestamp', 'result' keys
    # If not, calculate the timestamp from the filename
    timestamp = json_stats.get('timestamp', datetime.strptime(input_file_path.stem, '%Y%m%d_%H%M%S').isoformat())
    result = json_stats.get('result', json_stats)
    return TimestampedConnectionStats(timestamp=timestamp, stats=ConnectionDetails(**result))


def is_channel_stats_change(history: list, cur_stats: dict, cur_ts: str) -> bool:
    if history:
        # Compare (excluding the timestamp key) the last entry to this current one
        prev_ts_stats = history[len(history) - 1]
        prev_stats = dict(prev_ts_stats)
        prev_stats.pop('timestamp')
        if cur_stats == prev_stats:
            logger.debug('No changes; prev={}, cur={}'.format(prev_stats, cur_stats))
            return False

    # Change found...append entry to history
    cur_ts_stats = cur_stats.copy()
    cur_ts_stats['timestamp'] = cur_ts
    history.append(cur_ts_stats)
    return True


def transform_downstream_channel_stats(ts_stats: TimestampedConnectionStats, root_json_path: Path):
    downstream_path = root_json_path / 'downstream'
    downstream_path.mkdir(exist_ok=True)

    for cur_stats in ts_stats.stats.downstream_channels:
        channel_file_path = downstream_path / f'ch{cur_stats.channel_id:02}.json'

        with channel_file_path.open() as json_file:
            logger.debug('Reading {}'.format(channel_file_path))
            channel_stats_history = json.load(json_file)

        if is_channel_stats_change(channel_stats_history, vars(cur_stats).copy(), ts_stats.timestamp):
            with channel_file_path.open(mode='w') as json_file:
                logger.debug('Updating {}'.format(channel_file_path))
                json_file.write(json.dumps(channel_stats_history))
    return


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    args = parser.parse_args()

    device = create_device(args.device_id)

    root_json_path = Path('devices', args.device_id, 'details')
    input_filenames = sorted(root_json_path.glob('2022*.json'))
    logger.info('Checking {} files'.format(len(input_filenames)))
    for input_filename in input_filenames:
        stats = extract_connection_stats(input_filename)
        transform_downstream_channel_stats(stats, root_json_path)

    # json_result = json.dumps(sorted(combined_events.keys(), key=lambda e: e.timestamp), default=lambda o: o.__dict__)
    # output_filename = 'devices/{}/details.json'.format(args.device_id)
    # with open(output_filename, 'w') as output_file:
    #     output_file.write(json_result)


if __name__ == '__main__':
    main()
