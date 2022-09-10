import argparse
import json
import logging

import log_config
from devices import create_device

log_config.configure('api_tester.log')
logger = logging.getLogger('api_tester')


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', choices=supported_devices.keys())
    parser.add_argument('action', default='test', choices=['test', 'device', 'summary', 'details', 'events', 'reboot'])
    args = parser.parse_args()

    device_attrs = supported_devices.get(args.device_id)

    device = create_device(args.device_id)
    device.login(device_attrs['scheme'], device_attrs['host'], device_attrs['username'], device_attrs['password'])

    if args.action == 'test':
        for command in device.get_commands():
            if command.read_only:
                logger.info('Testing {}...'.format(command))
                print(json.dumps(device.do_command(command), default=lambda o: o.__dict__))
    elif args.action == 'device':
        print(json.dumps(device.get_device_info(), default=lambda o: o.__dict__))
    elif args.action == 'summary':
        print(json.dumps(device.get_connection_summary(), default=lambda o: o.__dict__))
    elif args.action == 'details':
        print(json.dumps(device.get_connection_details(), default=lambda o: o.__dict__))
    elif args.action == 'events':
        print(json.dumps(device.get_events(), default=lambda o: o.__dict__))
    elif args.action == 'reboot':
        device.reboot()

    device.logout()


if __name__ == '__main__':
    main()
