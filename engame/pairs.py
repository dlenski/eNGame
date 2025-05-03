'''
Pairs of interlisted USD/CAD stocks and ETFs for Norbert's Gambit

Mostly taken from "Best stocks for Norbert's Gambit" thread:
https://www.canadianmoneyforum.com/threads/dual-listed-etfs-tsx-nyse.135364/post-1972456

US CUSIP search: https://www.quantumonline.com/search.cfm?sopt=symbol&tickersymbol=AAA
'''

from collections import namedtuple
p = namedtuple('SameCusipPair', ('desc', 'cusip', 'usd', 'cad', 'wssecid'))

ng_pairs = (
    #                                                      |---- Yahoo Finance ----|    |------------- WealthSimple ------------|
    #                                        CUSIP         US$ symbol     CA$ symbol    CA$ security ID

    # For all these interlisted *stocks*, the US$ side is listed on NYSE or Nasdaq, while the CA$ side is listed in Toronto:
    p('TD (Canadian bank)',                  '891160509',  'TD',          'TD.TO',      'sec-s-ea5e995e98774e3d998aa5dae06cf237'),
    p('BMO (Canadian bank)',                 '063671101',  'BMO',         'BMO.TO',     'sec-s-d670c0c7745743f8a0f469b2f02444fc'),
    p('CIBC (Canadian bank)',                '136069101',  'CM',          'CM.TO',      'sec-s-b898f6623a2c42649f9e9b53532b073c'),
    p('ScotiaBank (Canadian bank)',          '064149107',  'BNS',         'BNS.TO',     'sec-s-cac48e23f5b84b4787b97628581ce59f'),
    p('RBC (Canadian bank)',                 '780087102',  'RY',          'RY.TO',      'sec-s-3305aeb61f3a4b8797140439b028689b'),
    p('Canadian National Railway',           '136375102',  'CNI',         'CNR.TO',     'sec-s-37f80b493095405189c7ea131adfd8ce'),
    p('Enbridge (oil/energy)',               '29250N105',  'ENB',         'ENB.TO',     'sec-s-5405e20fa09946d29c768e0d41a4195d'),
    p('Suncor (oil/energy)',                 '867224107',  'SU',          'SU.TO',      'sec-s-e90effe2699b47acbd69e96ffd0fea97'),
    p('MFC (insurance/investment)',          '56501R106',  'MFC',         'MFC.TO',     'sec-s-82d7214a0efa4d338bb8307838f8f0aa'),
    p('Thompson Reuters',                    '884903709',  'TRI',         'TRI.TO',     'sec-s-8e618c90909b4908b75997d4a497d07a'),

    # For all these interelisted *ETFs*, both US$ and CA$ sides are listed in Toronto:
    p('Horizons U.S. Dollar Currency ETF',   '379948102',  'DLR-U.TO',    'DLR.TO',     'sec-s-4c836ded25404e71862ac52ff5219506'),
    p('Horizons S&P 500 ETF',                '37964P100',  'HXS-U.TO',    'HXS.TO',     'sec-s-27165f620fe14413bd2ee518716fa53f'),
    p('Horizons TSX60 ETF',                  '37963M108',  'HXT-U.TO',    'HXT.TO',     'sec-s-12d0b80be5384550baf4b6a9ab21b7a2'),
    p('Horizons Global Dev Index ETF',       '37963V108',  'HXDM-U.TO',   'HXDM.TO',    'sec-s-bc584288e77b4d4994cbc9bffa0a8373'),
)

# IT IS NOT POSSIBLE TO USE THESE PAIRS FOR NORBERT'S GAMBIT
# because the USD/CAD symbols do not share the same CUSIPs,
# as explained in
# https://www.finiki.org/wiki/Norbert%27s_gambit#ETFs_with_different_CUSIPs

bad_list = (
    # Taken from https://www.finiki.org/w/index.php?title=Norbert%27s_gambit&oldid=25581
    'ZSP.U', 'ZSP',
    'XEF.U', 'XEF',
    'XUS.U', 'XUS',
    'XUU.U', 'XUU',
    # Other ETFs that are commission-free on BMO SD (https://www.bmoinvestorline.com/selfDirected/pdfs/no_commission_fee_etfs_en.pdf), but which have different CUSIPs:
    'ZLU.U', 'ZLU', # https://www.bmogam.com/ca-en/products/exchange-traded-fund/bmo-low-volatility-us-equity-etf-zlu, https://www.bmogam.com/ca-en/products/exchange-traded-fund/bmo-low-volatility-us-equity-etf-zlu
    'ZDY.U', 'ZDY', # https://bmogam.com/ca-en/products/exchange-traded-fund/bmo-us-dividend-etf-zdy, https://bmogam.com/ca-en/products/exchange-traded-fund/bmo-us-dividend-etf-usd-units-zdy-u
    'ZUQ.U', 'ZUQ', # https://bmogam.com/ca-en/products/exchange-traded-fund/bmo-msci-usa-high-quality-index-etf-zuq, https://bmogam.com/ca-en/products/exchange-traded-fund/bmo-msci-usa-high-quality-index-etf-usd-units-zuq-u
    'ZWH.H', 'ZWH', # https://bmogam.com/ca-en/products/exchange-traded-fund/bmo-us-high-dividend-covered-call-etf-zwh, https://bmogam.com/ca-en/products/exchange-traded-fund/bmo-us-high-dividend-covered-call-etf-us-dollar-units-zwh-u
    'XEC.U', 'XEC', # https://www.blackrock.com/ca/investors/en/products/251423/ishares-msci-emerging-markets-imi-index-etf, https://www.blackrock.com/ca/investors/en/products/310734/ishares-core-msci-emerging-markets-imi-index-etf
    'XMU.U', 'XMU', # https://www.blackrock.com/ca/investors/en/products/310740/ishares-msci-min-vol-usa-index-etf, https://www.blackrock.com/ca/investors/en/products/239694/ishares-msci-usa-minimum-volatility-index-etf,
    'ZMI.U', 'ZMI', # https://bmogam.com/ca-en/products/exchange-traded-fund/bmo-monthly-income-etf-zmi/, https://www.bmogam.com/ca-en/products/exchange-traded-fund/bmo-monthly-income-etf-usd-units-zmi-u/
    'ZJK.U', 'ZJK', # https://www.bmogam.com/ca-en/products/exchange-traded-fund/bmo-high-yield-us-corporate-bond-index-etf-zjk/, https://www.bmogam.com/ca-en/products/exchange-traded-fund/bmo-high-yield-us-corporate-bond-index-etf-usd-units-zjk-u/
)
