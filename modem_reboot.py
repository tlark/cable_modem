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


class SurfboardHNAP:

    def __init__(self, scheme='http', host='192.168.100.1'):
        self.s = requests.Session()
        self.privatekey = None
        self.cookie_id = None
        self.host = host
        self.scheme = scheme

    def generate_keys(self, challenge, pubkey, password):
        privatekey = hmac.new(pubkey + password, challenge, digestmod='sha256').hexdigest().upper()
        passkey = hmac.new(privatekey.encode(), challenge, digestmod='sha256').hexdigest().upper()
        self.privatekey = privatekey
        return privatekey, passkey

    def generate_hnap_auth(self, operation):
        privkey = self.privatekey or 'withoutloginkey'
        curtime = str(int(time.time() * 1000))
        auth_key = curtime + '"http://purenetworks.com/HNAP1/{}"'.format(operation)
        privkey = privkey.encode()
        auth = hmac.new(privkey, auth_key.encode(), digestmod='sha256')
        return auth.hexdigest().upper() + ' ' + curtime

    def _login_request(self, username):
        url = '{}://{}/HNAP1/'.format(self.scheme, self.host)
        auth = self.generate_hnap_auth('Login')
        headers = {'HNAP_AUTH': auth, 'SOAPAction': '"http://purenetworks.com/HNAP1/Login"'}
        payload = '{"Login":{"Action":"request","Username":"' + username + '","LoginPassword":"","Captcha":"","PrivateLogin":"LoginPassword"}}'

        try:
            logger.debug("_login_request POST: headers={}, payload={}".format(headers, payload))
            r = self.s.post(url, headers=headers, data=payload, stream=True, verify=False)
            logger.debug("_login_request POST response: code={}, body={}".format(r.status_code, json.loads(r.text)))
            return r
        except Exception as ex:
            logger.exception(ex)
            print(json.dumps({"requestStatus": "ERROR", "message": "Login failed.", "details": ex}))
            exit(-1)

    def _login_real(self, username, cookie_id, privatekey, passkey):
        url = '{}://{}/HNAP1/'.format(self.scheme, self.host)
        auth = self.generate_hnap_auth('Login')
        headers = {'HNAP_AUTH': auth, 'SOAPAction': '"http://purenetworks.com/HNAP1/Login"'}
        cookies = {'uid': '{}'.format(cookie_id),
                   'PrivateKey': '{}'.format(privatekey)}
        payload = {'Login': {'Action': 'login',
                             'Captcha': '',
                             'LoginPassword': '{}'.format(passkey),
                             'PrivateLogin': 'LoginPassword',
                             'Username': '{}'.format(username)}}

        try:
            logger.debug("_login_real POST: headers={}, cookies={}, payload={}".format(headers, cookies, payload))
            r = self.s.post(url, headers=headers, cookies=cookies, json=payload, verify=False)
            logger.debug("_login_real POST response: code={}, body={}".format(r.status_code, json.loads(r.text)))
            return r
        except Exception as ex:
            logger.exception(ex)
            print(json.dumps({"requestStatus": "ERROR", "message": "Login failed.", "details": ex}))
            exit(-1)

    def login(self, username, password):
        r = self._login_request(username)

        # Validate there was a response from the server
        lrdata = None
        try:
            lrdata = json.loads(r.text)
        except Exception as ex:
            logger.exception(ex)
            print(json.dumps({"requestStatus": "ERROR", "message": "Unable to parse modem response.", "details": ex}))
            exit(-1)

        if "LoginResponse" not in lrdata:
            msg = {"requestStatus": "ERROR", "message": "LoginResponse not in modem response.", "details": lrdata}
            print(json.dumps(msg))
            exit(-1)

        if "LoginResult" not in lrdata['LoginResponse']:
            msg = {"requestStatus": "ERROR", "message": "LoginResult not in modem LoginResponse object.",
                   "details": lrdata['LoginResponse']}
            print(json.dumps(msg))
            exit(-1)

        # Validate the login response was successful
        if lrdata['LoginResponse']['LoginResult'] != "OK":
            msg = {"requestStatus": "ERROR", "message": "Login failed.",
                   "details": lrdata['LoginResponse']['LoginResult']}
            print(json.dumps(msg))
            exit(-1)

        cookie_id = lrdata['LoginResponse']['Cookie']
        pubkey = lrdata['LoginResponse']['PublicKey']
        challenge = lrdata['LoginResponse']['Challenge']

        self.cookie_id = cookie_id

        privkey, passkey = self.generate_keys(challenge.encode(),
                                              pubkey.encode(),
                                              password.encode())
        return self._login_real(username, cookie_id, privkey, passkey)

    def get_status(self):
        url = '{}://{}/HNAP1/'.format(self.scheme, self.host)
        auth = self.generate_hnap_auth('GetMultipleHNAPs')
        headers = {'HNAP_AUTH': auth, 'SOAPACTION': '"http://purenetworks.com/HNAP1/GetMultipleHNAPs"'}

        cookies = {'uid': '{}'.format(self.cookie_id),
                   'PrivateKey': '{}'.format(self.privatekey)}

        payload = {'GetMultipleHNAPs': {'GetMotoStatusSoftware': '', 'GetHomeConnection': '',
                                        'GetMotoStatusConnectionInfo': ''}}

        try:
            logger.debug("get_status POST: headers={}, cookies={}, payload={}".format(headers, cookies, payload))
            r = self.s.post(url, headers=headers, cookies=cookies, json=payload, verify=False)
            logger.debug("get_status POST response: status={}, body={}".format(r.status_code, json.loads(r.text)))

            json_response = json.loads(r.text)

            # Parse the results to a simplified object
            msg = {"requestStatus": "SUCCESS",
                   "data": {
                       "softwareVersion":
                           json_response['GetMultipleHNAPsResponse']['GetMotoStatusSoftwareResponse'][
                               'StatusSoftwareSfVer'],
                       "macAddress": json_response['GetMultipleHNAPsResponse']['GetMotoStatusSoftwareResponse'][
                           'StatusSoftwareMac'],
                       "serialNumber":
                           json_response['GetMultipleHNAPsResponse']['GetMotoStatusSoftwareResponse'][
                               'StatusSoftwareSerialNum'],
                       "operatorSoftwareVersion":
                           json_response['GetMultipleHNAPsResponse']['GetMotoStatusSoftwareResponse'][
                               'StatusSoftwareCustomerVer'],
                       "wanStatus": json_response['GetMultipleHNAPsResponse']['GetHomeConnectionResponse'][
                           'MotoHomeOnline'],
                       "systemUptime":
                           json_response['GetMultipleHNAPsResponse']['GetMotoStatusConnectionInfoResponse'][
                               'MotoConnSystemUpTime'],
                       "networkAccess":
                           json_response['GetMultipleHNAPsResponse']['GetMotoStatusConnectionInfoResponse'][
                               'MotoConnNetworkAccess'],
                   }}

            print(json.dumps(msg))

        except Exception as ex:
            logger.exception(ex)
            print(json.dumps({"requestStatus": "ERROR", "message": "Get status FAILED.", "details": ex}))
            exit(-1)

    def get_capabilities(self):
        url = '{}://{}/HNAP1/'.format(self.scheme, self.host)
        auth = self.generate_hnap_auth('')
        headers = {'HNAP_AUTH': auth}

        cookies = {'uid': '{}'.format(self.cookie_id),
                   'PrivateKey': '{}'.format(self.privatekey)}

        try:
            logger.debug("get_capabilities GET: headers={}, cookies={}".format(headers, cookies))
            r = self.s.get(url, headers=headers, cookies=cookies, verify=False)
            logger.debug("get_capabilities GET response: {}".format(r))
            msg = {"requestStatus": "SUCCESS", "details": r.text}
            print(json.dumps(msg))

        except Exception as ex:
            logger.exception(ex)
            print(json.dumps({"requestStatus": "ERROR", "message": "Get capabilities FAILED.", "details": ex}))
            exit(-1)

    def reboot(self):
        url = '{}://{}/HNAP1/'.format(self.scheme, self.host)
        auth = self.generate_hnap_auth('SetStatusSecuritySettings')
        headers = {'HNAP_AUTH': auth, 'SOAPAction': '"http://purenetworks.com/HNAP1/SetStatusSecuritySettings"'}

        cookies = {'uid': '{}'.format(self.cookie_id),
                   'PrivateKey': '{}'.format(self.privatekey)}
        payload = {'SetStatusSecuritySettings': {'MotoStatusSecurityAction': '1',
                                                 'MotoStatusSecXXX': 'XXX'}}

        try:
            logger.debug("reboot POST: headers={}, cookies={}, payload={}".format(headers, cookies, payload))
            r = self.s.post(url, headers=headers, cookies=cookies, json=payload, verify=False)
            logger.debug("reboot POST response: {}".format(r))
            msg = {"requestStatus": "SUCCESS", "details": r.text}
            print(json.dumps(msg))

        except Exception as ex:
            logger.exception(ex)
            print(json.dumps({"requestStatus": "ERROR", "message": "Reboot FAILED.", "details": ex}))
            exit(-1)


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scheme', default='http', help='URL scheme (Default: http)')
    parser.add_argument('--host', default='192.168.100.1', help='Hostname or IP of your modem (Default: 192.168.100.1)')
    parser.add_argument('--username', default='admin', help='Admin username (Default: admin)')
    parser.add_argument('--password', default='motorola', help='Admin password (Default: motorola)')
    parser.add_argument('--reboot', action='store_true', help="Reboots the modem")
    parser.add_argument('--capabilities', action='store_true', help="Prints SOAPActions supported")

    return parser.parse_args()


if __name__ == '__main__':
    args = get_arguments()
    scheme = args.scheme
    host = args.host
    username = args.username
    password = args.password

    h = SurfboardHNAP(scheme, host)
    h.login(username, password)
    h.get_status()

    if args.capabilities:
        h.get_capabilities()
    if args.reboot:
        h.reboot()
