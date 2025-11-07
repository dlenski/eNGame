import sys
import requests
import json
import uuid
import random
from datetime import datetime

from websockets.sync.client import connect

from . import pairs
from .yq import YFQuoteResult, nav, navs

#import logging
#logging.basicConfig(level=logging.DEBUG)

sess = requests.session()
sess.headers.update({
    'User-Agent': (ua := 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
})

email, password, otp = sys.argv[1:4]

sess_uuid = uuid.uuid1()
devid = random.getrandbits(256).to_bytes(32).hex()
resp = sess.post(
    'https://api.production.wealthsimple.com/v1/oauth/v2/token',
    headers={'X-Wealthsimple-Client': '@wealthsimple/wealthsimple',
             'X-Ws-Profile': 'undefined',
             'X-Ws-Session-Id': str(sess_uuid),
             'X-Ws-Device-Id': devid,                              # "Real" device ID doesn't seem necessary
             'X-Wealthsimple-Otp': otp + ';remember=true',
    },
    json={
        "grant_type": "password",
        "username": email,
        "password": password,
        "skip_provision": True,
        "otp_claim": None,
        "scope": "invest.read invest.write trade.read trade.write tax.read tax.write",
        "client_id": "4da53ac2b03225bed1550eba8e4611e086c7b905a3855e6ed12ea08c246758fa",  # FIXED?
    }
)
assert resp.ok, resp.content
j = resp.json()
assert j['token_type'] == 'Bearer'
atoken, rtoken, exp = j['access_token'], j['refresh_token'], j['created_at'] + j['expires_in']

sess.headers.update(sess_info := {
    "authorization": 'Bearer ' + atoken,
    "x-ws-api-version": '12',
    "x-ws-locale": "en-CA",
    "x-ws-profile": "trade",
    "x-platform-os": "web",
    "x-ws-device-id": devid,  # "Real" device ID doesn't seem necessary
})

with connect(
    'wss://realtime-api.wealthsimple.com/subscription',
    subprotocols=('graphql-transport-ws',),
    origin='https://my.wealthsimple.com',
    user_agent_header=ua,
) as ws:
    init = {
        "type": "connection_init",
        "payload": sess_info,
    }
    ws.send(json.dumps(init))
    print(ws.recv())

    ws2sym = {}
    for p in pairs.ng_pairs:
        ws2sym[p.wssecid] = p.cad
        sub = {
            "id": p.wssecid.removeprefix('sec-s-'),  # Reuse WealthSimple security ID as query ID
            "type": "subscribe",
            "payload": {
                "variables": {"id": p.wssecid},
                "extensions": {},
                "operationName": "QuoteV2BySecurityIdStream",
                "query": "subscription QuoteV2BySecurityIdStream($id: ID!, $currency: Currency) {\n  securityQuoteUpdates(id: $id) {\n    id\n    quoteV2(currency: $currency) {\n      ...StreamedSecurityQuoteV2\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment StreamedSecurityQuoteV2 on UnifiedQuote {\n  __typename\n  securityId\n  ask\n  bid\n  currency\n  price\n  sessionPrice\n  quotedAsOf\n  ... on EquityQuote {\n    marketStatus\n    askSize\n    bidSize\n    close\n    high\n    last\n    lastSize\n    low\n    open\n    mid\n    volume\n    __typename\n  }\n  ... on OptionQuote {\n    marketStatus\n    askSize\n    bidSize\n    close\n    high\n    last\n    lastSize\n    low\n    open\n    mid\n    volume\n    breakEven\n    inTheMoney\n    liquidityStatus\n    openInterest\n    underlyingSpot\n    __typename\n  }\n}"
            }
        }
        ws.send(json.dumps(sub))

    for msg in ws:
        j = json.loads(msg)
        jq = j['payload']['data']['securityQuoteUpdates']['quoteV2']
        sym = ws2sym[jq['securityId']]
        ts = navs(jq, 'quotedAsOf', converter=datetime.fromisoformat)
        q = YFQuoteResult(
            symbol=sym,
            currency=navs(jq, 'currency'),
            timestamp=ts.timestamp(), tz=ts.tzinfo,
            bid_size=nav(jq, 'bidSize'),
            ask_size=nav(jq, 'askSize'),
            bid=navs(jq, 'bid', converter=float),
            ask=navs(jq, 'ask', converter=float),
            low=navs(jq, 'low', converter=float),
            high=navs(jq, 'high', converter=float),
            last_size=nav(jq, 'lastSize'),
            last_price=navs(jq, 'last', converter=float),
            change=None, change_percent=None,
            market_state=navs(jq, 'marketStatus'),
            volume=nav(jq, 'volume'),
        )

        print(q)
        print(f'{jq["currency"]} {sym} {jq["quotedAsOf"]} ({jq["marketStatus"]}) bid: {jq["bid"]} x {jq["bidSize"]}, ask: {jq["ask"]} x {jq["askSize"]}, last: {jq["last"]} x {jq["lastSize"]}, volume: {jq["volume"]}')
