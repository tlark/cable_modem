#!/usr/bin/env python3
import hmac
import time
import argparse
import requests
import json

# Disable warnings for ignoring SSL cert verification
import urllib3

urllib3.disable_warnings()


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
        return (privatekey, passkey)

    def generate_hnap_auth(self, operation):
        privkey = self.privatekey
        curtime = str(int(time.time() * 1000))
        auth_key = curtime + '"http://purenetworks.com/HNAP1/{}"'.format(operation)
        privkey = privkey.encode()
        auth = hmac.new(privkey, auth_key.encode(), digestmod='sha256')
        return auth.hexdigest().upper() + ' ' + curtime

    def _login_request(self, username):
        url = '{}://{}/HNAP1/'.format(self.scheme, self.host)
        headers = {'SOAPAction': '"http://purenetworks.com/HNAP1/Login"'}
        payload = '{"Login":{"Action":"request","Username":"' + username + '","LoginPassword":"","Captcha":"","PrivateLogin":"LoginPassword"}}'

        try:
            r = self.s.post(url, headers=headers, data=payload, stream=True, verify=False)

            return r
        except Exception as ex:
            print(ex)
            returnValue = {"requestStatus": "ERROR", "message": "Login failed."}
            print(json.dumps(returnValue))
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
            r = self.s.post(url, headers=headers, cookies=cookies, json=payload)

            return r
        except Exception as ex:
            print(ex)
            returnValue = {"requestStatus": "ERROR", "message": "Login failed."}
            print(json.dumps(returnValue))
            exit(-1)

    def login(self, username, password):
        self.username = username
        r = self._login_request(username)

        # Validate there was a response from the server
        try:
            lrdata = json.loads(r.text)

        except Exception as ex:
            print(ex)
            returnValue = {"requestStatus": "ERROR", "message": "Unable to parse modem response."}
            print(json.dumps(returnValue))
            exit(-1)

        if "LoginResponse" not in lrdata:
            returnValue = {"requestStatus": "ERROR", "message": "LoginResponse not in modem response."}
            print(json.dumps(returnValue))
            exit(-1)

        if "LoginResult" not in lrdata['LoginResponse']:
            returnValue = {"requestStatus": "ERROR", "message": "LoginResult not in modem LoginResponse object."}
            print(json.dumps(returnValue))
            exit(-1)

        # Validate the login response was successful
        print(lrdata)
        if lrdata['LoginResponse']['LoginResult'] != "OK":
            returnValue = {"requestStatus": "ERROR", "message": "Login failed."}
            print(json.dumps(returnValue))
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
            r = self.s.post(url, headers=headers, cookies=cookies, json=payload)

            jsonResponse = json.loads(r.text)
            print(jsonResponse)

            # Parse the results to a simplified object
            returnValue = {"requestStatus": "SUCCESS",
                           "data": {
                               "softwareVersion":
                                   jsonResponse['GetMultipleHNAPsResponse']['GetMotoStatusSoftwareResponse'][
                                       'StatusSoftwareSfVer'],
                               "macAddress": jsonResponse['GetMultipleHNAPsResponse']['GetMotoStatusSoftwareResponse'][
                                   'StatusSoftwareMac'],
                               "serialNumber":
                                   jsonResponse['GetMultipleHNAPsResponse']['GetMotoStatusSoftwareResponse'][
                                       'StatusSoftwareSerialNum'],
                               "operatorSoftwareVersion":
                                   jsonResponse['GetMultipleHNAPsResponse']['GetMotoStatusSoftwareResponse'][
                                       'StatusSoftwareCustomerVer'],
                               "wanStatus": jsonResponse['GetMultipleHNAPsResponse']['GetHomeConnectionResponse'][
                                   'MotoHomeOnline'],
                               "systemUptime":
                                   jsonResponse['GetMultipleHNAPsResponse']['GetMotoStatusConnectionInfoResponse'][
                                       'MotoConnSystemUpTime'],
                               "networkAccess":
                                   jsonResponse['GetMultipleHNAPsResponse']['GetMotoStatusConnectionInfoResponse'][
                                       'MotoConnNetworkAccess'],
                           }}

            print(json.dumps(returnValue))

        except Exception as ex:
            print(ex)
            returnValue = {"requestStatus": "ERROR", "message": "Failed to retrieve status."}
            print(json.dumps(returnValue))
            exit(-1)

    def get_capabilities(self):
        url = '{}://{}/HNAP1/'.format(self.scheme, self.host)
        auth = self.generate_hnap_auth('')
        headers = {'HNAP_AUTH': auth}

        cookies = {'uid': '{}'.format(self.cookie_id),
                   'PrivateKey': '{}'.format(self.privatekey)}

        try:
            r = self.s.get(url, headers=headers, cookies=cookies)
            print(r)
            returnValue = {"requestStatus": "SUCCESS"}
            print(json.dumps(returnValue))

        except Exception as ex:
            print(ex)
            returnValue = {"requestStatus": "ERROR", "message": "Get capabilities FAILED."}
            print(json.dumps(returnValue))
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
            r = self.s.post(url, headers=headers, cookies=cookies, json=payload)
            returnValue = {"requestStatus": "SUCCESS"}
            print(json.dumps(returnValue))

        except Exception as ex:
            print(ex)
            returnValue = {"requestStatus": "ERROR", "message": "Reboot failed."}
            print(json.dumps(returnValue))
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
    h.get_capabilities()
    if args.reboot:
        r = h.reboot()
