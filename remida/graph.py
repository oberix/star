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

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rc
import logging
from tempfile import NamedTemporaryFile, TemporaryFile
# import pandas
import re

import plotters

__author__ = "Marco Pattaro <marco.pattaro@servabit.it>"
__version__ = "0.1"
__all__ = ['Graph']

TICK_LABEL_LIMIT = 999. # xticks labels length limit
TICK_STEP = 2  # Draw an xtick every n values

FIGSIZE = { # (w, h) in inches
    'stamp': (3.200, 2.0), # (3.180, 2.380)
    'dinamic': (6.360, 2.380),
    'square': (6.360, 6.360),
    'flag': (3.180, 9.52),
    'scpaese': (3.5, 2.2),
}

TEX_ESCAPE = {
    re.compile("€"): "\\officialeuro", 
    re.compile("%"): "\\%", 
    re.compile("&"): "\\&",
    re.compile("\$(?!\w+)"): "\\$",
    re.compile(">(?!\{)"): "\\textgreater",
    re.compile("<(?!\{)"): "\\textless",
    re.compile("\n"): "\\\\",
    re.compile("_"): "\_",
#    re.compile("-"): "$-$",
    # tell LaTeX that an hyphen can be inserted after a '/'
    re.compile("/"): "/\-", 
    re.compile("\^"): "\textasciicircum",
    re.compile("~"): "\normaltilde",
    }

# TODO: fill this up
HTML_ESCAPE = {
    re.compile("<"): "&lt;",
    re.compile(">"): "&gt;",
    re.compile("&"): "&amp;",
    re.compile("\""): "&quot;",
    re.compile("'"): "&apos;",
    re.compile("€"): "&euro;",
    }

# TODO: move this to template.py
def escape(string, patterns=None):
    ''' Escape string to work with LaTeX.
    The function calls TEX_ESCAPE dictionary to metch regexp with their escaped
    version.

    @ param string: the string to escape
    @ param patterns: a pattern/string mapping dictionary
    @ return: escaped version of string

    '''
    if patterns is None:
        patterns = TEX_ESCAPE
    for pattern, sub in patterns.iteritems():
        string = re.sub(pattern, sub, string)
    return string


class Plotters(object):
    ''' Plotter factory.
    
    This class manage instanciation of concrete implementations of BasePlotter
    by ensuring that there is at most one instance of each of them.

    '''

    def __init__(self, graph):
        self._graph = graph
        self._logger = logging.getLogger(type(self).__name__)
        self._plotters = dict()

    def __getitem__(self, key):
        ''' Plotters can be accessed with square brackets notation

        Example:
        >>> plotters = Plotters(myGraph)
        >>> plotters['graphtype'].plot(ax, col)

        '''
        try:
            return self._plotters[key]
        except KeyError:
            try:
                self._plotters[key] = plotters.__getattribute__(key)(self._graph)
            except AttributeError:
                raise KeyError("Unhandled graph type '%s'" % key)
            return self._plotters[key]

    def __setitem__(self, key, value):
        ''' Item assignment not allowed.
        '''
        raise TypeError("'%s' object does not support item assignment" %
                        type(self).__name__)

class Graph(object):

    def __init__(self, data, **kwargs):
        self._logger = logging.getLogger(type(self).__name__)
        rc('legend', **{
                'markerscale': 1, 
                'labelspacing': 0, 
                'columnspacing': 1, 
                'borderpad': 0,
                })
        self._title = data.title
        self._footnote = data.footnote
        self._df = data.df
        self._y_meta = list()
        self._x_meta = list()
        self._fontsize = data.fontsize
        self._lax = None
        try:
            self._size = FIGSIZE[data.size]
        except KeyError, e:
            if isinstance(data.size, tuple):
                self._size = data.size
            else:
                raise e
        self._legend = data.legend
        self._plotters = Plotters(self)
        self.parse_lm(data.lm)
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
        if len(handles) < 3:
            ncol = 1
        elif len(handles) < 5:
            ncol = 2
        # Estimate new hight needed for the legend
        dheight = ((len(handles)/ncol) + 1) * self._fontsize * 0.01
        dheight_perc = dheight / figure.get_figheight() 
        # Scale figure and adjust subplot
        figure.set_figheight(figure.get_figheight() + dheight)
        figure.subplots_adjust(top=(0.9-dheight_perc))
        # Make legend
        leg = figure.legend(handles, labels, ncol=ncol, loc='upper left',
                            bbox_to_anchor=(0.10, 1.0))
        # Remove legend border
        leg.get_frame().set_linewidth(0)

        return leg

    def _unroll_cum(self, lm, val):
        ''' Visit bag's lm dictionary and make an ordered list of those
        variables that are cumulative to each other. This list will be used to
        stack variables in bar and hbar graphs.

        @ param lm : an lm dictionary
        @ param val: an lm dictionary entry

        '''
        ret = list()
        if val.get('cum'):
            ret = [val.get('cum', None)]
            ret += self._unroll_cum(lm, lm[val['cum']])
        return ret

    def parse_lm(self, lm):
        ''' Parse Bag's lm dictionary and estract the following non-public
        attrubutes:

        _lax: Series to use as x axes
        _y_meta: metadata for y ax series
        _x_meta: metadata for x ax series

        '''
        # TODO: handle line styles
        for key, val in lm.iteritems():
            # TODO: apply translation
            if val['type'] == 'lax':
                self._lax = [float(elem) for elem in self._df[key].tolist()]
                self._x_meta.append(val)
            else:
                val['key'] = key
                val['cumulate'] = self._unroll_cum(lm, val)
                if val['type'] == 'plot':
                    self._y_meta.insert(0, val)
                else:
                    self._y_meta.append(val)

    def _set_x_ax(self, ax):
        ticks = []
        rotation = 0
        delta = (self._lax.max() - self._lax.min()) / len(self._lax)
        # Draw only even ticks
        for idx, elem in enumerate(self._lax):
            if idx % TICK_STEP == 0:
                ticks.append(self._lax[idx])
            if elem > TICK_LABEL_LIMIT:
                rotation = 30
        ax.set_xticks(ticks)
        ax.set_xlim(self._lax.min() - delta,
                    self._lax.max() + delta)
        plt.setp(plt.xticks()[1], rotation=rotation)
        plt.subplots_adjust(hspace=0, bottom=0.13)

    def make_graph(self):
        ''' Create a Figure and plot a graph in it following what was specified
        in Bag.lm.

        @ return: the Figure instance created
        
        '''
        fig = plt.figure(figsize=self._size)
        ax = fig.add_subplot(1, 1, 1, axisbg='w', autoscale_on=True,
                             adjustable="datalim")
        ax.grid(True)
        lines = []
        labels = []
        for idx, col in enumerate(self._y_meta):
            try:
                line = self._plotters[col['type']].plot(ax, col)
            except KeyError:
                self._logger.warning(
                    "Unhandled graph type '%s', I will ignore entry '%s'", 
                    col['type'], col['key'])
                continue
            lines.append(line)
            labels.append(col['label'])

        # self._set_x_ax(ax) # Single graphs may change this
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
                'serif':['Computer Modern Roman'], 
                'size':self._fontsize})
        rc('text', usetex=True)
    
    def _make_legend(self, figure, handles, labels):
        labels = [escape(label) for label in labels]
        return super(TexGraph, self)._make_legend(figure, handles, labels)

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
        import base64, cStringIO
        buf = cStringIO.StringIO()
        self._figure.savefig(buf, format='png')
        buf.seek(0)
        png_base64 = base64.b64encode(buf.read())
        return '<img src="data:image/png;base64,%s" />' % png_base64


if __name__ == '__main__':
    ''' TEST '''

    import os
    import sys
    import pandas as pnd
    import numpy as np

    import sre
    from share import Bag
    
    logging.basicConfig(level=logging.DEBUG)

    lm_bar = {
        'a': {'type': 'lax', 
              'label': 'AAA'},
        'b': {'type': 'bar', 
              'label': 'BBB',
              'color': 'b',},
        'c': {'type': 'bar', 
              'ax': 'dx',
              'label': "CCC", 
              'color': 'g',
              'cum': 'b'},
        }

    lm_barh = {
        'a': {'type': 'lax', 
              'label': 'AAA'},
        'b': {'type': 'barh', 
              'ax': 'sx', 
              'label': 'BBB',
              'color': 'b'},
        'c': {'type': 'barh', 
              'ax': 'dx', 
              'label': "CCC", 
              'color': 'g',
              'cum': 'b'},
        }

    lm_plot = {
        'a': {'type': 'lax', 
              'label': 'AAA'},
        'b': {'type': 'bar', 
              'ax': 'sx', 
              'label': 'BBB',
              'color': 'b'},
        'c': {'type': 'plot', 
              'ax': 'dx', 
              'label': "CCC", 
              'color': 'g',}
        }

    df = pnd.DataFrame({
            'a': np.arange(0, 11, 1),
            'b': np.arange(5, 16, 1),
            'c': np.arange(0, 5.5, 0.5),
         })

#    import ipdb; ipdb.set_trace()

    lm_sc = {
        'a': {'type': 'lax', 
              'ax': 'sx', 
              'label': 'AAA'},
        'b': {'type': 'scatter', 
              'ax': 'sx', 
              'label': 'BBB',
              'color': 'b'},
        }

    df_sc = pnd.DataFrame({
            'a': [59.9, 46.2, 0],
            'b': [13.6, 7.1, 2],
            })

    bar = Bag(df, meta=lm_bar, bag_type='graph', title='USRobotics', 
              size='stamp',
              legend=True,
              fontsize=10.0)
    barh = Bag(df,  meta=lm_barh, bag_type='graph', title='USRobotics', 
              size='stamp',
              legend=True,
              fontsize=10.0)
    plot = Bag(df,  meta=lm_plot, bag_type='graph', title='USRobotics', 
              size='stamp',
              legend=True,
              fontsize=10.0)
    scat = Bag(df_sc, meta=lm_sc, bag_type='graph', title='USRobotics', 
              size='stamp',
              legend=False,
              fontsize=10.0)

    bar.save(os.path.join(sre.BASEPATH, "reports/esempio/bar.pickle"))
    barh.save(os.path.join(sre.BASEPATH, "reports/esempio/barh.pickle"))
    plot.save(os.path.join(sre.BASEPATH, "reports/esempio/plot.pickle"))
    scat.save(os.path.join(sre.BASEPATH, "reports/esempio/scatter.pickle"))


