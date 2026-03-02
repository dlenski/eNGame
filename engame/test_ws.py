import sys
import requests
import json
import uuid
import random
from datetime import datetime
import logging
import os

from websockets.sync.client import connect

from . import pairs
from .yq import YFQuoteResult, nav, navs
from . import ws_auth

logging.basicConfig(level=logging.INFO)
level = os.environ.get('WS_AUTH_LOGLEVEL', 'INFO').strip().upper()
ws_auth.logger.setLevel(level)

sess = ws_auth._new_ws_session()
u = ws_auth.authenticate(sess=sess)

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
#  -A ua \
#  -H 'x-platform-os: web' \
#  -H 'x-ws-api-version: 12' \
#  -H 'x-ws-device-id: '+devid \
#  -H 'x-ws-locale: en-CA' \
#  -H 'x-ws-profile: trade' \
#  --data-raw $'{"operationName":"FetchSecuritySearchResult","variables":{"query":"enbri"},"query":"query FetchSecuritySearchResult($query: String\u0021) {\\n  securitySearch(input: {query: $query}) {\\n    results {\\n      ...SecuritySearchResult\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment SecuritySearchResult on Security {\\n  id\\n  buyable\\n  status\\n  stock {\\n    symbol\\n    name\\n    primaryExchange\\n    __typename\\n  }\\n  features\\n  quoteV2 {\\n    securityId\\n    currency\\n    ... on EquityQuote {\\n      marketStatus\\n      __typename\\n    }\\n    __typename\\n  }\\n  __typename\\n}"}'

# Fetch wealthsimple quote:
# curl 'https://my.wealthsimple.com/graphql' \
#  -H 'authorization: Bearer '+jwt
#  -H 'content-type: application/json' \
#  -H ua \
#  -H 'x-platform-os: web' \
#  -H 'x-ws-api-version: 12' \
#  -H 'x-ws-device-id: '+devid \
#  -H 'x-ws-locale: en-CA' \
#  -H 'x-ws-profile: trade' \
#  --data-raw $'{"operationName":"FetchSecurityQuoteV2","variables":{"currency":null,"id":"sec-s-d670c0c7745743f8a0f469b2f02444fc"},"query":"query FetchSecurityQuoteV2($id: ID\u0021, $currency: Currency = null) {\\n  security(id: $id) {\\n    id\\n    quoteV2(currency: $currency) {\\n      ...SecurityQuoteV2\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment StreamedSecurityQuoteV2 on UnifiedQuote {\\n  __typename\\n  securityId\\n  ask\\n  bid\\n  currency\\n  price\\n  sessionPrice\\n  quotedAsOf\\n  ... on EquityQuote {\\n    marketStatus\\n    askSize\\n    bidSize\\n    close\\n    high\\n    last\\n    lastSize\\n    low\\n    open\\n    mid\\n    volume: vol\\n    referenceClose\\n    __typename\\n  }\\n  ... on OptionQuote {\\n    marketStatus\\n    askSize\\n    bidSize\\n    close\\n    high\\n    last\\n    lastSize\\n    low\\n    open\\n    mid\\n    volume: vol\\n    breakEven\\n    inTheMoney\\n    liquidityStatus\\n    openInterest\\n    underlyingSpot\\n    __typename\\n  }\\n}\\n\\nfragment SecurityQuoteV2 on UnifiedQuote {\\n  ...StreamedSecurityQuoteV2\\n  previousBaseline\\n  __typename\\n}"}'

if False:
    p0 = pairs.ng_pairs[0]
    r = sess.post('https://my.wealthsimple.com/graphql',
        json=json.loads('{"operationName":"FetchSecurityQuoteV2","variables":{"currency":null,"id":"'+p0.wssecid_cad+'"},"query":"query FetchSecurityQuoteV2($id: ID\u0021, $currency: Currency = null) {\\n  security(id: $id) {\\n    id\\n    quoteV2(currency: $currency) {\\n      ...SecurityQuoteV2\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment StreamedSecurityQuoteV2 on UnifiedQuote {\\n  __typename\\n  securityId\\n  ask\\n  bid\\n  currency\\n  price\\n  sessionPrice\\n  quotedAsOf\\n  ... on EquityQuote {\\n    marketStatus\\n    askSize\\n    bidSize\\n    close\\n    high\\n    last\\n    lastSize\\n    low\\n    open\\n    mid\\n    volume: vol\\n    referenceClose\\n    __typename\\n  }\\n  ... on OptionQuote {\\n    marketStatus\\n    askSize\\n    bidSize\\n    close\\n    high\\n    last\\n    lastSize\\n    low\\n    open\\n    mid\\n    volume: vol\\n    breakEven\\n    inTheMoney\\n    liquidityStatus\\n    openInterest\\n    underlyingSpot\\n    __typename\\n  }\\n}\\n\\nfragment SecurityQuoteV2 on UnifiedQuote {\\n  ...StreamedSecurityQuoteV2\\n  previousBaseline\\n  __typename\\n}"}'),
        headers={'Referer': f'https://my.wealthsimple.com/app/security-details/{p0.wssecid_cad}',
                 'Authorization': 'Bearer ' + u.access_token}
    )
    r.raise_for_status()
    from pprint import pprint
    print(p0.cad)
    pprint(r.json())

sess_info = {
    "authorization": 'Bearer ' + u.access_token,
    "x-ws-api-version": '12',
    "x-ws-locale": "en-CA",
    "x-ws-profile": "trade",
    "x-platform-os": "web",
    "x-ws-device-id": u.device_id,
}

with connect(
    'wss://realtime-api.wealthsimple.com/subscription',
    subprotocols=('graphql-transport-ws',),
    origin='https://my.wealthsimple.com',
    user_agent_header=ws_auth.USER_AGENT,
) as ws:
    init = {
        "type": "connection_init",
        "payload": sess_info,
    }
    ws.send(json.dumps(init))
    assert ws.recv() == '{"type":"connection_ack"}'

    ws2sym = {}
    for p in pairs.ng_pairs:
        for (si, sym) in ((p.wssecid_cad, p.cad), (p.wssecid_usd, p.usd)):
            if si is None or sym is None:
                continue

            ws2sym[si] = sym
            sub = {
                "id": si.removeprefix('sec-s-'),  # Reuse WealthSimple security ID as query ID
                "type": "subscribe",
                "payload": {
                    "variables": {"id": si},
                    "extensions": {},
                    "operationName": "QuoteV2BySecurityIdStream",
                    "query": "subscription QuoteV2BySecurityIdStream($id: ID!, $currency: Currency) {\n  securityQuoteUpdates(id: $id) {\n    id\n    quoteV2(currency: $currency) {\n      ...StreamedSecurityQuoteV2\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment StreamedSecurityQuoteV2 on UnifiedQuote {\n  __typename\n  securityId\n  ask\n  bid\n  currency\n  price\n  sessionPrice\n  quotedAsOf\n  ... on EquityQuote {\n    marketStatus\n    askSize\n    bidSize\n    close\n    high\n    last\n    lastSize\n    low\n    open\n    mid\n    volume\n    __typename\n  }\n  ... on OptionQuote {\n    marketStatus\n    askSize\n    bidSize\n    close\n    high\n    last\n    lastSize\n    low\n    open\n    mid\n    volume\n    breakEven\n    inTheMoney\n    liquidityStatus\n    openInterest\n    underlyingSpot\n    __typename\n  }\n}"
                }
            }
            ws.send(json.dumps(sub))

    for msg in ws:
        j = json.loads(msg)
        #print('*****', msg)
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
