import argparse
import glob
import json
import logging
from datetime import datetime, timedelta
from typing import Tuple, Union, Any

import log_config
from devices import create_device
from hnap import HNAPDevice
from models import EventLogEntry

log_config.configure('events.log')
logger = logging.getLogger('transformer')


def handle_file(json_filename: str, device: HNAPDevice) -> dict:
    with open(json_filename) as json_file:
        logger.debug('Processing {}'.format(json_filename))
        json_events = json.load(json_file)

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

    logger.debug('Found {} unique events from {}'.format((len(combined_file_events)), json_filename))
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


def get_event_timestamp(event: dict, synthetic_ts: datetime, device: HNAPDevice) -> Tuple[Union[datetime, Any], datetime]:
    if event.get('timestamp', None):
        ts = datetime.fromisoformat(event.get('timestamp'))
    else:
        try:
            ts = device.to_timestamp(event.get('date'), event.get('time'))
        except ValueError:
            synthetic_ts += timedelta(seconds=1)
            ts = synthetic_ts
    return ts, synthetic_ts


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    args = parser.parse_args()

    device = create_device(args.device_id)

    combined_events = {}

    json_filenames = sorted(glob.glob('devices/{}/events/2022*.json'.format(args.device_id)))
    logger.info('Checking {} files'.format(len(json_filenames)))
    total_file_events = 0
    for json_filename in json_filenames:
        prev_combined_size = len(combined_events)
        combined_file_events = handle_file(json_filename, device)
        total_file_events += len(combined_file_events)
        combined_events.update(combined_file_events)
        logger.debug('Added {} events from {}'.format((len(combined_events) - prev_combined_size), json_filename))

    logger.info('Transformed {} file events into {} combined events'.format(total_file_events, len(combined_events)))
    json_result = json.dumps(sorted(combined_events.keys(), key=lambda e: e.timestamp), default=lambda o: o.__dict__)
    output_filename = 'devices/{}/events.json'.format(args.device_id)
    with open(output_filename, 'w') as output_file:
        output_file.write(json_result)


if __name__ == '__main__':
    main()
