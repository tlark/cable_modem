import argparse
import json
import logging
from pathlib import Path

import log_config
from common import calc_stats_ts
from etl import finalize_target_files, compare_ts_history_with_current, TimestampedResult
from models import ConnectionSummary

log_config.configure('summary.log')
logger = logging.getLogger('transformer')
combined_file = 'summary.json'


def extract_summary(src_file: Path) -> TimestampedResult:
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
        return TimestampedResult(timestamp=timestamp, result=ConnectionSummary(**result))


def transform_summary(cur_ts_summary: TimestampedResult, combined_summaries_file: Path) -> bool:
    summaries_history = list()
    if combined_summaries_file.exists():
        with combined_summaries_file.open() as json_file:
            logger.debug('Reading {}'.format(combined_summaries_file))
            summaries_history = json.load(json_file)

    cur_summary = dict()

    # If the result is an error (instead of an actual summary), simply append to the history
    if cur_ts_summary.error:
        cur_summary['error'] = cur_ts_summary.error
        cur_summary['timestamp'] = cur_ts_summary.timestamp
        summaries_history.append(cur_summary)
        changed = True
    else:
        # Determine if the current summary is different than the previous one, ignoring timestamp
        cur_summary.update(vars(cur_ts_summary.result))
        changed = compare_ts_history_with_current(summaries_history, cur_summary, cur_ts_summary.timestamp, logger)

    if not changed:
        logger.debug('No changes; ignoring {}'.format(cur_ts_summary))
        return False

    with combined_summaries_file.open(mode='w') as json_file:
        logger.info('Updating {} with {} entries'.format(combined_summaries_file, len(summaries_history)))
        json.dump(summaries_history, fp=json_file, default=lambda o: o.__dict__, sort_keys=True, indent=2)

    return changed


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    args = parser.parse_args()

    root_path = Path('devices', args.device_id, 'summary')
    processed_path = root_path / Path('processed')
    processed_path.mkdir(exist_ok=True)
    combined_summaries_file = root_path / Path(combined_file)

    src_files = sorted(root_path.glob('2022*.json'))
    logger.info('Checking {} files in {}'.format(len(src_files), root_path))
    for src_file in src_files:
        summary = extract_summary(src_file)
        transform_summary(summary, combined_summaries_file)

        # Getting here means the source file has been completely processed
        # Move source file to processed area
        src_file.rename(processed_path / src_file.name)

    # Finalize all target files: combined_file, upstream/*.json and downstream/*.json
    finalize_target_files(root_path, [combined_file], logger)


if __name__ == '__main__':
    main()
