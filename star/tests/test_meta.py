# -*- coding: utf-8 -*-
# pylint: disable=W0212
import numpy as np
import pandas
import star
from star import Stark

if __name__ == '__main__' :

    df = pandas.DataFrame({
        'YEAR': pandas.to_datetime([str(year) for year in np.arange(1995, 2013)]),
        'XER': ['ITA', 'FRA', 'DEU'] * 6,
        'X': np.random.randn(18),
        'K': np.random.randn(18),
    })
    stk = Stark(df)
    stk._md['vars']['YEAR']['type'] = 'D'
    stk._md['vars']['XER']['type'] = 'D'
    stk._md['vars']['X']['type'] = 'N'
    stk._md['vars']['K']['type'] = 'N'
    stk['OUT'] = '$X / $K * 1000'
    out = stk.rollup(YEAR='TOT')['OUT']

    assert(type(out._md) is star.share.meta_dict.Meta)
    assert(type(out._md['vars']) is star.share.meta_dict.MetaVars)
    assert(type(out._md['vars']['OUT']) is star.share.meta_dict.MetaVarsAttr,)

    assert(type(out._md['graph']) is star.share.meta_dict.MetaGraph)
    assert(type(out._md['graph']['vars']) is star.share.meta_dict.MetaVarsGraph)
    # assert(type(out._md['graph']['vars']['OUT']) is star.share.meta_dict.MetaVarsAttrGraph)

    assert(type(out._md['table']) is star.share.meta_dict.MetaTable)
    assert(type(out._md['table']['vars']) is star.share.meta_dict.MetaVarsTable)
    # assert(type(out._md['table']['vars']['OUT']) is star.share.meta_dict.MetaVarsAttrTable)

    assert(type(out._md['des']) is star.share.meta_dict.MetaDes)
    assert(type(out._md['des']['vars']) is star.share.meta_dict.MetaVarsDes)
    # assert(type(out._md['des']['vars']['OUT']) is star.share.meta_dict.MetaVarsAttrDes)

    print "ok"