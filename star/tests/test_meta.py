# -*- coding: utf-8 -*-
import os
import sys
import star
from star import Stark
from star.share.meta_dict import MetaDict, MetaDictVars

PKL_PATH = 'data/test_stark.pickle'

if __name__ == '__main__' :
    base = os.path.dirname(__file__)
    stk1 = Stark.load(os.path.join(base, PKL_PATH))
    old_lm = stk1.lm
    stk1._lm = MetaDict()
    stk1._lm['vars'] = old_lm
    stk1['MIO'] = '$X / $K * 1000'

    mio = stk1.rollup(MER='TOT').head()['MIO']

    assert(type(mio._lm) is star.share.meta_dict.MetaDict)
    assert(type(mio._lm['vars']) is star.share.meta_dict.MetaVars)
    assert(type(mio._lm['vars']['MIO']) is star.share.meta_dict.MetaDictVars) 

    assert(type(mio._lm['graph']) is star.share.meta_dict.MetaDictGraph)
    assert(type(mio._lm['graph']['vars']) is star.share.meta_dict.MetaVarsGraph)
#    assert(type(mio._lm['graph']['vars']['MIO']) is star.share.meta_dict.MetaDictGraphVars) 

    assert(type(mio._lm['table']) is star.share.meta_dict.MetaDictTable)
    assert(type(mio._lm['table']['vars']) is star.share.meta_dict.MetaVarsTable)
#    assert(type(mio._lm['table']['vars']['MIO']) is star.share.meta_dict.MetaDictTableVars) 

    assert(type(mio._lm['des']) is star.share.meta_dict.MetaDictDes)
    assert(type(mio._lm['des']['vars']) is star.share.meta_dict.MetaVarsDes)
#    assert(type(mio._lm['des']['vars']['MIO']) is star.share.meta_dict.MetaDictDesVars) 

    print "ok"


