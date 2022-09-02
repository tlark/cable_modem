import argparse
import json
import logging
import os
from datetime import datetime, timedelta
from logging.config import fileConfig
from time import sleep

logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)
logger = logging.getLogger('monitor')

actions = {'device': 'get_device_info',
           'summary': 'get_connection_summary',
           'events': 'get_events',
           'details': 'get_connection_details'}

if __name__ == '__main__':
    with open('devices.json') as devices_file:
        devices = json.load(devices_file)

    wanted_actions = ['device', 'summary', 'events', 'details']

    parser = argparse.ArgumentParser()
    parser.add_argument('--note', required=False)
    parser.add_argument('device', choices=devices.keys())
    args = parser.parse_args()

    device = devices.get(args.device)
    action_ids = [a for a in wanted_actions if a in device.get('supported_actions')]

    system = None
    if args.device == 'arris':
        from arris import ArrisSystem

        system = ArrisSystem()
    elif args.device == 'motorola':
        from motorola import MotorolaSystem

        system = MotorolaSystem()

    system.login(device.get('scheme'), device.get('host'), device.get('username'), device.get('password'))

    # Create directories to hold JSON results and add any specified note to the README file
    for action_id in action_ids:
        path = '{}/{}'.format(args.device, action_id)
        os.makedirs(path, exist_ok=True)
        if args.note:
            with open('{}/README.txt'.format(path), 'a') as readme_file:
                readme_file.write('{}: {}\n'.format(datetime.now().strftime('%Y%m%d %H%M%S'), args.note))

    try:
        sleep_time = timedelta(seconds=300)
        while True:
            print('{} Gathering {} stats'.format(datetime.now().strftime('%D %T'), args.device), end='...', flush=True)
            unique = datetime.now().strftime('%Y%m%d_%H%M%S')
            for action_id in action_ids:
                action_name = actions.get(action_id, None)
                if not action_name:
                    logger.error('{} does not support {}'.format(system, action_id))
                    continue

                print(action_id, end='...', flush=True)
                action = getattr(system, action_name, None)
                if not action:
                    logger.error('{} does not have "{}" function for {}'.format(system, action_name, action_id))
                    continue

                sleep_time = timedelta(seconds=300)
                try:
                    result = action()
                    json_result = json.dumps(result, default=lambda o: o.__dict__)
                    output_filename = '{}/{}/{}.json'.format(args.device, action_id, unique)
                    with open(output_filename, 'w') as output_file:
                        output_file.write(json_result)
                except Exception as e:
                    print('FAILED', end='...', flush=True)
                    logger.exception('{} FAILED for {}'.format(action_id, system))
                    sleep_time = timedelta(seconds=30)
                    break

            print('sleeping until {}'.format((datetime.now() + sleep_time).strftime('%T')), flush=True)
            sleep(sleep_time.seconds)

    except KeyboardInterrupt:
        system.logout()
        pass
