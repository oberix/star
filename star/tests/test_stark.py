# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, '/home/mpattaro/workspace/star/')
from star.share.stark import Stark

PKL_PATH = 'data/test_stark.pickle'

if __name__ == '__main__' :
    base = os.path.dirname(__file__)
    stk1 = Stark.load(os.path.join(base, PKL_PATH))
    stk1['MIO'] = '$X / $K * 1000'
    stk2 = Stark.load(os.path.join(base, PKL_PATH))
    stk2['MIO'] = '$X / $K * 1000'
    stk_tot = stk1.merge(stk2)
    print "ok"


