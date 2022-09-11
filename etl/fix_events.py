import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import log_config
from common import get_stats_history, set_stats_history
from devices import create_device

log_config.configure('fix_events.log')
logger = logging.getLogger('transformer')


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    args = parser.parse_args()

    root_path = Path('devices', args.device_id, 'events')

    device = create_device(args.device_id)

    new_history = list()
    history = get_stats_history(device, 'events', logger)
    logger.info('Starting with {} history events'.format(len(history)))
    client_events_count = 0
    for event in history:
        if not event.get('desc', '').startswith('(Client'):
            new_history.append(event)
            continue

        ts = datetime.fromisoformat(event.get('timestamp', None))
        output_file = Path(root_path, '{}.json'.format(ts.strftime('%Y%m%d_%H%M%S')))
        with output_file.open(mode='w') as file:
            json.dump([event], fp=file)
            client_events_count += 1

    history_removed_count = len(history) - len(new_history)
    if history_removed_count != client_events_count:
        logger.error('{} client events does not match {} history removed events!'.format(client_events_count,
                                                                                         history_removed_count))
        return

    logger.info('Replacing history with {} events'.format(len(new_history)))
    set_stats_history(device, 'events', new_history, logger)


if __name__ == '__main__':
    main()
