import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Union, Any, List

import log_config
from devices import create_device
from etl import finalize_target_files, sort_unique_ts_history
from hnap import HNAPDevice
from models import EventLogEntry

log_config.configure('events.log')
logger = logging.getLogger('transformer')
combined_file = 'events.json'


def get_event_ts(event: dict, synthetic_ts: datetime, device: HNAPDevice) -> Tuple[Union[datetime, Any], datetime]:
    if event.get('timestamp', None):
        ts = datetime.fromisoformat(event.get('timestamp'))
    else:
        try:
            ts = device.to_timestamp(event.get('date'), event.get('time'))
        except ValueError:
            synthetic_ts += timedelta(seconds=1)
            ts = synthetic_ts

    # Force ts year to be no earlier than epoch since we're doing math
    if ts.year < 1970:
        ts = ts.replace(year=1970)
    return ts, synthetic_ts


def process_unknown_ts_events(unknown_ts_events: List[EventLogEntry], cur_ts: datetime,
                              combined_events: List[EventLogEntry]):
    # Coerce any unknown timestamps based on this current event timestamp
    # Go back one second to differentiate these unknown events from real ones
    cur_ts = cur_ts - timedelta(seconds=1)
    for unknown_ts_event in reversed(unknown_ts_events):
        unknown_ts = datetime.fromisoformat(unknown_ts_event.timestamp)

        # Since we need to keep going back in time, if the unknown ts has the SAME minute/second
        # as the previous one, manually increment it
        offset = timedelta(minutes=unknown_ts.minute, seconds=unknown_ts.second)
        new_ts = cur_ts - offset
        unknown_ts_event.timestamp = new_ts.isoformat()
        combined_events.append(unknown_ts_event)
    unknown_ts_events.clear()


def combine_events(events: List[dict], device: HNAPDevice) -> List[dict]:
    unknown_ts_events = []
    combined_events = []
    ts = None
    synthetic_ts = datetime.fromisoformat('1970-01-01T00:00:00')

    for event in events:
        ts, synthetic_ts = get_event_ts(event, synthetic_ts, device)
        event_entry = EventLogEntry(timestamp=ts, priority=event.get('priority'), desc=event.get('desc'))

        # Collect unknown ts events.  Once we have a real ts, coerce the unknown events using the current ts.
        if ts.year <= 1970:
            unknown_ts_events.append(event_entry)
        else:
            combined_events.append(event_entry)
            process_unknown_ts_events(unknown_ts_events, ts, combined_events)

    # If the last event(s) in the file are unknown, process those now
    if unknown_ts_events:
        process_unknown_ts_events(unknown_ts_events, ts, combined_events)

    combined_events = json.loads(json.dumps(combined_events, default=lambda o: o.__dict__))
    return sort_unique_ts_history(combined_events)


def transform_events(cur_events: List[dict], combined_events_file: Path, device: HNAPDevice) -> bool:
    if not cur_events:
        return False

    orig_size = len(cur_events)
    cur_events = combine_events(cur_events, device)
    logger.debug('Found {} unique events from {} total'.format(len(cur_events), orig_size))

    events_history = list()
    if combined_events_file.exists():
        with combined_events_file.open() as json_file:
            logger.debug('Reading {}'.format(combined_events_file))
            events_history = json.load(json_file)

    updated_events_history = sort_unique_ts_history(events_history + cur_events)
    if events_history == updated_events_history:
        return False

    with combined_events_file.open(mode='w') as json_file:
        logger.debug('Updating {} with {} entries'.format(combined_events_file, len(updated_events_history)))
        json.dump(updated_events_history, fp=json_file, default=lambda o: o.__dict__, sort_keys=True, indent=2)
    return True


def extract_events(src_file: Path) -> List[dict]:
    if not src_file.exists():
        logger.warning('{} does not exist'.format(src_file))
        return list()

    with src_file.open() as file:
        logger.info('Processing {}'.format(src_file))
        cur_events = json.load(file)

    # 3 versions of source files exist: One with a list of events and one with 'result' value is the list of events
    if not isinstance(cur_events, list):
        if 'result' in cur_events:
            cur_events = cur_events['result']
        else:
            cur_events = [cur_events]
    return cur_events


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    args = parser.parse_args()

    root_path = Path('devices', args.device_id, 'events')
    processed_path = root_path / Path('processed')
    processed_path.mkdir(exist_ok=True)
    combined_events_file = root_path / Path(combined_file)

    device = create_device(args.device_id)

    src_file_pattern = '20*.json'
    src_files = sorted(root_path.glob(src_file_pattern))
    if not src_files:
        logger.info('No source files from {}/{}'.format(root_path, src_file_pattern))
        return

    logger.info('Checking {} files in {}'.format(len(src_files), root_path))
    for src_file in src_files:
        events = extract_events(src_file)
        transform_events(events, combined_events_file, device)

        # Getting here means the source file has been completely processed
        # Move source file to processed area
        src_file.rename(processed_path / src_file.name)

    # Finalize all target files: combined_file, upstream/*.json and downstream/*.json
    finalize_target_files(root_path, [combined_file], logger)


if __name__ == '__main__':
    main()
