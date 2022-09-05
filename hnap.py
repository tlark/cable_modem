import hmac
import json
import logging
import time
from datetime import datetime, timedelta

import requests
# Disable warnings for ignoring SSL cert verification
import urllib3
from requests import Response

from models import ConnectionSummary, ConnectionDetails, DeviceInfo

urllib3.disable_warnings()

logger = logging.getLogger(__name__)


class HNAPSession:
    def __init__(self, host, scheme, username, password):
        self.scheme = scheme
        self.host = host
        self.username = username
        self.password = password

        self.http_session = requests.Session()
        self.private_key = None
        self.cookie_id = None
        self.digestmod = 'md5'
        self.encoded_password = None
        self.request_ts = None
        self.max_inactive = timedelta(seconds=600)

    def __str__(self):
        return '{} for {} on {}://{}/, valid={}'.format(self.__class__.__name__, self.username, self.scheme, self.host,
                                                        self.is_valid())

    def authenticate(self, challenge, public_key, password, cookie_id):
        self.private_key = hmac.new(public_key + password, challenge, digestmod=self.digestmod).hexdigest().upper()
        self.encoded_password = hmac.new(self.private_key.encode(), challenge,
                                         digestmod=self.digestmod).hexdigest().upper()
        self.cookie_id = cookie_id

    def authenticate_operation(self, operation: str) -> str:
        now = str(int(time.time() * 1000))
        auth_key = '{}"http://purenetworks.com/HNAP1/{}"'.format(now, operation)
        key = (self.private_key or 'withoutloginkey').encode()
        auth = hmac.new(key, auth_key.encode(), digestmod=self.digestmod)
        return '{} {}'.format(auth.hexdigest().upper(), now)

    def get_cookies(self) -> dict:
        return {'uid': '{}'.format(self.cookie_id),
                'PrivateKey': '{}'.format(self.private_key)}

    def do_request(self, method: str, url: str, **kwargs) -> Response:
        self.request_ts = datetime.now()
        return self.http_session.request(method, url, **kwargs)

    def invalidate(self):
        logger.warning('Invalidating {}'.format(self))
        self.http_session = requests.Session()
        self.private_key = None
        self.cookie_id = None
        self.encoded_password = None
        self.request_ts = None

    def is_expired(self):
        return self.request_ts and (datetime.now() - self.request_ts) > self.max_inactive

    def is_valid(self):
        return self.private_key and self.cookie_id and self.encoded_password and not self.is_expired()


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
        resp = session.do_request(self.method, url, headers=headers, cookies=cookies, json=body, verify=False,
                                  timeout=(3.0, 10.0))
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


class HNAPDevice:
    def __init__(self, device_id):
        self.device_id = device_id
        self.session = None
        self.model = None
        self.serial_number = None
        self.mac_address = None

    def __str__(self):
        return '{}(id={}, model={}, serial_number={}, mac_address={})'.format(self.__class__.__name__,
                                                                              self.device_id, self.model,
                                                                              self.serial_number,
                                                                              self.mac_address)

    def login(self, scheme, host, username, password) -> HNAPSession:
        logger.debug('Attempting login for {} on {}://{}'.format(username, scheme, host))
        self.session = HNAPSession(host, scheme, username, password)

        # Ask server to encode credentials
        command = LoginRequest()
        login_response = command.execute(self.session, username=username, password=password)

        cookie_id = login_response['Cookie']
        public_key = login_response['PublicKey']
        challenge = login_response['Challenge']

        self.session.authenticate(challenge.encode(), public_key.encode(), password.encode(), cookie_id)

        command = Login()
        command.execute(self.session, username=username, encoded_password=self.session.encoded_password)

        logger.info('Completed login; {}'.format(self.session))
        return self.session

    def logout(self) -> dict:
        if not self.session:
            return {}
        logger.debug('Attempting logout; {}'.format(self.session))
        resp = self.do_command(Logout(), username=self.session.username)
        self.session.invalidate()
        logger.info('Completed logout; {}'.format(self.session))
        return resp

    def get_commands(self) -> list:
        raise NotImplemented

    def get_device_info(self) -> DeviceInfo:
        raise NotImplemented

    def get_connection_summary(self) -> ConnectionSummary:
        raise NotImplemented

    def get_connection_details(self) -> ConnectionDetails:
        raise NotImplemented

    def get_events(self) -> list:
        raise NotImplemented

    def reboot(self):
        raise NotImplemented

    def ping(self):
        self.do_command(HNAPCommand('GetHomeConnection'))

    def do_command(self, command: HNAPCommand, **kwargs) -> dict:
        if not self.is_session_valid():
            self.refresh_session()
        return command.execute(self.session, **kwargs)

    def is_session_valid(self) -> bool:
        if not self.session:
            logger.debug('No session active')
            return False
        if not self.session.is_valid():
            logger.debug('Invalid session={}'.format(self.session))
            return False
        return True

    def refresh_session(self):
        logger.info('Refreshing {}'.format(self.session))
        self.login(self.session.scheme, self.session.host, self.session.username, self.session.password)

    def invalidate_session(self):
        self.session.invalidate()

    def to_timestamp(self, date: str, time: str):
        raise NotImplemented
