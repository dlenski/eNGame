import sys
import requests
import json
import uuid
from datetime import datetime

from websockets.sync.client import connect

from . import pairs
from .yq import YFQuoteResult, nav

#import logging
#logging.basicConfig(level=logging.DEBUG)

sess = requests.session()
sess.headers['user-agent'] = ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'


email, password, otp = sys.argv[1:4]

# This old API still works
# https://github.com/seansullivan44/Wealthsimple-Trade-Python/blob/0b6370efb7632dd106603edcafe060d213e8f31c/src/wealthsimple/wealthsimple.py#L68-L122
resp = sess.post('https://trade-service.wealthsimple.com/auth/login', dict(email=email, password=password, otp=otp))
assert resp.ok, resp.content
devid, atoken, rtoken, exp = resp.headers['x-ws-device-id'], resp.headers['x-access-token'], resp.headers['x-refresh-token'], resp.headers['x-access-token-expires']
sess.headers['authorization'] = auth = 'Bearer ' + atoken

# Fetch wealthsimple exchange rate:
#curl 'https://my.wealthsimple.com/graphql' \
#  -H 'authorization: Bearer '+jwt \
#  -H 'content-type: application/json' \
#  -H 'user-agent: '+ua \
#  -H 'x-platform-os: web' \
#  -H 'x-ws-api-version: 12' \
#  -H 'x-ws-device-id: '+devid \
#  -H 'x-ws-locale: en-CA' \
#  -H 'x-ws-profile: trade' \
#  --data-raw $'{"operationName":"FetchLatestExchangeRate","variables":{"baseCurrency":"USD","quoteCurrency":"CAD"},"query":"query FetchLatestExchangeRate($baseCurrency: ForexCurrency\u0021, $quoteCurrency: ForexCurrency\u0021) {\\n  latestRate(baseCurrency: $baseCurrency, quoteCurrency: $quoteCurrency) {\\n    ...LatestExchangeRate\\n    __typename\\n  }\\n}\\n\\nfragment LatestExchangeRate on ExchangeRate {\\n  mid\\n  bid\\n  ask\\n  __typename\\n}"}'

# Fetch wealthsimple security IDs:
#curl 'https://my.wealthsimple.com/graphql' \
#  -H 'authorization: Bearer '+jwt
#  -H 'content-type: application/json' \
#  -A ua
#  -H 'x-platform-os: web' \
#  -H 'x-ws-api-version: 12' \
#  -H 'x-ws-device-id: '+devid \
#  -H 'x-ws-locale: en-CA' \
#  -H 'x-ws-profile: trade' \
#  --data-raw $'{"operationName":"FetchSecuritySearchResult","variables":{"query":"enbri"},"query":"query FetchSecuritySearchResult($query: String\u0021) {\\n  securitySearch(input: {query: $query}) {\\n    results {\\n      ...SecuritySearchResult\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment SecuritySearchResult on Security {\\n  id\\n  buyable\\n  status\\n  stock {\\n    symbol\\n    name\\n    primaryExchange\\n    __typename\\n  }\\n  features\\n  quoteV2 {\\n    securityId\\n    currency\\n    ... on EquityQuote {\\n      marketStatus\\n      __typename\\n    }\\n    __typename\\n  }\\n  __typename\\n}"}'

# This one does too
resp = sess.get('https://trade-service.wealthsimple.com/securities?query=hxs')
import pprint
pprint.pprint(resp.json())

with connect(
    'wss://realtime-api.wealthsimple.com/subscription',
    subprotocols=('graphql-transport-ws',),
    origin='https://my.wealthsimple.com',
    user_agent_header=ua,
) as ws:
    init = {
        "type": "connection_init",
        "payload": {
            "Authorization": auth,
            "x-ws-api-version": 12,
            "x-ws-locale": "en-CA",
            "x-ws-profile": "trade",
            "x-platform-os": "web",
            "x-ws-device-id": devid,  # "Real" device ID doesn't seem necessary
        }
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
        print('*****', msg)
        jq = j['payload']['data']['securityQuoteUpdates']['quoteV2']
        sym = ws2sym[jq['securityId']]
        ts = nav(jq, 'quotedAsOf', types_ok=str, converter=datetime.fromisoformat)
        q = YFQuoteResult(
            symbol=sym,
            currency=nav(jq, 'currency', types_ok=str),
            timestamp=ts.timestamp(), tz=ts.tzinfo,
            bid_size=nav(jq, 'bidSize'),
            ask_size=nav(jq, 'askSize'),
            bid=nav(jq, 'bid', converter=float, types_ok=str),
            ask=nav(jq, 'ask', converter=float, types_ok=str),
            low=nav(jq, 'low', converter=float, types_ok=str),
            high=nav(jq, 'high', converter=float, types_ok=str),
            last_size=nav(jq, 'lastSize'),
            last_price=nav(jq, 'last', converter=float, types_ok=str),
            change=None, change_percent=None,
            market_state=nav(jq, 'marketStatus', types_ok=str),
        )

        print(q)
        print(f'{sym} {jq["quotedAsOf"]} bid: {jq["bid"]} x {jq["bidSize"]}, ask: {jq["ask"]} x {jq["askSize"]}, last: {jq["last"]} x {jq["lastSize"]}')
