# -*- coding: utf-8 -*-

###############################################################################
# This is just an example of how a Star evaluation procedure should organized #
###############################################################################

import pandas

def elaborate(starks, year=None, company=None, **kwargs):
    return {'libro_giornale': StarK(DF=pandas.DataFrame(), COD='ciao', TYPE='tab')}
