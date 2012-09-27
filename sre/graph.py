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
import matplotlib.patches as patches
from matplotlib import rc
import logging
from tempfile import NamedTemporaryFile, TemporaryFile

__author__ = "Marco Pattaro <marco.pattaro@servabit.it>"
__version__ = "0.1"
__all__ = ['Graph']

GRAPH_TYPES = (
    'plot',
    'bar',
    'scatter',
)

FIGSIZE = { # (w, h) in inches
    'stamp': (3.180, 2.380),
    'dinamic': (6.360, 2.380),
    'square': (6.360, 6.360),
    'flag': (3.180, 9.52),
}

VAL_STEP = {
    0: 0,
    0.5: 0.2,
    1: 0.5,
    2: 1,
    8: 2,
    15: 5,
    30: 10,
    60: 20,
    120: 40,
    150: 50,
    300: 60,
    500: 100,
    1000: 200,
    1500: 500,
    3000: 1000,
    6000: 2000,
    10000: 20000,
    12000: 4000,
    15000: 5000,
    30000: 6000,
    50000: 10000,
}

WORST_COLOR = "#FFDBC1"
BEST_COLOR = "#9BFFE6"

class Graph(object):

    def __init__(self, data, **kwargs):
        self._logger = logging.getLogger(type(self).__name__)
        rc('legend', **{
                'markerscale': 1, 
                'labelspacing': 0, 
                'columnspacing': 1, 
                'borderpad': 0,
                })
#        self._data = data
        self._title = data.TITLE
        self._footnote = data.FOOTNOTE
        self._df = data.DF
        self._graph = list()
        self._fontsize = data.fontsize
        self._size = data.size
#        self._legend = self._data.legend
        self.parse_lm(data.LM)
        self._figure = self.make_graph()

    def _make_legend(self, figure, handles, labels):
        ''' Create legend for the graph, evaluate how the whole figure must be
        scaled to make room for the legend.
        
        @ param figure: Figure object that must contain the legend
        @ param hadles: list of Line an Path objects used to populate the
             graph.
        @ param labels: list of string used as labels in the legend
        @ return: the new Legend created.

        '''
        # Evaluate number of columns
        ncol = 3
        if len(handles) < 5:
            ncol = 2
        elif len(handles) < 3:
            ncol = 1
        # Estimate new hight needed for the legend
        dheight = ((len(handles)/ncol) + 1) * self._fontsize * 0.01
        dheight_perc = dheight / figure.get_figheight() 
        # Scale figure and adjust subplot
        figure.set_figheight(figure.get_figheight() + dheight)
        figure.subplots_adjust(top=(0.9-dheight_perc))
        # Make legend
        leg = figure.legend(handles, labels, ncol=ncol, loc='upper left',
                            bbox_to_anchor=(0.10, 1.0))
        leg.get_frame().set_linewidth(0) # Remove legend border

        return leg


    def _scatter(self, ax, y_meta):
        ''' Buld a scatter plot.

        @ param y_meta:
        @ return: A Collection instance
        '''
        x_data = self._lax
        y_data = self._df[y_meta['key']]
        # TODO: set lable for the axes
        val = (x_data[0], y_data[0])
        bench = (x_data[1], y_data[1])
        quadrant = (x_data[2], y_data[2])
        margin = 1 # TODO: make it scaled to val
        min_val = (x_data[0:2].min() - margin, y_data[0:2].min() - margin)
        max_val = (x_data[0:2].min() + margin, y_data[0:2].min() + margin)
        
        for idx in xrange(len(quadrant)):
            quad = quadrant[idx]
            # if quad < 2:
            #     width = max_val[0] - bench[0]
            # else:
            #     width = bench[0] - min_val[0]
            # if quad == 1 or quad == 2:
            #     height = bench[1] - min_val[1]
            # else:
            #     height = max_val[1] - bench[1]
            if quad == 0:
                p2 = (bench_x, bench_y)
                w2 = (max_ax - bench_x)
                h2 = (max_ay - bench_y)
            elif quad == 1:
                p2 = (bench_x, min_ay)
                w2 = (max_ax - bench_x)
                h2 = (bench_y - min_ay)
            elif quad == 2:
                p2 = (min_ax, min_ay)
                w2 = (bench_x - min_ax)
                h2 = (bench_y - min_ay)
            elif quad == 3:
                p2 = (min_ax, bench_y)
                w2 = (bench_x - min_ax)
                h2 = (max_ay - bench_y)        
            color = WORST_COLOR
            if idx == 0:
                color = BEST_COLOR
            ax.add_patch(
                patches.Rectangle(
                    bench, width=width, height=height, antialiased=True,
                    facecolor=color, zorder=1))

        return ax.scatter(val[0], val[1], s=50, c=y_meta['color'], color='DarkBlue', antialiased=True, zorder=3)
        # TODO: where is the label?
        # offset = 0.02
        # text_pos(val[0]+offset, val[1]+offset)
        # an = ax.text(text_pos, 
        #              imp_name, color='DarkBlue', clip_on=False, zorder=4)
        

    def parse_lm(self, lm):
        ''' Parse Bag's LM dictionary and estract the following non-public
        attrubutes:

        _lax: Series to use as x axes
        _graph: a subset of LM containing only variables we are going to plot.

        '''
        # TODO: handle line styles (see sftp://terra.devsite/home/studiabo/UlisseRep/Q20/Q20S2630/HS690790/MER_ARE)
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
        ''' Create a Figure and plot a graph in it following what was specified
        in Bag.LM.

        @ return: the Figure instance created
        
        ''' 
        fig = plt.figure(figsize=FIGSIZE[self._size])
        ax = fig.add_subplot(1,1,1, axisbg='#eeefff', autoscale_on=True,
                             adjustable="datalim")
        ax.set_xlim(self._lax.min(), self._lax.max())
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
                # FIXME: Centered bars cause the plot to be much wider on the right
                # TODO: handle cumulative bars
                line = ax.bar(self._lax, self._df[col['key']], color=col['color'], align='center')
            elif col['type'] == 'scatter':
                line = self._scatter(ax, col)
            else:
                self._logger.warning("Unhandled graph type '%s', I will ignore entry '%s'", 
                                     col['type'], col['key'])
                continue
            lines.append(line)
            labels.append(col['label'])
        # if self._legend:
        #     handles = [line[0] for line in lines]
        #     leg = self._make_legend(fig, handles, labels)
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
        rc('font',**{
                'family': 'serif',
                'sans-serif':['Computer Modern Roman'], 
                'size':self._fontsize})
        rc('text', usetex=True)
 
    def out(self):
        if self._logger.getEffectiveLevel() > logging.DEBUG:
            fd = NamedTemporaryFile(suffix='.pdf')
        else:
            fd = open('/tmp/tmpsregraph.pdf', 'wb')
        self._figure.savefig(fd, format='pdf')
        ret = "\\includegraphics{%s}" % fd.name
        self._logger.debug("graph file name is '%s'", fd.name)
        return ret, fd

class HTMLGraph(Graph):

    def out(self):
        # TODO: implement
        raise NotImplementedError

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
        'c': ['scatter', 'sx', '\LaTeX', 'r'],
        # 'b': ['bar', 'dx', "$E=mc^2$", 'b'],
        # 'd': ['plot', 'dx', 'Dau', 'g'],
        }    

    df = pnd.DataFrame({'a':np.arange(0, 10,1)})
    df['b'] = np.random.randn(10)
    df['c'] = np.random.randn(10)
    df['d'] = np.random.randn(10)

    path = '/home/mpattaro/workspace/star/trunk/sre/esempio/graph0.pickle'
    bag = Bag(df, path, LM=lm, TI='graph')
    bag.save()

    lm = {
        'b': [0, '|c|', '|@v0|', '|Bao'],
        'c': [1, 'l|', '|@v0|', '\LaTeX|'],
        'd': [2, 'r|', '@v1|', 'Dau|'],
        }
        
    path = '/home/mpattaro/workspace/star/trunk/sre/esempio/table0.pickle'
    bag = Bag(df, path, LM=lm, TITLE='Esempio')
    bag.save()

    # graph = TexGraph(bag)
    # graph._figure.show()
#    bag.save()
#    graph._figure.savefig('/tmp/pollo.pdf', format='pdf')
    
    
