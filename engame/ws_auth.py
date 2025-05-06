import configparser
import getpass
import logging
import os
from time import time
from typing import Optional
from collections import namedtuple
import requests

logger = logging.getLogger(__name__)

CONFIG_FILE = '~/.config/wealthsimple'
BASE_URL = 'https://trade-service.wealthsimple.com'

WSLogin = namedtuple('WSLogin', 'user access_token refresh_token device_id access_token_expires')

def authenticate(
    user: Optional[str] = None,
    cf: str = CONFIG_FILE,
    sess: Optional[requests.Session] = None,
    writeback: bool = True,
):
    if sess is None:
        sess = requests.Session()

    try:
        return load_credentials(user, cf, sess, writeback)
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
                otp = input('One-time password: ')


def load_credentials(
    user: Optional[str] = None,
    cf: str = CONFIG_FILE,
    sess: Optional[requests.Session] = None,
    writeback: bool = True
):
    if sess is None:
        sess = requests.Session()

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
    if not (access_token and refresh_token):
        raise NotImplementedError(f'Did not find access_token and refresh_token in section {section!r} of config file {cf!r}')
    if exp is not None:
        exp = int(exp)

    r = sess.get(f'{BASE_URL}/me', headers={'authorization': f'Bearer {access_token}'})
    if not r.ok:
        r = sess.post(f'{BASE_URL}/token', {'refresh_token': refresh_token}, headers={'authorization': f'Bearer {access_token}'})
        if r.status_code == 401:
            raise NotImplementedError('New login needed because refresh_token has expired')
        elif not r.ok:
            # It used to exist and work! https://github.com/MarkGalloway/wealthsimple-trade/blob/master/API.md#request-2
            raise NotImplementedError('New login needed because refresh endpoint is dead/broken/changed (FIXME)')
        logger.debug(f'Successfully refreshed access_token for user {"FIXME"}')
        u = WSLogin(user, r.headers['x-access-token'], r.headers['x-refresh-token'], r.headers['x-ws-device-id'], int(r.headers['x-access-token-expires']))
        if writeback:
            write_credentials(cf, u)
    else:
        j = r.json()
        assert j.get('email') == user, f"Expected user {user!r} but token is for user {j.get('email')!r}"
        logger.debug(f'Using unexpired access_token for user {user!r}')
        u = WSLogin(user, access_token, refresh_token, device_id, exp)

    return u


def login(user: str, password: str, sess: Optional[requests.Session] = None, otp: Optional[str] = None, cf: Optional[str] = None):
    if sess is None:
        sess = requests.Session()

    r = sess.post(f'{BASE_URL}/auth/login', {'email': user, 'password': password, 'otp': otp})
    if r.status_code == 401 and r.headers.get('x-wealthsimple-otp-required') == 'true':
        details = r.headers.get('x-wealthsimple-otp')
        logging.debug(f'Need to retry login with OTP: {details!r}')
        raise BlockingIOError()
    elif not r.ok:
        raise PermissionError()

    u = WSLogin(user, r.headers['x-access-token'], r.headers['x-refresh-token'], r.headers['x-ws-device-id'], int(r.headers['x-access-token-expires']))
    logger.debug('Successfully authenticated as user {user!r}')
    if cf:
        write_credentials(cf, u)
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
