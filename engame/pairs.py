'''
Pairs of interlisted USD/CAD stocks and ETFs for Norbert's Gambit

Mostly taken from "Best stocks for Norbert's Gambit" thread:
https://www.canadianmoneyforum.com/threads/dual-listed-etfs-tsx-nyse.135364/post-1972456

US CUSIP search: https://www.quantumonline.com/search.cfm?sopt=symbol&tickersymbol=AAA
'''

from collections import namedtuple
SameCusipPair = namedtuple('SameCusipPair', ('desc', 'cusip', 'usd', 'cad', 'wssecid_usd', 'wssecid_cad'))
SAME = WITH_U = None
p = lambda desc, cusip, usd, cad, wssecid_usd, wssecid_cad: SameCusipPair(
    desc, cusip,
    cad + '-U.TO' if usd is WITH_U else usd,
    (usd if cad is SAME else cad) + '.TO',
    ('sec-s-' + wssecid_usd) if wssecid_usd is not None else None,
    'sec-s-' + wssecid_cad)

ng_pairs = (
    #                                                      |--- Yahoo Finance ---|    |------------------------------ WealthSimple ----------------------------|
    #                                        CUSIP         US$ symbol   CA$ symbol    US$ security ID                       CA$ security ID

    # For all these interlisted *stocks*, the US$ side is listed on NYSE or Nasdaq, while the CA$ side is listed in Toronto:
    p('TD (Canadian bank)',                  '891160509',  'TD',        SAME,         '41b756b014454655a0365699984eeeab',   'ea5e995e98774e3d998aa5dae06cf237'),
    p('BMO (Canadian bank)',                 '063671101',  'BMO',       SAME,         '86557912ccea4345a788fcb964011bf3',   'd670c0c7745743f8a0f469b2f02444fc'),
    p('CIBC (Canadian bank)',                '136069101',  'CM',        SAME,         '79e64cacd75647bdb574abecad681ed6',   'b898f6623a2c42649f9e9b53532b073c'),
    p('ScotiaBank (Canadian bank)',          '064149107',  'BNS',       SAME,         'be8e0d081aeb48b3847f4b24316a749d',   'cac48e23f5b84b4787b97628581ce59f'),
    p('RBC (Canadian bank)',                 '780087102',  'RY',        SAME,         '6501705bb1614b47ad5e72105d47a41b',   '3305aeb61f3a4b8797140439b028689b'),
    p('Canadian National Railway',           '136375102',  'CNI',       'CNR',        '1c3b2af163aa4e2fb19a573fa7d5134e',   '37f80b493095405189c7ea131adfd8ce'),
    p('Enbridge (oil/energy)',               '29250N105',  'ENB',       SAME,         '92ff02d9a03b4bc69c0f2c58ed0155fe',   '5405e20fa09946d29c768e0d41a4195d'),
    p('Suncor (oil/energy)',                 '867224107',  'SU',        SAME,         '845cd37ec20648769043de645d1e3d2e',   'e90effe2699b47acbd69e96ffd0fea97'),
    p('MFC (insurance/investment)',          '56501R106',  'MFC',       SAME,         '0138dbbecbe84a14ad1c982499911488',   '82d7214a0efa4d338bb8307838f8f0aa'),
    p('Thompson Reuters',                    '884903709',  'TRI',       SAME,         '74c92230b14b40f190ff3b3ef40a0d54',   '8e618c90909b4908b75997d4a497d07a'),

    # For all these interlisted *ETFs*, both US$ and CA$ sides are listed in Toronto:
    p('Horizons U.S. Dollar Currency ETF',   '379948102',  WITH_U,      'DLR',        '6f10b675a88649bd8dcd13040d1e8594',   '4c836ded25404e71862ac52ff5219506'),
    p('Horizons S&P 500 ETF',                '37964P100',  WITH_U,      'HXS',        None,                                 '27165f620fe14413bd2ee518716fa53f'),
    p('Horizons TSX60 ETF',                  '37963M108',  WITH_U,      'HXT',        None,                                 '12d0b80be5384550baf4b6a9ab21b7a2'),
    p('Horizons Global Dev Index ETF',       '37963V108',  WITH_U,      'HXDM',       None,                                 'bc584288e77b4d4994cbc9bffa0a8373'),
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
