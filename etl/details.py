import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import log_config
from models import ConnectionDetails

log_config.configure('details.log')
logger = logging.getLogger('transformer')


class TimestampedResult:
    def __init__(self, timestamp: str, details: ConnectionDetails = None, error: str = None):
        self.timestamp = timestamp
        self.details = details
        self.error = error

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.__dict__)


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
        prev_stats.pop('timestamp', None)
        if cur_stats == prev_stats:
            logger.debug('No changes; ignoring {}'.format(cur_stats))
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
                json_file.write(json.dumps(channel_stats_history, sort_keys=True, indent=2))


def transform_details(history: list, cur_stats: TimestampedResult) -> bool:
    cur_startup_steps = cur_stats.details.startup_steps
    cur_network_access = cur_stats.details.network_access
    if history:
        prev_details = history[len(history) - 1]
        prev_startup_steps = prev_details.get('startup_steps', None)
        prev_network_access = prev_details.get('network_access', None)
        if prev_startup_steps == cur_startup_steps and prev_network_access == cur_network_access:
            logger.debug('No changes; ignoring {}'.format(cur_stats))
            return False

    # Change found...append entry to history
    cur_details = dict()
    cur_details['startup_steps'] = cur_startup_steps
    cur_details['network_access'] = cur_network_access
    cur_details['timestamp'] = cur_stats.timestamp
    history.append(cur_details)
    return True


def setup(root_path: Path, delete_src: bool) -> Path:
    combined_details_file = 'details.json'

    # If we're not deleting the source files, delete any existing target files
    if not delete_src:
        for sub_path_pattern in [combined_details_file, 'downstream/*.json', 'upstream/*.json']:
            files_to_delete = sorted(root_path.glob(sub_path_pattern))
            logger.info('Deleting {} files from {}/{}'.format(len(files_to_delete), root_path, sub_path_pattern))
            for file_to_delete in files_to_delete:
                logger.debug('Deleting {}'.format(file_to_delete))
                file_to_delete.unlink()
    return root_path / combined_details_file


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    parser.add_argument('--delete-src', action='store_true', help='Delete source files if all processing succeeds')
    args = parser.parse_args()

    root_path = Path('devices', args.device_id, 'details')

    combined_details_file = setup(root_path, args.delete_src)
    combined_details = list()

    # If deleting source files, then start with the existing combined details
    if args.delete_src:
        if combined_details_file.exists():
            with combined_details_file.open(mode='r') as fp:
                combined_details = json.load(fp)
    orig_details_size = len(combined_details)
    logger.info('Found {} already combined details in {}'.format(orig_details_size, combined_details_file))

    details_files = sorted(root_path.glob('2022*.json'))
    logger.info('Checking {} files'.format(len(details_files)))
    for details_file in details_files:
        stats = extract_connection_stats(details_file)

        if stats.error:
            combined_details.append({'timestamp': stats.timestamp, 'error': stats.error})
        else:
            transform_channel_stats('downstream', stats.timestamp, stats.details.downstream_channels, root_path)
            transform_channel_stats('upstream', stats.timestamp, stats.details.upstream_channels, root_path)
            transform_details(combined_details, stats)

    if orig_details_size != len(combined_details):
        logger.info('Transformed {} files into {} combined details'.format(len(details_files), len(combined_details)))
        with combined_details_file.open(mode='w') as fp:
            json.dump(combined_details, fp, default=lambda o: o.__dict__, indent=2)
    else:
        logger.info('No new details found in {} files'.format(len(details_files)))

    if args.delete_src:
        logger.info('Deleting {} files'.format(len(details_files)))
        for details_file in details_files:
            logger.debug('Deleting {}'.format(details_file))
            details_file.unlink()


if __name__ == '__main__':
    main()
