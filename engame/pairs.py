'''
Pairs of interlisted USD/CAD stocks and ETFs for Norbert's Gambit

Mostly taken from "Best stocks for Norbert's Gambit" thread:
https://www.canadianmoneyforum.com/threads/dual-listed-etfs-tsx-nyse.135364/post-1972456

US CUSIP search: https://www.quantumonline.com/search.cfm?sopt=symbol&tickersymbol=AAA
'''

from collections import namedtuple
p = namedtuple('SameCusipPair', ('desc', 'usd', 'cad', 'cusip'))

ng_pairs = (                               # US$ symbol    CA$ symbol    CUSIP
    p('Horizons U.S. Dollar Currency ETF', 'DLR-U.TO',    'DLR.TO',     '379948102'),
    p('TD (Canadian bank)',                'TD',          'TD.TO',      '891160509'),
    p('BMO (Canadian bank)',               'BMO',         'BMO.TO',     '063671101'),
    p('CIBC (Canadian bank)',              'CM',          'CM.TO',      '136069101'),
    p('ScotiaBank (Canadian bank)',        'BNS',         'BNS.TO',     '064149107'),
    p('RBC (Canadian bank)',               'RY',          'RY.TO',      '780087102'),
    p('Canadian National Railway',         'CNI',         'CNR.TO',     '136375102'),
    p('Enbridge (oil/energy)',             'ENB',         'ENB.TO',     '29250N105'),
    p('Suncor (oil/energy)',               'SU',          'SU.TO',      '867224107'),
    p('MFC (insurance/investment)',        'MFC',         'MFC.TO',     '56501R106'),
    p('Horizons S&P 500 ETF',              'HXS-U.TO',    'HXS.TO',     '37964P100'),
    p('Horizons TSX60 ETF',                'HXT-U.TO',    'HXT.TO',     '37963M108'),
    p('Horizons Global Dev Index ETF',     'HXDM-U.TO',   'HXDM.TO',    '37963V108'),
    p('Thompson Reuters',                  'TRI',         'TRI.TO',     '884903709'),
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
)
