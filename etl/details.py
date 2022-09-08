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


class TimestampedResult:
    def __init__(self, timestamp: str, details: ConnectionDetails = None, error: str = None):
        self.timestamp = timestamp
        self.details = details
        self.error = error


def extract_connection_stats(input_file_path: Path) -> TimestampedResult:
    with input_file_path.open() as json_file:
        logger.info('Processing {}'.format(input_file_path))
        json_stats = json.load(json_file)

    # json_stats will be a dict that SHOULD contain 'timestamp', 'result' keys
    # If not, calculate the timestamp from the filename
    timestamp = json_stats.get('timestamp', datetime.strptime(input_file_path.stem, '%Y%m%d_%H%M%S').isoformat())
    result = json_stats.get('result', json_stats)
    if 'error' in result:
        return TimestampedResult(timestamp=timestamp, error=result['error'])
    else:
        return TimestampedResult(timestamp=timestamp, details=ConnectionDetails(**result))


def is_channel_stats_changed(history: list, cur_stats: dict, cur_ts: str) -> bool:
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


def transform_channel_stats(channel_type: str, timestamp: str, channel_stats_list: list, root_json_path: Path):
    channel_stats_path = root_json_path / channel_type
    channel_stats_path.mkdir(exist_ok=True)

    for cur_stats in channel_stats_list:
        logger.debug('Processing {} channel {}'.format(channel_type, cur_stats.channel_id))
        channel_stats_file_path = channel_stats_path / f'ch{cur_stats.channel_id:02}.json'

        channel_stats_history = list()
        if channel_stats_file_path.exists():
            with channel_stats_file_path.open() as json_file:
                logger.debug('Reading {}'.format(channel_stats_file_path))
                channel_stats_history = json.load(json_file)

        if is_channel_stats_changed(channel_stats_history, vars(cur_stats).copy(), timestamp):
            with channel_stats_file_path.open(mode='w') as json_file:
                logger.debug('Updating {}'.format(channel_stats_file_path))
                json_file.write(json.dumps(channel_stats_history))


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    parser.add_argument('--delete-files', type=bool, help='Delete files that get successfully processed')
    args = parser.parse_args()

    device = create_device(args.device_id)

    combined_details = list()

    root_json_path = Path('devices', args.device_id, 'details')
    input_filenames = sorted(root_json_path.glob('2022*.json'))
    logger.info('Checking {} files'.format(len(input_filenames)))
    for input_filename in input_filenames:

        try:
            stats = extract_connection_stats(input_filename)

            if stats.error:
                combined_details.append({'timestamp': stats.timestamp, 'error': stats.error})
            else:
                transform_channel_stats('downstream', stats.timestamp, stats.details.downstream_channels, root_json_path)
                transform_channel_stats('upstream', stats.timestamp, stats.details.upstream_channels, root_json_path)

            # Getting here means the file was successfully processed
            if args.delete_files:
                logger.info('Deleting {}'.format(input_filename))
                input_filename.unlink()
        except Exception as e:
            logger.error('Processing {} FAILED ({})'.format(input_filename, e))

    # json_result = json.dumps(sorted(combined_events.keys(), key=lambda e: e.timestamp), default=lambda o: o.__dict__)
    # output_filename = 'devices/{}/details.json'.format(args.device_id)
    # with open(output_filename, 'w') as output_file:
    #     output_file.write(json_result)


if __name__ == '__main__':
    main()
