# -*- coding: utf-8 -*-
import os
import sys
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

    stk2 = Stark.load(os.path.join(base, PKL_PATH))
    old_lm = stk2.lm
    stk2._lm = MetaDict()
    stk2._lm['vars'] = old_lm
    stk2['MIO'] = '$X / $K * 1000'

    stk_tot = stk1.merge(stk2)
    
    print "ok"


