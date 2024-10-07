# Pairs of interlisted USD/CAD stocks and ETFs for Norbert's Gambit
#
# Mostly taken from "Best stocks for Norbert's Gambit" thread:
# https://www.canadianmoneyforum.com/threads/dual-listed-etfs-tsx-nyse.135364/post-1972456

ng_pairs = (                              # US$ symbol    CA$ symbol
    ('Horizons U.S. Dollar Currency ETF', 'DLR-U.TO',    'DLR.TO'),
    ('TD (Canadian bank)',                'TD',          'TD.TO'),
    ('BMO (Canadian bank)',               'BMO',         'BMO.TO'),
    ('CIBC (Canadian bank)',              'CM',          'CM.TO'),
    ('ScotiaBank (Canadian bank)',        'BNS',         'BNS.TO'),
    ('RBC (Canadian bank)',               'RY',          'RY.TO'),
    ('Canadian National Railway',         'CNI',         'CNR.TO'),
    ('Enbridge (oil/energy)',             'ENB',         'ENB.TO'),
    ('Suncor (oil/energy)',               'SU',          'SU.TO'),
    ('MFC (insurance/investment)',        'MFC',         'MFC.TO'),
    ('Horizons S&P 500 ETF',              'HXS-U.TO',    'HXS.TO'),
    ('Horizons TSX60 ETF',                'HXT-U.TO',    'HXT.TO'),
    ('Horizons Global Dev Index ETF',     'HXDM-U.TO',   'HXDM.TO'),
    ('Thompson Reuters',                  'TRI',         'TRI.TO'),
)

# IT IS NOT POSSIBLE TO USE THESE PAIRS FOR NORBERT'S GAMBIT
# because the USD/CAD symbols do not share the same CUSIPs.
#
# Taken from https://www.finiki.org/wiki/Norbert%27s_gambit#ETFs_with_different_CUSIPs

bad_list = (
    'ZSP.U', 'ZSP',
    'XEF.U', 'XEF',
    'XUS.U', 'XUS',
    'XUU.U', 'XUU',
)
