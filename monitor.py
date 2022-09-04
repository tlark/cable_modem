import argparse
import json
import logging
import os
from datetime import datetime, timedelta
from time import sleep

import schedule
from requests import ConnectTimeout

import log_config
from hnap import HNAPDevice

log_config.configure('monitor.log')
logger = logging.getLogger('monitor')

# Associate function calls with single word actions
actions = {'device': 'get_device_info',
           'summary': 'get_connection_summary',
           'events': 'get_events',
           'details': 'get_connection_details'}


def setup(device_id: str, device_attrs: dict, action_ids: list, note: str) -> HNAPDevice:
    device = None
    if device_id == 'arris':
        from arris import ArrisDevice

        device = ArrisDevice(device_id)
    elif device_id == 'motorola':
        from motorola import MotorolaDevice

        device = MotorolaDevice(device_id)

    device.login(device_attrs['scheme'], device_attrs['host'], device_attrs['username'], device_attrs['password'])

    # Create directories to hold JSON results and add any specified note to the README file
    for action_id in action_ids:
        path = '{}/{}'.format(device_id, action_id)
        os.makedirs(path, exist_ok=True)
        if note:
            with open('{}/README.txt'.format(path), 'a') as readme_file:
                readme_file.write('{}: {}\n'.format(datetime.now().strftime('%Y%m%d %H%M%S'), note))
    return device


def gather_stats(device: HNAPDevice, action_ids: list) -> timedelta:
    sleep_time = timedelta(seconds=300)

    print('{} Gathering {} stats'.format(datetime.now().strftime('%D %T'), device.device_id), end='...', flush=True)
    unique = datetime.now().strftime('%Y%m%d_%H%M%S')
    for action_id in action_ids:
        action_name = actions.get(action_id, None)
        if not action_name:
            logger.error('{} does not support {}'.format(device.device_id, action_id))
            continue

        print(action_id, end='...', flush=True)
        action = getattr(device, action_name, None)
        if not action:
            logger.error('{} does not have "{}" function for {}'.format(device.device_id, action_name, action_id))
            continue

        try:
            result = action()
            json_result = json.dumps(result, default=lambda o: o.__dict__)
            output_filename = '{}/{}/{}.json'.format(device.device_id, action_id, unique)
            with open(output_filename, 'w') as output_file:
                output_file.write(json_result)
        except Exception as e:
            print('FAILED ({})'.format(e), end='...', flush=True)
            logger.exception('{} FAILED for {}'.format(action_id, device.device_id))
            if isinstance(e, ConnectTimeout):
                sleep_time = timedelta(seconds=30)
            else:
                # Assume the session expired and needs to be refreshed
                device.session = None
                sleep_time = timedelta(seconds=5)
            break
    return sleep_time


def reboot(device: HNAPDevice):
    device.reboot()


def main():
    with open('devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    wanted_actions = ['device', 'summary', 'events', 'details']

    parser = argparse.ArgumentParser()
    parser.add_argument('--note', required=False)
    parser.add_argument('device', choices=supported_devices.keys())
    args = parser.parse_args()

    device_attrs = supported_devices.get(args.device)
    action_ids = [a for a in wanted_actions if a in device_attrs['supported_actions']]

    device = setup(args.device, device_attrs, action_ids, args.note)

    # Reboot the device every day at 4am and 4pm
    schedule.every().day.at("04:00").do(reboot, device=device)
    schedule.every().day.at("16:00").do(reboot, device=device)
    try:
        while True:
            schedule.run_pending()

            sleep_time = gather_stats(device, action_ids)

            print('sleeping until {}'.format((datetime.now() + sleep_time).strftime('%T')), flush=True)
            sleep(sleep_time.seconds)
    except KeyboardInterrupt:
        device.logout()
        pass


if __name__ == '__main__':
    main()
