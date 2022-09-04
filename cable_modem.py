import argparse
import json
import logging

import log_config

log_config.configure('cable_modem.log')
logger = logging.getLogger('cable_modem')


def main():
    with open('devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device', choices=supported_devices.keys())
    parser.add_argument('action', default='test', choices=['test', 'device', 'summary', 'details', 'events', 'reboot'])
    args = parser.parse_args()

    device_attrs = supported_devices.get(args.device)

    device = None
    if args.device == 'arris':
        from arris import ArrisDevice

        device = ArrisDevice(args.device)
    elif args.device == 'motorola':
        from motorola import MotorolaDevice

        device = MotorolaDevice(args.device)

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
