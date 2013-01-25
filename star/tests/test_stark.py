# -*- coding: utf-8 -*-
# pylint: disable=W0212
import numpy as np
import pandas
from star import Stark

if __name__ == '__main__' :

    np.random.seed()

    df = pandas.DataFrame({
        'YEAR': pandas.to_datetime(
            [str(year) for year in np.arange(2005, 2013)] * 3) ,
        'XER': ['ITA'] * 8 + ['FRA'] * 8 + ['DEU'] * 8,
        'X': np.random.randn(24),
        'K': np.random.randn(24),
    })
    stk = Stark(df)
    stk.md['vars']['YEAR']['type'] = 'D'
    stk.md['vars']['XER']['type'] = 'D'
    stk.md['vars']['X']['type'] = 'N'
    stk.md['vars']['K']['type'] = 'N'
    stk['OUT'] = '$X / $K * 1000'

    stk.cagr('X')
    stk.cagr('OUT')

    df1 = pandas.DataFrame({
        'XER': ['ITA', 'FRA', 'ESP'],
        'K': np.random.randn(3),
        'Q': np.random.randn(3),
    })
    stk1 = Stark(df1)
    stk1.md['vars']['XER']['type'] = 'D'
    stk1.md['vars']['K']['type'] = 'N'
    stk1.md['vars']['Q']['type'] = 'N'

    stk_tot = stk.merge(stk1)

    print stk_tot

