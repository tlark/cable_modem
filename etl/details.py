import argparse
import json
import logging
from pathlib import Path
from typing import List

import log_config
from common import calc_stats_ts
from etl import finalize_target_files, compare_ts_history_with_current, TimestampedResult
from models import ConnectionDetails, ChannelStats

log_config.configure('details.log')
logger = logging.getLogger('transformer')
combined_file = 'details.json'


def extract_connection_stats(src_file: Path) -> TimestampedResult:
    with src_file.open() as json_file:
        logger.info('Processing {}'.format(src_file))
        json_stats = json.load(json_file)

    # json_stats will be a dict that SHOULD contain 'timestamp', 'result' keys
    # If not, calculate the timestamp from the filename
    timestamp = json_stats.get('timestamp', calc_stats_ts(src_file))
    result = json_stats.get('result', json_stats)
    if 'error' in result:
        return TimestampedResult(timestamp=timestamp, error=result['error'])
    else:
        return TimestampedResult(timestamp=timestamp, result=ConnectionDetails(**result))


def is_channel_stats_changed(json_history: List[dict], cur_stats: dict, cur_ts: str) -> bool:
    return compare_ts_history_with_current(json_history, cur_stats, cur_ts, logger)


def transform_channel_stats(channel_type: str, timestamp: str, cur_stats_list: List[ChannelStats], root_path: Path):
    channel_stats_path = root_path / channel_type
    channel_stats_path.mkdir(exist_ok=True)

    for cur_stats in cur_stats_list:
        logger.debug('Processing {} channel {}'.format(channel_type, cur_stats.channel_id))
        channel_stats_file = channel_stats_path / f'ch{cur_stats.channel_id:02}.json'

        channel_stats_history = list()
        if channel_stats_file.exists():
            with channel_stats_file.open() as json_file:
                logger.debug('Reading {}'.format(channel_stats_file))
                channel_stats_history = json.load(json_file)

        if is_channel_stats_changed(channel_stats_history, vars(cur_stats), timestamp):
            with channel_stats_file.open(mode='w') as json_file:
                logger.debug('Updating {} with {} entries'.format(channel_stats_file, len(channel_stats_history)))
                json.dump(channel_stats_history, fp=json_file, default=lambda o: o.__dict__, sort_keys=True, indent=2)


def transform_details_stats(cur_stats: TimestampedResult, details_history: List[dict]) -> bool:
    # Determine if the current stats are different than the previous entry
    cur_startup_steps = cur_stats.result.startup_steps
    cur_network_access = cur_stats.result.network_access

    if details_history:
        prev_details = details_history[len(details_history) - 1]
        prev_startup_steps = prev_details.get('startup_steps', None)
        prev_network_access = prev_details.get('network_access', None)
        if prev_startup_steps == cur_startup_steps and prev_network_access == cur_network_access:
            logger.debug('No changes; ignoring {}'.format(cur_stats))
            return False

    # Change found...append entry to history
    cur_details = dict()
    cur_details['timestamp'] = cur_stats.timestamp
    cur_details['startup_steps'] = cur_startup_steps
    cur_details['network_access'] = cur_network_access
    details_history.append(cur_details)
    return True


def transform_details(cur_stats: TimestampedResult, combined_details_file: Path) -> bool:
    cur_details = dict()

    details_history = list()
    if combined_details_file.exists():
        with combined_details_file.open() as json_file:
            logger.debug('Reading {}'.format(combined_details_file))
            details_history = json.load(json_file)

    # If the result is an error (instead of actual stats), simply append to the history
    if cur_stats.error:
        cur_details['timestamp'] = cur_stats.timestamp
        cur_details['error'] = cur_stats.error
        details_history.append(cur_details)
        changed = True
    else:
        changed = transform_details_stats(cur_stats, details_history)

    if changed:
        with combined_details_file.open(mode='w') as json_file:
            logger.debug('Updating {} with {} entries'.format(combined_details_file, len(details_history)))
            json.dump(details_history, fp=json_file, default=lambda o: o.__dict__, sort_keys=True, indent=2)

    return changed


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    args = parser.parse_args()

    root_path = Path('devices', args.device_id, 'details')
    processed_path = root_path / Path('processed')
    processed_path.mkdir(exist_ok=True)
    combined_details_file = root_path / Path(combined_file)

    src_file_pattern = '20*.json'
    src_files = sorted(root_path.glob(src_file_pattern))
    if not src_files:
        logger.info('No source files from {}/{}'.format(root_path, src_file_pattern))
        return

    logger.info('Checking {} files in {}'.format(len(src_files), root_path))
    for src_file in src_files:
        stats = extract_connection_stats(src_file)

        transform_details(stats, combined_details_file)
        if not stats.error:
            transform_channel_stats('downstream', stats.timestamp, stats.result.downstream_channels, root_path)
            transform_channel_stats('upstream', stats.timestamp, stats.result.upstream_channels, root_path)

        # Getting here means the source file has been completely processed
        # Move source file to processed area
        src_file.rename(processed_path / src_file.name)

    # Finalize all target files: combined_file, upstream/*.json and downstream/*.json
    finalize_target_files(root_path, [combined_file, 'downstream/*.json', 'upstream/*.json'], logger)


if __name__ == '__main__':
    main()
