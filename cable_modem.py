import argparse
import json
import logging
from logging.config import fileConfig

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    with open('devices.json') as devices_file:
        devices = json.load(devices_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('device', choices=devices.keys())
    parser.add_argument('action', default='test', choices=['test', 'device', 'summary', 'details', 'events', 'reboot'])
    args = parser.parse_args()

    device = devices.get(args.device)

    system = None
    if args.device == 'arris':
        from arris import ArrisSystem

        system = ArrisSystem()
    elif args.device == 'motorola':
        from motorola import MotorolaSystem

        system = MotorolaSystem()

    hnap_session = system.login(device.get('scheme'), device.get('host'), device.get('username'),
                                device.get('password'))

    if args.action == 'test':
        for command in system.get_commands(hnap_session):
            if command.read_only:
                logger.info('Testing {}...'.format(command))
                print(json.dumps(system.do_command(hnap_session, command), default=lambda o: o.__dict__))
    elif args.action == 'device':
        print(json.dumps(system.get_device_info(hnap_session), default=lambda o: o.__dict__))
    elif args.action == 'summary':
        print(json.dumps(system.get_connection_summary(hnap_session), default=lambda o: o.__dict__))
    elif args.action == 'details':
        print(json.dumps(system.get_connection_details(hnap_session), default=lambda o: o.__dict__))
    elif args.action == 'events':
        print(json.dumps(system.get_events(hnap_session), default=lambda o: o.__dict__))
    elif args.action == 'reboot':
        system.reboot(hnap_session)
