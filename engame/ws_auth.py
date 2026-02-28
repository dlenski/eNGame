import configparser
import getpass
import logging
import os
import random
from time import time
from typing import Optional
from collections import namedtuple
from uuid import uuid1
import requests

logger = logging.getLogger(__name__)

CONFIG_FILE = '~/.config/wealthsimple'
BASE_URL = 'https://api.production.wealthsimple.com/v1/oauth/v2/token'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
CLIENT_ID = '4da53ac2b03225bed1550eba8e4611e086c7b905a3855e6ed12ea08c246758fa'   # Is this fixed?
SCOPE = 'invest.read invest.write trade.read trade.write tax.read tax.write'     # FIXME: Allow specifying this

WSLogin = namedtuple('WSLogin', 'user access_token refresh_token device_id access_token_expires')

def _new_ws_session(devid=None, sess_uuid=None):
    if devid is None:
        # This field needs to be persisted, otherwise user gets "new device"
        # warning and has to enter OTP every time.
        devid = random.getrandbits(256).to_bytes(32).hex()
    if sess_uuid is None:
        sess_uuid = str(uuid1())

    sess = requests.Session()
    sess.headers.update({
        'User-Agent': USER_AGENT,
        'X-Wealthsimple-Client': '@wealthsimple/wealthsimple',
        'X-Ws-Profile': 'trade',  # also 'invest', 'tax'
        'X-Ws-Api-Version': '12',
        'X-Ws-Session-Id': sess_uuid,
        'X-Ws-Device-Id': devid,
    })
    return sess


def authenticate(
    user: Optional[str] = None,
    cf: Optional[str] = CONFIG_FILE,
    sess: Optional[requests.Session] = None,
    writeback: bool = True,
    force_refresh: bool = True,
):
    if sess is None:
        sess = _new_ws_session()

    if cf:
        try:
            return load_credentials(user, cf, sess, writeback, force_refresh)
        except NotImplementedError as exc:
            print(f'Could not load WealthSimple login credentials{"" if user is None else " for user " + repr(user)}: {exc.args[0]}')

    user_ = password = otp = None
    while True:
        try:
            if otp is None:
                user_ = input('Username: ') if user is None else user
                password = getpass.getpass('Password: ')
                return login(user_, password, sess, cf=(cf if writeback else None))
            else:
                # redo with OTP
                return login(user_, password, sess, otp, cf=(cf if writeback else None))
        except PermissionError:
            print('Incorrect username or password')
            otp = None
        except BlockingIOError: # "EAGAIN"
            if otp is not None:
                print('Incorrect OTP entered')
            otp = input('One-time password: ')


def load_credentials(
    user: Optional[str] = None,
    cf: str = CONFIG_FILE,
    sess: Optional[requests.Session] = None,
    writeback: bool = True,
    force_refresh: bool = False,
):
    if sess is None:
        sess = _new_ws_session()

    config = configparser.ConfigParser()
    cf = os.path.expanduser(cf)
    try:
        config.read(cf)
    except configparser.Error as exc:
        raise NotImplementedError(f"Could not read config file {cf!r}") from exc

    if user is None:
        section = next((s for s in config.sections() if s.startswith('ws:')), None)
        if section is None:
            raise NotImplementedError(f'Did not find any section named "ws:USERNAME" in config file {cf!r}')
        user = section.removeprefix('ws:')
        logger.debug(f'Using credentials from section {section!r} of config file {cf!r}')
    else:
        section = f'ws:{user}'

    access_token = config.get(section, 'access_token', fallback=None)
    refresh_token = config.get(section, 'refresh_token', fallback=None)
    device_id = sess.headers['x-ws-device-id'] = config.get(section, 'device_id', fallback=None)
    exp = config.get(section, 'access_token_expires', fallback=None)
    if not (access_token or refresh_token):
        raise NotImplementedError(f'Did not find access_token and/or refresh_token in section {section!r} of config file {cf!r}')
    if exp is not None:
        exp = int(exp)

    for refreshing in (False, True):
        if refreshing or not force_refresh:
            r = sess.get(f'{BASE_URL}/info', headers={'authorization': f'Bearer {access_token}'})
            if r.ok:
                break
        if not refreshing:
            r = sess.post(BASE_URL, json={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": CLIENT_ID,  # FIXED?
                }, headers={'authorization': f'Bearer {access_token}'})
            if r.ok:            
                j = r.json()
                assert j['token_type'] == 'Bearer'
                u = WSLogin(user, j['access_token'], j['refresh_token'], r.request.headers.get('x-ws-device-id'), int(j['created_at']) + int(j['expires_in']))

    if r.ok:
        j = r.json()
        assert j.get('email') == user, f"Expected user {user!r} but token is for user {j.get('email')!r}"        
        if refreshing:
            if writeback:
                write_credentials(cf, u)
            logger.debug(f'Successfully refreshed access_token for user {user}')
        else:
            u = WSLogin(user, access_token, refresh_token, device_id, exp)
            logger.debug(f'Using unexpired acces_token for user {user}')
    else:
        assert refreshing
        if r.status_code == 401:
            raise NotImplementedError('New login needed because refresh_token has expired')
        elif not r.ok:
            raise NotImplementedError('Token refresh failed for unknown reasons (FIXME)') from requests.HTTPError(response=r)

    return u


def login(user: str, password: str, sess: Optional[requests.Session] = None, otp: Optional[str] = None, cf: Optional[str] = None):
    if sess is None:
        sess = _new_ws_session()

    r = sess.post(BASE_URL, json={
            "grant_type": "password",
            "username": user,
            "password": password,
            "skip_provision": True,
            "otp_claim": None,
            "scope": SCOPE,
            "client_id": CLIENT_ID,
        })
    if r.status_code == 401 and r.headers.get('x-wealthsimple-otp-required') == 'true':
        details = r.headers.get('x-wealthsimple-otp')
        logging.debug(f'Need to retry login with OTP: {details!r}')
        if otp is None:
            raise BlockingIOError('OTP required, but not specified')
        else:
            r.request.headers['X-Wealthsimple-Otp'] = otp + ';remember=true'
            r = sess.send(r.request)
    if not r.ok:
        if r.headers.get('x-wealthsimple-otp') == 'invalid':
            raise BlockingIOError('Invalid OTP specified')
        raise PermissionError(f'Login failed at {"OTP" if "x-wealthsimple-otp" in r.request.headers else "username/password"} step') from requests.HTTPError(response=r)

    j = r.json()
    assert j['token_type'] == 'Bearer'
    u = WSLogin(user, j['access_token'], j['refresh_token'], r.request.headers.get('x-ws-device-id'), int(j['created_at']) + int(j['expires_in']))
    if cf:
        write_credentials(cf, u)
    logger.debug(f'Successfully authenticated as user {user!r}')
    return u


def write_credentials(cf: str, u: WSLogin):
    config = configparser.ConfigParser()
    cf = os.path.expanduser(cf)
    try:
        config.read(cf)
    except configparser.Error as exc:
        logger.warning('Discarding unparseable contents of {cf!r}: {exc}')

    with open(cf, 'w') as cf:
        section = f'ws:{u.user}'
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, 'access_token', u.access_token)
        config.set(section, 'refresh_token', u.refresh_token)
        config.set(section, 'device_id', u.device_id)
        config.set(section, 'access_token_expires', str(u.access_token_expires))
        config.write(cf)
    logger.info(f'Successfully wrote credentials for user {u.user!r} to {cf.name!r}')


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-v', '--verbose', action='count')
    x = p.add_mutually_exclusive_group()
    x.add_argument('-f', '--config-file', default=CONFIG_FILE, help='Config file to load/save credentials')
    x.add_argument('--no-config', dest='config_file', action='store_const', const=None)
    p.add_argument('-u', '--user', help='User to authenticate')
    p.add_argument('-R', '--force-refresh', action='store_true')
    args = p.parse_args()

    logging.basicConfig(level={0: 'WARNING', 1: 'INFO'}.get(args.verbose, 'DEBUG'))
    authenticate(user=args.user, cf=args.config_file, force_refresh=args.force_refresh)


if __name__ == '__main__':
    main()