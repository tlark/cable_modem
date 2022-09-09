import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Union, Any

import log_config
from devices import create_device
from hnap import HNAPDevice
from models import EventLogEntry

log_config.configure('events.log')
logger = logging.getLogger('transformer')


def handle_file(input_file: Path, device: HNAPDevice) -> dict:
    with input_file.open() as file:
        logger.debug('Processing {}'.format(input_file))
        json_events = json.load(file)

    unknown_ts_events = []
    combined_file_events = {}
    ts = None
    synthetic_ts = datetime.fromisoformat('1970-01-01T00:00:00')

    if not isinstance(json_events, list):
        json_events = json_events['result']
    for json_event in json_events:
        ts, synthetic_ts = get_event_timestamp(json_event, synthetic_ts, device)
        event = EventLogEntry(timestamp=ts, priority=json_event.get('priority'), desc=json_event.get('desc'))

        # Collect unknown ts events.  Once we have a real ts, coerce the unknown events using the current ts.
        if ts.year == 1970:
            unknown_ts_events.append(event)
        else:
            combined_file_events[event] = None
            process_unknown_timestamp_events(unknown_ts_events, ts, combined_file_events)

    # If the last event(s) in the file are unknown, process those now
    if unknown_ts_events:
        process_unknown_timestamp_events(unknown_ts_events, ts, combined_file_events)

    logger.debug('Found {} unique events from {}'.format((len(combined_file_events)), input_file))
    return combined_file_events


def process_unknown_timestamp_events(unknown_ts_events: list, cur_ts: datetime, combined_events: dict):
    # Now, coerce any unknown timestamps based on this current event timestamp
    prev_offset = None
    prev_ts = cur_ts
    for unknown_ts_event in reversed(unknown_ts_events):
        unknown_ts = datetime.fromisoformat(unknown_ts_event.timestamp)
        offset = timedelta(minutes=unknown_ts.minute, seconds=unknown_ts.second)
        new_ts = prev_ts - ((prev_offset - offset) if prev_offset else offset)
        unknown_ts_event.timestamp = new_ts.isoformat()
        combined_events[unknown_ts_event] = None

        prev_offset = offset
        prev_ts = new_ts
    unknown_ts_events.clear()


def get_event_timestamp(event: dict, synthetic_ts: datetime, device: HNAPDevice) -> Tuple[
    Union[datetime, Any], datetime]:
    if event.get('timestamp', None):
        ts = datetime.fromisoformat(event.get('timestamp'))
    else:
        try:
            ts = device.to_timestamp(event.get('date'), event.get('time'))
        except ValueError:
            synthetic_ts += timedelta(seconds=1)
            ts = synthetic_ts
    return ts, synthetic_ts


def setup(root_path: Path, delete_src: bool) -> Path:
    combined_file = 'events.json'

    # If we're not deleting the source files, delete any existing target files
    if not delete_src:
        for sub_path_pattern in [combined_file]:
            files_to_delete = sorted(root_path.glob(sub_path_pattern))
            logger.info('Deleting {} files from {}/{}'.format(len(files_to_delete), root_path, sub_path_pattern))
            for file_to_delete in files_to_delete:
                logger.debug('Deleting {}'.format(file_to_delete))
                file_to_delete.unlink()
    return root_path / combined_file


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    parser.add_argument('--delete-src', action='store_true', help='Delete source files if all processing succeeds')
    args = parser.parse_args()

    root_path = Path('devices', args.device_id, 'events')

    combined_events_file = setup(root_path, args.delete_src)
    combined_events = dict()

    # If deleting source files, then start with the existing combined events
    if args.delete_src:
        if combined_events_file.exists():
            with combined_events_file.open(mode='r') as fp:
                combined_events = {e: None for e in json.load(fp)}
    orig_combined_size = len(combined_events)
    logger.info('Found {} already combined events in {}'.format(orig_combined_size, combined_events_file))

    device = create_device(args.device_id)

    src_files = sorted(root_path.glob('2022*.json'))
    logger.info('Checking {} files'.format(len(src_files)))
    total_file_events = 0
    for src_file in src_files:
        prev_combined_size = len(combined_events)
        combined_file_events = handle_file(src_file, device)
        total_file_events += len(combined_file_events)
        combined_events.update(combined_file_events)
        logger.debug('Added {} events from {}'.format((len(combined_events) - prev_combined_size), src_file))

    logger.info('Transformed {} file events into {} combined events'.format(total_file_events, len(combined_events)))
    with combined_events_file.open(mode='w') as file:
        json.dump(sorted(combined_events.keys(), key=lambda e: e.timestamp), fp=file, default=lambda o: o.__dict__,
                  sort_keys=True, indent=2)

    if args.delete_src:
        logger.info('Deleting {} files'.format(len(src_files)))
        for src_file in src_files:
            logger.debug('Deleting {}'.format(src_file))
            src_file.unlink()


if __name__ == '__main__':
    main()
