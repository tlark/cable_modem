import argparse
import glob
import json
import logging
from datetime import datetime, timedelta

import logging_config
from models import EventLogEntry

logging_config.configure()
logger = logging.getLogger('transformer')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('device')
    args = parser.parse_args()

    system = None
    if args.device == 'arris':
        from arris import ArrisSystem

        system = ArrisSystem()
    elif args.device == 'motorola':
        from motorola import MotorolaSystem

        system = MotorolaSystem()

    combined_events = {}
    unknown_ts_events = []

    json_filenames = sorted(glob.glob('{}/events/2022*.json'.format(args.device)))
    logger.info('Checking {} files'.format(len(json_filenames)))
    for json_filename in json_filenames:
        prev_combined_size = len(combined_events)
        with open(json_filename) as json_file:
            logger.debug('Processing {}'.format(json_filename))

            synthetic_ts = datetime.fromisoformat('1970-01-01T00:00:00')
            json_events = json.load(json_file)
            for json_event in json_events:
                if json_event.get('timestamp', None):
                    ts = datetime.fromisoformat(json_event.get('timestamp'))
                else:
                    try:
                        ts = system.to_timestamp(json_event.get('date'), json_event.get('time'))
                    except ValueError as ve:
                        synthetic_ts += timedelta(seconds=1)
                        ts = synthetic_ts

                event = EventLogEntry(timestamp=ts, priority=json_event.get('priority'), desc=json_event.get('desc'))

                # Is this an unknown timestamp?
                if ts.year == 1970:
                    unknown_ts_events.append(event)
                else:
                    combined_events[event] = None

                    # Now, coerce any unknown timestamps based on this current event timestamp
                    prev_offset = None
                    prev_ts = ts
                    for unknown_ts_event in reversed(unknown_ts_events):
                        unknown_ts = datetime.fromisoformat(unknown_ts_event.timestamp)
                        offset = timedelta(minutes=unknown_ts.minute, seconds=unknown_ts.second)
                        new_ts = prev_ts - ((prev_offset - offset) if prev_offset else offset)
                        unknown_ts_event.timestamp = new_ts.isoformat()
                        combined_events[unknown_ts_event] = None

                        prev_offset = offset
                        prev_ts = new_ts
                    unknown_ts_events.clear()

            logger.info('Added {} events from {}'.format((len(combined_events) - prev_combined_size), json_filename))

    logger.info('Transformed {} events'.format(len(combined_events)))
    json_result = json.dumps(sorted(combined_events.keys(), key=lambda e: e.timestamp), default=lambda o: o.__dict__)
    output_filename = '{}/events.json'.format(args.device)
    with open(output_filename, 'w') as output_file:
        output_file.write(json_result)
