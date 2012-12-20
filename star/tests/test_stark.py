# -*- coding: utf-8 -*-
import os
from star.share.stark import Stark

PKL_PATH = 'data/test_stark.pickle'

if __name__ == '__main__' :
    base = os.path.dirname(__file__)
    stk1 = Stark.load(os.path.join(base, PKL_PATH))
    stk2 = Stark.load(os.path.join(base, PKL_PATH))
    stk1._lm['Q']['munit'] = 'Lupini'
    stk2._lm['Q']['munit'] = 'Bagigi'
    stk_tot = stk1 + stk2
    print "ok"


