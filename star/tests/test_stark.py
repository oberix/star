# -*- coding: utf-8 -*-
# pylint: disable=W0212
import numpy as np
import pandas
from star import Stark

if __name__ == '__main__' :

    np.random.seed()

    df = pandas.DataFrame({
        'YEAR': pandas.to_datetime([str(year) for year in np.arange(1995, 2013)]),
        'XER': ['ITA', 'FRA', 'DEU'] * 6,
        'X': np.random.randn(18),
        'K': np.random.randn(18),
    })
    stk = Stark(df)
    stk.md['vars']['YEAR']['type'] = 'D'
    stk.md['vars']['XER']['type'] = 'D'
    stk.md['vars']['X']['type'] = 'N'
    stk.md['vars']['K']['type'] = 'N'
    stk['OUT'] = '$X / $K * 1000'

    df1 = pandas.DataFrame({
        'YEAR': pandas.to_datetime([str(year) for year in np.arange(1995, 2013)]),
        'XER': ['ITA', 'FRA', 'DEU'] * 6,
        'X': np.random.randn(18),
        'K': np.random.randn(18),
    })
    stk1 = Stark(df1)
    stk1.md['vars']['YEAR']['type'] = 'D'
    stk1.md['vars']['XER']['type'] = 'D'
    stk1.md['vars']['X']['type'] = 'N'
    stk1.md['vars']['K']['type'] = 'N'
    stk1['OUT'] = '$X / $K * 1000'

    stk_tot = stk.merge(stk1)

    print "ok"


