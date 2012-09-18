# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Marco Pattaro (<marco.pattaro@servabit.it>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

import numpy as np
import matplotlib.pyplot as plt

__author__ = "Marco Pattaro <marco.pattaro@servabit.it>"
__version__ = "0.1"
__all__ = ['Graph']

class Graph(object):
    
    def __init__(self, data, **kwargs):
        pass

    def to_latex():
        pass

class TexGraph(Graph):
    # TODO: implement
    pass

class HTMLGraph(Graph):
    # TODO: implement
    pass

if __name__ == '__main__':
    ''' TEST '''

    from share import Bag

    lm = {
        'CRT_MVL': ['plot', 'dx', 'avere'],
        'DBT_MVL': ['plot', 'sx', 'dare'],
        }

    df = Bag.load('/home/mpattaro/workspace/star/trunk/sre/esempio/table0.pickle').DF
#    graph_bag = Bag(LM=lm, DF=df, TIP="graph")
    graph_bag.save('/home/mpattaro/workspace/star/trunk/sre/esempio/graph0.pickle')
    
    
