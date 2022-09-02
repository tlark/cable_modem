import hmac
import json
import logging
import time
from logging.config import fileConfig

import requests
# Disable warnings for ignoring SSL cert verification
import urllib3
from requests import Response

from models import ConnectionSummary, ConnectionDetails, DeviceInfo

urllib3.disable_warnings()

logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)
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

    def authenticate_operation(self, operation) -> str:
        now = str(int(time.time() * 1000))
        auth_key = '{}"http://purenetworks.com/HNAP1/{}"'.format(now, operation)
        key = (self.private_key or 'withoutloginkey').encode()
        auth = hmac.new(key, auth_key.encode(), digestmod=self.digestmod)
        return '{} {}'.format(auth.hexdigest().upper(), now)

    def get_cookies(self) -> dict:
        return {'uid': '{}'.format(self.cookie_id),
                'PrivateKey': '{}'.format(self.private_key)}


class HNAPCommand:
    def __init__(self, operation, payload_default='', read_only=True, method='POST'):
        self.operation = operation
        self.payload_default = payload_default
        self.read_only = read_only
        self.method = method

    def __str__(self):
        return '{} ({} operation={})'.format(self.__class__.__name__, self.method, self.operation)

    def build_payload_data(self, **kwargs) -> str:
        return self.payload_default

    def execute(self, session: HNAPSession, **kwargs) -> dict:
        url = '{}://{}/HNAP1/'.format(session.scheme, session.host)
        auth = session.authenticate_operation(self.operation)
        headers = {'HNAP_AUTH': auth, 'SOAPAction': '"http://purenetworks.com/HNAP1/{}"'.format(self.operation)}
        cookies = session.get_cookies()
        body = {self.operation: self.build_payload_data(**kwargs)}

        logger.debug(">>>> {}: url={}, headers={}, cookies={}, body={}".format(self, url, headers, cookies, body))
        resp = session.http_session.request(self.method, url, headers=headers, cookies=cookies, json=body, verify=False, timeout=(3.0, 10.0))
        logger.debug("<<<< {}: url={}, code={}, body={}".format(self, url, resp.status_code, resp.text))
        return self.validate_response(resp)

    def validate_response(self, response: Response) -> dict:
        if not response.ok:
            raise ValueError('{}: Invalid response; code={}, body={}'.format(self, response.status_code, response.text))
        body = json.loads(response.text)
        return self.validate_response_body(body)

    def validate_response_body(self, body: dict) -> dict:
        # Each operation response has the same pattern (e.g. Login operation has LoginResponse key)
        operation_response_key = '{}Response'.format(self.operation)
        operation_response = body.get(operation_response_key)
        if not operation_response:
            raise ValueError('Missing {} in {}'.format(operation_response_key, body))

        # Each operation response has a result code where the key is the same pattern
        # (e.g. Login result code key is LoginResult)
        operation_result_key = '{}Result'.format(self.operation)
        operation_result = operation_response.get(operation_result_key)
        if operation_result != 'OK':
            raise ValueError('Invalid {}={}'.format(operation_result_key, operation_result))

        return operation_response


class LoginRequest(HNAPCommand):
    def __init__(self):
        super().__init__('Login')

    def build_payload_data(self, **kwargs) -> dict:
        return {'Action': 'request',
                'Captcha': '',
                'PrivateLogin': 'LoginPassword',
                'Username': kwargs['username'],
                'LoginPassword': ''}


class Login(LoginRequest):
    def build_payload_data(self, **kwargs) -> dict:
        return {'Action': 'login',
                'Captcha': '',
                'PrivateLogin': 'LoginPassword',
                'Username': kwargs['username'],
                'LoginPassword': kwargs['encoded_password']}


class Logout(HNAPCommand):
    def __init__(self):
        super().__init__('Logout')

    def build_payload_data(self, **kwargs) -> dict:
        return {'Action': 'logout',
                'Captcha': '',
                'Username': kwargs.get('username', 'admin')}


class GetMultipleCommands(HNAPCommand):
    def __init__(self, commands: list):
        super().__init__('GetMultipleHNAPs')
        self.commands = commands

    def build_payload_data(self, **kwargs) -> dict:
        payload_data = {}
        for command in self.commands:
            payload_data[command.operation] = command.build_payload_data(**kwargs)
        return payload_data

    def validate_response(self, response) -> dict:
        multiple_commands_response = super().validate_response(response)
        for command in self.commands:
            command.validate_response_body(multiple_commands_response)
        return multiple_commands_response


class HNAPSystem:
    def login(self, scheme, host, username, password) -> HNAPSession:
        session = HNAPSession(host, scheme)

        # Ask server to encode credentials
        command = LoginRequest()
        login_response = command.execute(session, username=username, password=password)

        cookie_id = login_response['Cookie']
        public_key = login_response['PublicKey']
        challenge = login_response['Challenge']

        session.authenticate(challenge.encode(), public_key.encode(), password.encode(), cookie_id)

        command = Login()
        command.execute(session, username=username, encoded_password=session.encoded_password)

        return session

    def logout(self, session: HNAPSession, username) -> dict:
        return self.do_command(session, Logout(), username=username)

    def get_commands(self, session: HNAPSession) -> list:
        raise NotImplemented

    def get_device_info(self, session: HNAPSession) -> DeviceInfo:
        raise NotImplemented

    def get_connection_summary(self, session: HNAPSession) -> ConnectionSummary:
        raise NotImplemented

    def get_connection_details(self, session: HNAPSession) -> ConnectionDetails:
        raise NotImplemented

    def get_events(self, session: HNAPSession) -> list:
        raise NotImplemented

    def reboot(self, session: HNAPSession):
        raise NotImplemented

    def do_command(self, session: HNAPSession, command: HNAPCommand, **kwargs) -> dict:
        return command.execute(session, **kwargs)
