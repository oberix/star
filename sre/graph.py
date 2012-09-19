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

import matplotlib.pyplot as plt
#from matplotlib.figure import Figure
from matplotlib import rc
import logging

__author__ = "Marco Pattaro <marco.pattaro@servabit.it>"
__version__ = "0.1"
__all__ = ['Graph']

GRAPH_TYPES = (
    'plot',
    'bar',
    'scatter',
)

class Graph(object):
    
    def __init__(self, data, **kwargs):
        self._logger = logging.getLogger(type(self).__name__)
        self._title = data.TITLE
        self._footnote = data.FOOTNOTE
        self._df = data.DF
        self._graph = list()
        self.parse_lm(data.LM)
        self._figure = self.make_graph()

    def parse_lm(self, lm):
        ''' Parse Bag's LM dictionary and estract the following non-public
        attrubutes:

        _lax: Series to use as x axes
        _graph: a subset of LM containing only variables we are going to plot.

        '''
        # TODO: handle line styles
        for key, val in lm.iteritems():
            if val[0] == 'lax':
                self._lax = self._df[key]
            elif val[0] in GRAPH_TYPES:
                self._graph.append({
                        'key': key,
                        # 'order': val[0],
                        'type': val[0],
                        'ax': val[1],
                        'label': val[2],
                        'color': val[3],
                        })
            else:
                self._logger.warning("Unhandled graph type '%s', I will ignore entry '%s'", val[0], key)
                continue

    def make_graph(self):
        # TODO: handle legend position and layout
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1, axisbg='#eeefff', autoscale_on=True, 
                                      adjustable="box")
        ax.grid(True)
        lines = list()
        labels = list()
        for idx in xrange(len(self._graph)):
            col = self._graph[idx]
            # Axes
            new_ax = ax
            if idx > 0:
                new_ax = fig.add_axes(
                    ax.get_position(True), 
                    label=col['label'],
                    frameon=False, 
                    sharex=ax)
            if col['ax'] == 'dx':
                new_ax.yaxis.tick_right()
            # Handle different graph types
            if col['type'] == 'plot':
                line = ax.plot(self._lax, self._df[col['key']], color=col['color'])
            elif col['type'] == 'bar':
                line = ax.bar(self._lax, self._df[col['key']], color=col['color'], align='center')
            elif col['type'] == 'scatter':
                line = ax.scatter(self._df[col['key']])
            else:
                self._logger.warning("Unhandled graph type '%s', I will ignore entry '%s'", 
                                     col['type'], col['key'])
                continue
            lines.append(line)
            labels.append(col['label'])
        leg = fig.legend((line[0] for line in lines), labels)
        return fig

    def out(self):
        ''' You have to extend this class and override this method in order to
        generate a different report format.

        '''
        raise NotImplementedError

class TexGraph(Graph):
    
    def __init__(self, data, **kwargs):
        super(TexGraph, self).__init__(data, **kwargs)
        # Tell matplotlib to use LaTeX to render text
        rc('text', usetex=True)
        
    def out(self):
        pass

class HTMLGraph(Graph):

    def out(self):
        pass


if __name__ == '__main__':
    ''' TEST '''

    import os
    import sys

    BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
    sys.path.append(BASEPATH)
    sys.path = list(set(sys.path))

    from share import Bag
    import pandas as pnd
    import numpy as np
    
    logging.basicConfig(level = logging.DEBUG)

    lm = {
        'a': ['lax'],
        'c': ['plot', 'sx', 'Ciao', 'r'],
        'b': ['bar', 'dx', 'Bau', 'b'],
        'd': ['plot', 'dx', 'Dau', 'g'],
        }

    df = pnd.DataFrame({'a':np.arange(0, 10,1)})
    df['b'] = np.random.randn(10)
    df['c'] = np.random.randn(10)
    df['d'] = np.random.randn(10)

    path = '/tmp/pollo.pickle'
    bag = Bag(df, path, LM=lm)
    graph = TexGraph(bag)
    graph._figure.show()
    
    
