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
import numpy as np
import logging
from tempfile import NamedTemporaryFile, TemporaryFile

import plotters

__author__ = "Marco Pattaro <marco.pattaro@servabit.it>"
__version__ = "0.1"
__all__ = ['Graph']

GRAPH_TYPES = (
    'plot',
    'bar',
    'barh',
    'scatter',
)

FIGSIZE = { # (w, h) in inches
    'stamp': (3.200, 2.0), # (3.180, 2.380)
    'dinamic': (6.360, 2.380),
    'square': (6.360, 6.360),
    'flag': (3.180, 9.52),
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
        self._y_meta = list()
        self._x_meta = list()
        self._fontsize = data.fontsize
        self._size = data.size
        self._legend = data.legend
        self._plotters = dict()
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
        This method covers the case of a scatter with one point which position
        is highlited by a system axes with colored quadrants, where each colo
        tels if it's a good, neutral or bad placement.

        @ param y_meta:
        @ return: A Collection instance

        '''
        x_data = self._lax
        y_data = self._df[y_meta['key']]
        x_meta = self._x_meta[0]
        # TODO: set lable for the axes
        val = (x_data[0], y_data[0])
        bench = (x_data[1], y_data[1])
        quadrant = (x_data[2], y_data[2])
        # TOCHECK: log looks good, but it's just empirical
        margin = (np.log2(np.abs(x_data[0:2].max() - x_data[0:2].min())), 
                  np.log2(np.abs(y_data[0:2].max() - y_data[0:2].min())))
        min_val = (x_data[0:2].min() - margin[0], y_data[0:2].min() - margin[0])
        max_val = (x_data[0:2].max() + margin[1], y_data[0:2].max() + margin[1])

        # Draw colored quadrants
        for idx, quad in enumerate(quadrant):
            if quad < 2: # 2 right quadrants
                rect_x = bench[0]
                width = max_val[0] - bench[0]
            else:  # 2 left quadrants
                rect_x = min_val[0]
                width = bench[0] - min_val[0]
            if quad == 1 or quad == 2: # 2 lower quadrants
                rect_y = min_val[1]
                height = bench[1] - min_val[1]
            else: # 2 upper quadrants
                rect_y = bench[1]
                height = max_val[1] - bench[1]
            color = BEST_COLOR
            if idx == 0:
                color = WORST_COLOR
            rect = patches.Rectangle(
                (rect_x, rect_y), width=width, height=height, antialiased=True,
                facecolor=color, zorder=1)
            ax.add_patch(rect)
        # Draw dot
        scat = [ax.scatter(val[0], val[1], s=20, c=y_meta['color'],
                          color=y_meta['color'], antialiased=True, zorder=3)]
        
        offset = (margin[0]/15.0, margin[1]/15.0)
        # Add a lable to the dot
        # TODO: this string should be escaped
        label = ax.text(val[0] + offset[0], val[1] + offset[1], self._title,
                        color=y_meta['color'], clip_on=False, zorder=4)
        ax.add_artist(label)

        # bechmark axes
        ax.axvline(x = bench[0], linewidth=2, linestyle='--', 
                   color='MidnightBlue', antialiased=True, zorder=2)
        ax.axhline(y = bench[1], linewidth=2, linestyle='--',
                   color='MidnightBlue', antialiased=True, zorder=2)
        
        # Set axes tiks, limit and labels
        ax.set_xlim((min_val[0], max_val[0]))
        ax.set_xticks([bench[0], val[0]])
        ax.set_ylim((min_val[1], max_val[1]))
        ax.set_yticks([bench[1], val[1]])
        # TODO: this strings should be escaped too
        xlab = ax.set_xlabel(x_meta['label'], color='DarkBlue', labelpad=-1)
        ylab = ax.set_ylabel(y_meta['label'], color='DarkBlue', labelpad=-1)
        
        # FIME: isn't there a better way to avoid axes labels to fall off the
        # figure?
        # ax.get_figure().subplots_adjust(right=0.750, left=0.175, 
        #                                 top=0.950, bottom=0.150)
        return scat

    def parse_lm(self, lm):
        ''' Parse Bag's LM dictionary and estract the following non-public
        attrubutes:

        _lax: Series to use as x axes
        _y_meta: metadata for y ax series
        _x_meta: metadata for x ax series

        '''
        # TODO: handle line styles
        for key, val in lm.iteritems():
            if val[0] == 'lax':
                self._lax = self._df[key]
                self._x_meta.append({
                    'key': key,
                    'type': val[0],
                    'ax': val[1],
                    'label': val[2],
                    'color': val[3],})
            elif val[0] in GRAPH_TYPES:
                self._y_meta.append({
                        'key': key,
                        'type': val[0],
                        'ax': val[1],
                        'label': val[2],
                        'color': val[3],
                        })
                if not self._plotters.get(val[0]):
                    self._plotters[val[0]] = plotters.__getattribute__(val[0])(self)
            else:
                self._logger.warning(
                    "Unhandled graph type '%s', I will ignore entry '%s'", 
                    val[0], key)
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
        for idx, col in enumerate(self._y_meta):
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
            try:
                line = self._plotters[col['type']].plot(ax, col)
            except KeyError:
                # TODO: print some worning
                continue
            lines.append(line)
            labels.append(col['label'])
        if self._legend:
            handles = [line[0] for line in lines]
            leg = self._make_legend(fig, handles, labels)
        return fig

    def out(self):
        ''' You have to extend this class and override this method in order to
        generate a different report format.

        '''
        raise NotImplementedError

class TexGraph(Graph):
    ''' Extends Graph to generate LaTeX rendered graphs; implements out()
    method so that it produce a LaTeX tag ready to be substitued in the
    template.
    '''
    
    def __init__(self, data, **kwargs):
        ''' Just set some rc params
        ''' 
        super(TexGraph, self).__init__(data, **kwargs)
        # Tell matplotlib to use LaTeX to render text
        rc('font', **{
                'family': 'serif',
                'sans-serif':['Computer Modern Roman'], 
                'size':self._fontsize})
        rc('text', usetex=True)
 
    def out(self):
        ''' Produce a LaTeX compatible tag to be substituted in the template.
        '''
        delete = True
        if self._logger.getEffectiveLevel() <= logging.DEBUG:
            delete = False
        fd = NamedTemporaryFile(suffix='.pdf', delete=delete)        
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
        'a': ['lax', 'sx', 'Ammonrtamenti in \% produzione', 'r'],
        # 'b': ['scatter', 'sx', "Intensita' capitale fisso", 'b'],
        'c': ['bar', 'sx', "$E=mc^2$", 'b'],
        'd': ['plot', 'dx', 'Dau', 'g'],
        }    

    df = pnd.DataFrame({
            # 'a': [5.1, 6.1, 0],
            # 'b': [32.0, 33.0, 2],
            'a': np.arange(0, 10, 1),
            # 'b': np.random.randint(100, size=2),
            'c': np.random.randint(100, size=10),
            'd': np.random.randint(100, size=10),
         })

    path = '/home/mpattaro/workspace/star/trunk/reports/esempio/graph0.pickle'
    bag = Bag(df, LD=path, LM=lm, TI='graph', TITLE='USRobotics', 
              size='stamp',
              legend=False,
              fontsize=10.0)
    bag.save()

    lm = {
        'a': [0, '|c|','|@v0|', '|A|'],
        # 'b': [1, 'c|', '|@v0|', 'B|'],
        'c': [1, 'c|', '|@v0|', 'C|'],
        'd': [1, 'c|', '|@v0|', 'D|'],
        }
        
    path = '/home/mpattaro/workspace/star/trunk/reports/esempio/table0.pickle'
    bag = Bag(df, LD=path, LM=lm, TITLE='Esempio')
    bag.save()

    # graph = TexGraph(bag)
    # graph._figure.show()
#    bag.save()
#    graph._figure.savefig('/tmp/pollo.pdf', format='pdf')

