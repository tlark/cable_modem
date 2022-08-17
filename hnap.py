#!/usr/bin/env python3
import argparse
import hmac
import json
import logging
import time
from logging.config import fileConfig

import requests
# Disable warnings for ignoring SSL cert verification
import urllib3

urllib3.disable_warnings()

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)


class HNAPSession:
    def __init__(self, host, scheme):
        self.scheme = scheme
        self.host = host
        self.http_session = requests.Session()
        self.private_key = None
        self.cookie_id = None
        self.digestmod = 'md5'
        self.encoded_password = None

    def authenticate(self, challenge, public_key, password, cookie_id):
        self.private_key = hmac.new(public_key + password, challenge, digestmod=self.digestmod).hexdigest().upper()
        self.encoded_password = hmac.new(self.private_key.encode(), challenge,
                                         digestmod=self.digestmod).hexdigest().upper()
        self.cookie_id = cookie_id

    def authenticate_operation(self, operation):
        now = str(int(time.time() * 1000))
        auth_key = '{}"http://purenetworks.com/HNAP1/{}"'.format(now, operation)
        key = (self.private_key or 'withoutloginkey').encode()
        auth = hmac.new(key, auth_key.encode(), digestmod=self.digestmod)
        return '{} {}'.format(auth.hexdigest().upper(), now)

    def get_cookies(self):
        return {'uid': '{}'.format(self.cookie_id),
                'PrivateKey': '{}'.format(self.private_key)}


class HNAPCommand:
    def __init__(self, operation, payload_data=None):
        self.operation = operation
        self.payload_data = payload_data

    def __str__(self):
        return '{} (operation={})'.format(self.__class__.__name__, self.operation)

    def build_payload_data(self, **kwargs):
        return self.payload_data

    def execute(self, session, **kwargs):
        url = '{}://{}/HNAP1/'.format(session.scheme, session.host)
        auth = session.authenticate_operation(self.operation)
        headers = {'HNAP_AUTH': auth, 'SOAPAction': '"http://purenetworks.com/HNAP1/{}"'.format(self.operation)}
        cookies = session.get_cookies()
        body = {self.operation: self.build_payload_data(**kwargs)}

        try:
            logger.debug(">>>> {}: url={}, headers={}, cookies={}, body={}".format(self, url, headers, cookies, body))
            r = session.http_session.post(url, headers=headers, cookies=cookies, json=body, verify=False)
            logger.debug("<<<< {}: url={}, code={}, body={}".format(self, url, r.status_code, json.loads(r.text)))
            return r
        except Exception as ex:
            logger.exception(ex)
            exit(-1)

    def validate_response(self, response):
        if response.status_code >= 300:
            raise ValueError('{}: Invalid response code={}'.format(self, response.status_code))


class LoginRequest(HNAPCommand):
    def __init__(self):
        super().__init__('Login')

    def build_payload_data(self, **kwargs):
        return {'Action': 'request',
                'Captcha': '',
                'PrivateLogin': 'LoginPassword',
                'Username': kwargs['username'],
                'LoginPassword': ''}

    def validate_response(self, response):
        body = json.loads(response.text)

        login_response = body.get('LoginResponse')
        if not login_response:
            raise ValueError('Missing LoginResponse in {}'.format(body))

        login_result = login_response.get('LoginResult')
        if login_result != 'OK':
            raise ValueError('Invalid LoginResult={}'.format(login_result))

        return login_response


class Login(LoginRequest):
    def build_payload_data(self, **kwargs):
        return {'Action': 'login',
                'Captcha': '',
                'PrivateLogin': 'LoginPassword',
                'Username': kwargs['username'],
                'LoginPassword': kwargs['encoded_password']}


class GetHomeAddress(HNAPCommand):
    def __init__(self):
        super().__init__('GetHomeAddress')

    def build_payload_data(self, **kwargs):
        return ''


class GetHomeConnection(HNAPCommand):
    def __init__(self):
        super().__init__('GetHomeConnection')

    def build_payload_data(self, **kwargs):
        return ''


class GetMultipleCommands(HNAPCommand):
    def __init__(self, commands):
        super().__init__('GetMultipleHNAPs')
        self.commands = commands

    def build_payload_data(self, **kwargs):
        payload_data = {}
        for command in self.commands:
            payload_data[command.operation] = command.build_payload_data(**kwargs)
        return payload_data


class HNAPServer:
    def login(self, scheme, host, username, password):
        session = HNAPSession(host, scheme)

        # Ask server to encode credentials
        command = LoginRequest()
        resp = command.execute(session, username=username, password=password)
        login_response = command.validate_response(resp)

        cookie_id = login_response['Cookie']
        public_key = login_response['PublicKey']
        challenge = login_response['Challenge']

        session.authenticate(challenge.encode(), public_key.encode(), password.encode(), cookie_id)

        command = Login()
        resp = command.execute(session, username=username, encoded_password=session.encoded_password)
        command.validate_response(resp)

        return session

    def logout(self):
        raise NotImplemented

    def get_commands(self, session):
        raise NotImplemented

    def get_status(self, session):
        raise NotImplemented

    def do_command(self, session, command, **kwargs):
        return command.execute(session, **kwargs)


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scheme', default='http', help='URL scheme (Default: http)')
    parser.add_argument('--host', default='192.168.100.1', help='Hostname or IP of your modem (Default: 192.168.100.1)')
    parser.add_argument('--username', default='admin', help='Admin username (Default: admin)')
    parser.add_argument('--password', default='motorola', help='Admin password (Default: motorola)')

    return parser.parse_args()


if __name__ == '__main__':
    args = get_arguments()

    server = HNAPServer()
    hnap_session = server.login(args.scheme, args.host, args.username, args.password)

    server.do_command(hnap_session, GetHomeAddress())
    server.do_command(hnap_session, GetHomeConnection())
    server.do_command(hnap_session, GetMultipleCommands([GetHomeConnection(), GetHomeAddress()]))
